"""
memory_server.py — Continuity MCP Server
Persistent memory for Claude Desktop via ChromaDB.

MCP server exposing 7 tools:
  memory_save            — store a new memory
  memory_search          — semantic search across collections
  memory_list            — list recent entries in a collection
  memory_update          — update an existing memory by ID
  memory_delete          — delete a memory by ID
  memory_stats           — health check and entry counts
  memory_save_conversation — save a session summary

Collections: projects, people, decisions, knowledge, conversations, tasks

Storage: ~/.claude-memory/data/ (local, private, yours)
Protocol: MCP over stdin/stdout (Claude Desktop compatible)
"""

import sys
import json
import uuid
import os
import datetime

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    sys.stderr.write(
        "chromadb not installed. Run: pip install chromadb\n"
    )
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
MEMORY_DIR = os.path.join(os.path.expanduser("~"), ".claude-memory", "data")
os.makedirs(MEMORY_DIR, exist_ok=True)

COLLECTIONS = ["projects", "people", "decisions", "knowledge", "conversations", "tasks"]
IMPORTANCE_LEVELS = ["low", "medium", "high", "critical"]

# ── ChromaDB client ───────────────────────────────────────────────────────────
client = chromadb.PersistentClient(
    path=MEMORY_DIR,
    settings=Settings(anonymized_telemetry=False)
)

def get_collection(name: str):
    """Get or create a named collection."""
    if name not in COLLECTIONS:
        raise ValueError(f"Unknown collection '{name}'. Valid: {COLLECTIONS}")
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )


# ── Tool implementations ──────────────────────────────────────────────────────

def memory_save(collection: str, content: str, title: str,
                importance: str = "medium", tags: list = None) -> dict:
    """Store a new memory entry."""
    col = get_collection(collection)
    if importance not in IMPORTANCE_LEVELS:
        importance = "medium"

    entry_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    metadata = {
        "title": title,
        "importance": importance,
        "tags": json.dumps(tags or []),
        "created_at": now,
        "updated_at": now,
        "collection": collection,
    }

    col.add(
        ids=[entry_id],
        documents=[f"{title}\n{content}"],
        metadatas=[metadata]
    )

    return {
        "status": "saved",
        "id": entry_id,
        "collection": collection,
        "title": title,
        "importance": importance,
        "created_at": now,
    }


def memory_search(query: str, collections: list = None,
                  n_results: int = 5, tags_filter: list = None) -> dict:
    """Semantic search across one or more collections."""
    target = collections if collections else COLLECTIONS
    results = []

    for col_name in target:
        if col_name not in COLLECTIONS:
            continue
        col = get_collection(col_name)
        count = col.count()
        if count == 0:
            continue

        k = min(n_results, count)
        res = col.query(query_texts=[query], n_results=k)

        for i, doc_id in enumerate(res["ids"][0]):
            meta = res["metadatas"][0][i]
            dist = res["distances"][0][i] if res.get("distances") else None
            similarity = round(1 - dist, 3) if dist is not None else None

            # Optional tag filter
            if tags_filter:
                stored_tags = json.loads(meta.get("tags", "[]"))
                if not any(t in stored_tags for t in tags_filter):
                    continue

            results.append({
                "id": doc_id,
                "collection": col_name,
                "title": meta.get("title", ""),
                "content": res["documents"][0][i],
                "similarity": similarity,
                "importance": meta.get("importance", "medium"),
                "tags": json.loads(meta.get("tags", "[]")),
                "created_at": meta.get("created_at", ""),
                "updated_at": meta.get("updated_at", ""),
            })

    results.sort(key=lambda x: x.get("similarity") or 0, reverse=True)
    return {"query": query, "total_results": len(results), "results": results[:n_results]}


def memory_list(collection: str, importance_filter: str = None,
                limit: int = 20, tags_filter: list = None) -> dict:
    """List recent entries in a collection, newest first."""
    col = get_collection(collection)
    count = col.count()
    if count == 0:
        return {"collection": collection, "count": 0, "records": []}

    res = col.get(include=["documents", "metadatas"])
    records = []

    for i, doc_id in enumerate(res["ids"]):
        meta = res["metadatas"][i]

        if importance_filter and meta.get("importance") != importance_filter:
            continue
        if tags_filter:
            stored_tags = json.loads(meta.get("tags", "[]"))
            if not any(t in stored_tags for t in tags_filter):
                continue

        records.append({
            "id": doc_id,
            "title": meta.get("title", ""),
            "content": res["documents"][i],
            "importance": meta.get("importance", "medium"),
            "tags": json.loads(meta.get("tags", "[]")),
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", ""),
        })

    # Sort newest first by created_at
    records.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    records = records[:limit]

    return {"collection": collection, "count": len(records), "records": records}


def memory_update(collection: str, memory_id: str,
                  content: str = None, title: str = None,
                  importance: str = None, tags: list = None) -> dict:
    """Update an existing memory entry by ID."""
    col = get_collection(collection)

    res = col.get(ids=[memory_id], include=["documents", "metadatas"])
    if not res["ids"]:
        return {"status": "error", "message": f"Memory {memory_id} not found in {collection}"}

    old_meta = res["metadatas"][0]
    old_doc = res["documents"][0]

    new_title = title or old_meta.get("title", "")
    new_content = content or old_doc
    new_importance = importance if importance in IMPORTANCE_LEVELS else old_meta.get("importance", "medium")
    new_tags = tags if tags is not None else json.loads(old_meta.get("tags", "[]"))
    now = datetime.datetime.utcnow().isoformat()

    new_meta = {**old_meta, "title": new_title, "importance": new_importance,
                "tags": json.dumps(new_tags), "updated_at": now}

    col.update(
        ids=[memory_id],
        documents=[f"{new_title}\n{new_content}"],
        metadatas=[new_meta]
    )

    return {"status": "updated", "id": memory_id, "collection": collection,
            "title": new_title, "updated_at": now}


