# Continuity

**Persistent memory and context for Claude Desktop. Every conversation picks up where the last one left off.**

---

Most AI assistants forget you the moment the session ends.

You paste the same context document every time. You re-explain your project. You remind Claude who your team is, what you're building, what you decided last week. Every conversation starts from zero.

Continuity fixes that.

It gives Claude Desktop a persistent memory layer — backed by [ChromaDB](https://www.trychroma.com/) running locally on your machine — so that what you share in one conversation is available in the next. Not uploaded to a server. Not summarized by someone else's model. Yours, on your hardware, under your control.

---

## What it does

- **Remembers across sessions** — decisions, projects, people, tasks, and context persist between conversations
- **Searches semantically** — Claude can recall relevant memories using natural language, not exact keyword matching
- **Runs locally** — ChromaDB lives on your machine. Nothing leaves unless you choose to share it.
- **Works autonomously** — a nightly pipeline updates, prunes, and organizes memory without you thinking about it
- **MCP-native** — built on the [Model Context Protocol](https://modelcontextprotocol.io/), the same standard Claude Desktop uses natively

---

## What it's not

- Not a plugin you install from a marketplace
- Not a cloud service or SaaS product
- Not a wrapper around someone else's memory API
- Not finished — this is v0.1, built by one person, and it works

---

## How it works

```
Your conversation
      ↓
Claude Desktop (with MCP)
      ↓
Continuity MCP server (memory_save / memory_search / memory_list)
      ↓
ChromaDB (local vector store, 6 collections)
      ↓
Next conversation — context already loaded
```

Six memory collections: `projects`, `people`, `decisions`, `knowledge`, `conversations`, `tasks`

Each entry is stored as a vector embedding, so Claude can find related memories even when the wording doesn't match exactly.

---

## Requirements

- Windows 10/11 (primary platform; Mac/Linux adaptable)
- [Claude Desktop](https://claude.ai/download) with an active Anthropic subscription
- Python 3.10+
- ~500MB disk space for ChromaDB

---

## Quick start

```bash
# 1. Clone the repo
git clone https://github.com/johnmwhitman/claude-continuity.git
cd claude-continuity

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the onboarding wizard
python automation/onboarding_wizard.py

# 4. Add the system prompt to Claude Desktop
# Settings → Profile → paste contents of docs/SYSTEM_PROMPT_TEMPLATE.md

# 5. Restart Claude Desktop
```

Full install guide: [docs/INSTALL.md](docs/INSTALL.md)

---

## Project structure

```
claude-continuity/
├── automation/          # Core scripts — memory server, pipeline, utilities
├── docs/                # Install guide, architecture, system prompt template
├── web/                 # Dashboard and local web tools
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE              # MIT
├── README.md
└── requirements.txt
```

---

## Privacy

Your memories never leave your machine unless you explicitly push them somewhere. No telemetry. No analytics. No phone-home. The ChromaDB database lives at a local path you control.

---

## Contributing

This project is early and welcomes help — especially on Mac/Linux compatibility, documentation, and testing. Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

The one non-negotiable: **no telemetry, no cloud dependencies, no data leaving the user's machine without explicit opt-in.**

---

## Status

**v0.1 — working, opinionated, Windows-first.**

The nightly pipeline runs. The memory server works. The onboarding wizard walks you through setup. It's not polished. It does what it says.

---

## License

MIT © 2026 John Whitman

---

*Built on the Elk River in southwest Missouri. Started because pasting the same context document into every Claude session got old.*
