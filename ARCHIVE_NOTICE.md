# Archived: Claude Continuity

**Status:** Archived — superseded by more mature projects.

This repository was an early experiment (v0.1, 2026) in adding persistent memory to Claude Desktop via the Model Context Protocol (MCP) and local ChromaDB. It explored:

- Semantic memory across conversations (projects, people, decisions, tasks, knowledge)
- Local-first architecture with no telemetry or cloud dependencies
- Nightly automation pipeline for memory pruning and organization
- MCP-native server with `memory_save` / `memory_search` / `memory_list` tools

## Why archived

The broader ecosystem evolved rapidly. Projects like [Mem0](https://github.com/mem0ai/mem0), MemPalace, and others have since become the standard for Claude memory management. This codebase is preserved as a historical artifact and reference for early MCP patterns.

## What still works

- The core MCP server design and ChromaDB integration approach
- The privacy-first, local-only philosophy
- The system prompt template in `docs/SYSTEM_PROMPT_TEMPLATE.md`

## What doesn't

- Clone URL in README was outdated (`Jdubnwa` → `johnmwhitman`) — fixed in archival commit
- Windows-first assumptions; Mac/Linux compatibility was never completed
- No active maintenance or updates

## Lessons

Building memory layers for LLMs is fundamentally about retrieval quality, context window management, and user trust — not just vector storage. The patterns here (collection-per-domain, semantic search over keyword matching, autonomous cleanup) remain relevant even if the implementation is outdated.

---

**Built on the Elk River in southwest Missouri. Kept for reference.**
