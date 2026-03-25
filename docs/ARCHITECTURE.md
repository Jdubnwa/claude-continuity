# How Continuity Works

A technical overview of the architecture for contributors and curious users.

---

## The core problem

Every Claude conversation starts fresh. There's no built-in way for Claude to remember what you told it last week, last month, or five minutes ago in a different chat window. The typical workaround is a "context document" — a growing text file you paste at the start of every session.

Continuity replaces that pattern with a proper persistence layer.

---

## Architecture overview

```
┌──────────────────────────────────────────────────┐
│                  Claude Desktop                   │
│                                                   │
│  System prompt (session init, memory rules)       │
│              ↓              ↑                     │
│       MCP tool calls    MCP responses             │
└─────────────────┬────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────┐
│           claude-memory MCP Server                │
│   (automation/memory_server.py)                   │
│                                                   │
│   Tools:                                          │
│   • memory_save(collection, content, title, ...)  │
│   • memory_search(query, collections, ...)        │
│   • memory_list(collection, importance_filter)    │
│   • memory_update(memory_id, content, ...)        │
│   • memory_delete(memory_id)                      │
│   • memory_stats()                                │
│   • memory_save_conversation(summary, topics, ...) │
└─────────────────┬────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────┐
│              ChromaDB (local)                     │
│   ~/.claude-memory/data/                          │
│                                                   │
│   Collections:                                    │
│   • projects    — active work, status, goals      │
│   • people      — contacts, roles, relationships  │
│   • decisions   — choices made and reasoning      │
│   • knowledge   — facts, how-to, context          │
│   • tasks       — action items, follow-ups        │
│   • conversations — session summaries             │
└──────────────────────────────────────────────────┘
```

---

## Layer 1 — The identity specification (system prompt)

The system prompt in Claude Desktop defines the behavioral contract:
- Which tools to load at session start (`tool_search` → loads claude-memory tools)
- When to save automatically (new facts, decisions, tasks)
- When to search (before answering anything the user might have mentioned before)
- When to summarize (session close triggers)

The system prompt is the character layer. It's what makes Claude behave like it knows you, rather than a generic assistant that happens to have access to a database.

---

## Layer 2 — The MCP server

`automation/memory_server.py` is a [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes memory operations as tools Claude can call.

Claude Desktop discovers it via `claude_desktop_config.json`. The server runs as a subprocess, receives tool calls over stdin/stdout, and translates them into ChromaDB operations.

Key behaviors:
- **Semantic search** — queries use vector similarity, not exact keyword matching. "What did we decide about the database?" finds entries about PostgreSQL migrations even if those words aren't in the query.
- **Collection routing** — saves go to the right collection based on content type (a task to `tasks`, a person to `people`, etc.)
- **Importance levels** — entries tagged `critical` or `high` surface first in filtered queries

---

## Layer 3 — ChromaDB

[ChromaDB](https://www.trychroma.com/) is a local vector database. It:
- Converts text entries into vector embeddings (using the configured embedding model)
- Stores them persistently at `~/.claude-memory/data/`
- Supports semantic similarity search across all entries

No data leaves your machine through ChromaDB. It runs entirely in-process.

---

## Layer 4 — The nightly pipeline

`automation/run_nightly_pipeline.py` runs on a schedule (via Task Scheduler on Windows, cron elsewhere) and handles maintenance:
- Pruning stale or low-value memories
- Generating session summaries
- Backing up the ChromaDB data directory
- Optionally pushing a summary to a local dashboard

You don't need to run this manually. It's optional infrastructure — Continuity works fine without it.

---

## Session initialization flow

When you open a new Claude Desktop conversation:

1. Claude's system prompt fires
2. `tool_search("claude memory save search list")` — loads the MCP tools into scope for this session
3. `memory_search(...)` — pulls relevant context from prior sessions
4. `memory_list(collection="tasks", importance_filter="high")` — surfaces open action items
5. `memory_stats()` — verifies the server is running

This happens in the first few seconds, silently. By the time you type your first message, Claude already knows what you were working on.

---

## Storage format

Each memory entry is stored as:
```json
{
  "id": "uuid",
  "collection": "projects",
  "title": "Short descriptive title",
  "content": "Detailed content text",
  "importance": "high",
  "tags": ["tag1", "tag2"],
  "created_at": "2026-03-18T...",
  "updated_at": "2026-03-18T..."
}
```

Embeddings are stored alongside each entry in ChromaDB's internal format.

---

## Privacy model

- **Nothing leaves your machine** unless you explicitly push the ChromaDB data directory somewhere
- **No telemetry** — no analytics calls, no usage reporting, no crash reporting
- **No cloud dependencies** — ChromaDB runs locally; embeddings can use the Anthropic API (requires API key) or a local model (Ollama)
- **You own the data** — the database lives at `~/.claude-memory/data/` and can be backed up, moved, or deleted at will

---

## Extending it

The MCP server is designed to be modified. Common extension points:
- **Add a collection** — add a new collection name to the server and start saving to it
- **Custom importance logic** — modify how entries get tagged
- **Different embedding model** — swap in Ollama's `nomic-embed-text` for fully offline operation
- **Dashboard** — `web/dashboard.html` gives a local overview of memory health and recent activity

Pull requests welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md).
