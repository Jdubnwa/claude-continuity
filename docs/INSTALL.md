# Installing Continuity

**Time required: ~15 minutes**

---

## Before you start

You'll need:
- Windows 10/11 (Mac/Linux: mostly compatible, paths will differ)
- [Claude Desktop](https://claude.ai/download) installed and running
- An active Anthropic subscription (Claude Pro or higher recommended)
- Python 3.10 or later — [download here](https://python.org/downloads)
- Git — [download here](https://git-scm.com/downloads)

Check your Python version:
```
python --version
```
Should return `Python 3.10.x` or higher.

---

## Step 1: Clone the repository

```bash
git clone https://github.com/Jdubnwa/claude-continuity.git
cd claude-continuity
```

---

## Step 2: Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs ChromaDB, the Anthropic client, and supporting libraries. Takes 1–3 minutes depending on your connection.

If you see permission errors, try:
```bash
pip install -r requirements.txt --user
```

---

## Step 3: Set your API key

Continuity needs your Anthropic API key to generate memory embeddings.

Get yours at: https://console.anthropic.com/account/keys

**Windows:**
```cmd
setx ANTHROPIC_API_KEY "sk-ant-your-key-here"
```

Then **close and reopen your terminal** for the variable to take effect.

**Verify it's set:**
```cmd
echo %ANTHROPIC_API_KEY%
```
Should print your key (not blank).

---

## Step 4: Run the onboarding wizard

```bash
python automation/onboarding_wizard.py
```

The wizard will:
- Check all dependencies are installed
- Create the required directory structure
- Verify ChromaDB is working
- Run a quick smoke test
- Confirm everything is ready

If all 5 steps pass, you're ready to configure Claude Desktop.

---

## Step 5: Configure Claude Desktop

**5a. Find your Claude Desktop config file:**

Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Open it in a text editor. If it doesn't exist yet, create it.

**5b. Add the MCP server block:**

```json
{
  "mcpServers": {
    "claude-memory": {
      "command": "python",
      "args": ["C:/path/to/claude-continuity/automation/memory_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-key-here"
      }
    }
  }
}
```

Replace `C:/path/to/claude-continuity` with the actual path where you cloned the repo.

If you already have other MCP servers configured, add `claude-memory` alongside them — don't replace the whole file.

**5c. Add the system prompt:**

Open Claude Desktop → Settings → Profile.

Paste the contents of `docs/SYSTEM_PROMPT_TEMPLATE.md` into the **Custom Instructions** field.

---

## Step 6: Restart Claude Desktop

Close Claude Desktop completely and reopen it.

---

## Step 7: Verify it works

In a new Claude conversation, say:
> **"check memory status"**

Claude should respond by calling `memory_stats()` and reporting something like:
> "Memory system is healthy — 0 memories across 6 collections."

Zero memories is correct for a fresh install. Start a conversation and Claude will begin saving context automatically.

---

## What gets created on your machine

```
%USERPROFILE%\.claude-memory\
├── data\              ← ChromaDB vector store (your memories live here)
└── automation\        ← Nightly pipeline scripts
```

Nothing is uploaded anywhere. This is all local.

---

## Troubleshooting

**"No module named 'chromadb'"**
→ Run `pip install chromadb` and try again.

**"ANTHROPIC_API_KEY not set"**
→ Make sure you ran `setx` and reopened your terminal. Or set it directly in the MCP config JSON.

**Claude says "I don't have memory tools available"**
→ The MCP server isn't connecting. Double-check the path in `claude_desktop_config.json` — it must be the absolute path to `memory_server.py`. Use forward slashes.

**memory_stats() returns 0 collections or an error**
→ The claude-memory MCP server may not be running. Check Claude Desktop's developer tools (Help → Toggle Developer Tools → Console) for error messages.

**Onboarding wizard fails on Step 4 (smoke test)**
→ Run `python automation/smoke_test.py` directly and share the output in a GitHub Issue.

**Everything looks right but memory isn't persisting**
→ Make sure `tool_search("claude memory save search list")` is included in your system prompt. This step loads the memory tools into scope at the start of each session — without it, saves appear to succeed but don't actually fire.

---

## Updating

```bash
git pull origin main
pip install -r requirements.txt
```

No database migrations needed for minor updates.

---

## Uninstalling

1. Remove the `claude-memory` block from `claude_desktop_config.json`
2. Remove the system prompt from Claude Desktop Settings
3. Delete `%USERPROFILE%\.claude-memory\` if you want to erase your memories
4. Delete the cloned repo folder

---

## Need help?

Open an issue: https://github.com/Jdubnwa/claude-continuity/issues