def memory_delete(collection: str, memory_id: str) -> dict:
    """Delete a memory entry by ID."""
    col = get_collection(collection)
    res = col.get(ids=[memory_id])
    if not res["ids"]:
        return {"status": "error", "message": f"Memory {memory_id} not found in {collection}"}

    col.delete(ids=[memory_id])
    return {"status": "deleted", "id": memory_id, "collection": collection}


def memory_stats() -> dict:
    """Return entry counts per collection and total. Health check."""
    stats = {}
    total = 0
    for name in COLLECTIONS:
        col = get_collection(name)
        count = col.count()
        stats[name] = count
        total += count

    return {
        "status": "healthy" if total > 0 else "empty",
        "total": total,
        "collections": stats,
        "storage_path": MEMORY_DIR,
    }


def memory_save_conversation(summary: str, topics: list,
                              continue_next: str = None,
                              decisions: list = None,
                              tasks: list = None) -> dict:
    """Save a session summary to the conversations collection."""
    now = datetime.datetime.utcnow().isoformat()
    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    content_parts = [f"Summary: {summary}"]
    if decisions:
        content_parts.append("Decisions: " + " | ".join(decisions))
    if tasks:
        content_parts.append("Tasks: " + " | ".join(tasks))
    if continue_next:
        content_parts.append(f"Continue: {continue_next}")

    return memory_save(
        collection="conversations",
        content="\n".join(content_parts),
        title=f"Session {date_str} — {', '.join(topics[:3])}",
        importance="medium",
        tags=topics[:10],
    )


# ── MCP protocol handler ──────────────────────────────────────────────────────

TOOL_DISPATCH = {
    "memory_save": memory_save,
    "memory_search": memory_search,
    "memory_list": memory_list,
    "memory_update": memory_update,
    "memory_delete": memory_delete,
    "memory_stats": memory_stats,
    "memory_save_conversation": memory_save_conversation,
}

TOOL_SCHEMAS = [
    {
        "name": "memory_save",
        "description": "Store a new memory entry in the specified collection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string", "enum": COLLECTIONS},
                "content": {"type": "string"},
                "title": {"type": "string"},
                "importance": {"type": "string", "enum": IMPORTANCE_LEVELS, "default": "medium"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["collection", "content", "title"],
        },
    },
    {
        "name": "memory_search",
        "description": "Semantic search across memory collections.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "collections": {"type": "array", "items": {"type": "string"}},
                "n_results": {"type": "integer", "default": 5},
                "tags_filter": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["query"],
        },
    },
    {
        "name": "memory_list",
        "description": "List recent entries in a collection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string", "enum": COLLECTIONS},
                "importance_filter": {"type": "string", "enum": IMPORTANCE_LEVELS},
                "limit": {"type": "integer", "default": 20},
                "tags_filter": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["collection"],
        },
    },
    {
        "name": "memory_update",
        "description": "Update an existing memory entry by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string", "enum": COLLECTIONS},
                "memory_id": {"type": "string"},
                "content": {"type": "string"},
                "title": {"type": "string"},
                "importance": {"type": "string", "enum": IMPORTANCE_LEVELS},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["collection", "memory_id"],
        },
    },
    {
        "name": "memory_delete",
        "description": "Delete a memory entry by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string", "enum": COLLECTIONS},
                "memory_id": {"type": "string"},
            },
            "required": ["collection", "memory_id"],
        },
    },
    {
        "name": "memory_stats",
        "description": "Return entry counts per collection and confirm the server is running.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "memory_save_conversation",
        "description": "Save a session summary to the conversations collection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "topics": {"type": "array", "items": {"type": "string"}},
                "continue_next": {"type": "string"},
                "decisions": {"type": "array", "items": {"type": "string"}},
                "tasks": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["summary", "topics"],
        },
    },
]


def handle_request(req: dict) -> dict:
    """Route a single MCP JSON-RPC request to the appropriate handler."""
    method = req.get("method", "")
    req_id = req.get("id")

    def ok(result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def err(code, message):
        return {"jsonrpc": "2.0", "id": req_id,
                "error": {"code": code, "message": message}}

    if method == "initialize":
        return ok({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "claude-memory", "version": "1.0.0"},
        })

    if method == "tools/list":
        return ok({"tools": TOOL_SCHEMAS})

    if method == "tools/call":
        tool_name = req.get("params", {}).get("name", "")
        arguments = req.get("params", {}).get("arguments", {})

        if tool_name not in TOOL_DISPATCH:
            return err(-32601, f"Unknown tool: {tool_name}")

        try:
            result = TOOL_DISPATCH[tool_name](**arguments)
            return ok({
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            })
        except Exception as e:
            return err(-32603, f"Tool error ({tool_name}): {str(e)}")

    if method in ("notifications/initialized", "ping"):
        return None  # No response needed

    return err(-32601, f"Method not found: {method}")


def main():
    """Run the MCP server over stdin/stdout."""
    sys.stderr.write(f"claude-memory MCP server starting (storage: {MEMORY_DIR})\n")
    sys.stderr.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            response = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": f"Parse error: {e}"}}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        try:
            response = handle_request(req)
        except Exception as e:
            response = {"jsonrpc": "2.0", "id": req.get("id"),
                        "error": {"code": -32603, "message": f"Internal error: {e}"}}

        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
