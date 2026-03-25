"""
onboarding_wizard.py — Continuity first-run setup
Guides new users through installation in 5 steps.

Usage:
    python automation/onboarding_wizard.py
    python automation/onboarding_wizard.py --quick   (skip pauses)
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path

QUICK = "--quick" in sys.argv

def pause(msg="Press Enter to continue..."):
    if not QUICK:
        input(f"\n{msg}")

def step(n, title):
    print(f"\n{'='*60}")
    print(f"  STEP {n}/5 — {title}")
    print(f"{'='*60}")

def ok(msg):
    print(f"  ✅ {msg}")

def warn(msg):
    print(f"  ⚠️  {msg}")

def fail(msg):
    print(f"  ❌ {msg}")

def header():
    print("\n" + "="*60)
    print("  CONTINUITY — First-Run Setup Wizard")
    print("  Persistent memory for Claude Desktop")
    print("="*60)
    print("\n  This wizard will check your environment and prepare")
    print("  Continuity for use. Takes about 2-3 minutes.\n")
    if not QUICK:
        input("  Press Enter to begin...")


# ─── STEP 1: Python version check ────────────────────────────────────────────

def check_python():
    step(1, "Python Version Check")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro} detected")
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        fail("Python 3.10 or higher is required.")
        print("  Download at: https://python.org/downloads")
        sys.exit(1)
    ok(f"Python {version.major}.{version.minor} — good to go")
    return True

# ─── STEP 2: Dependency check ─────────────────────────────────────────────────

def check_deps():
    step(2, "Dependency Check")
    required = ["chromadb", "anthropic", "mcp"]
    optional = ["schedule", "psutil", "requests"]
    missing_required = []
    missing_optional = []

    for pkg in required:
        try:
            __import__(pkg)
            ok(f"{pkg} installed")
        except ImportError:
            fail(f"{pkg} NOT installed")
            missing_required.append(pkg)

    for pkg in optional:
        try:
            __import__(pkg)
            ok(f"{pkg} installed (optional)")
        except ImportError:
            warn(f"{pkg} not installed (optional — some features may not work)")
            missing_optional.append(pkg)

    if missing_required:
        print(f"\n  Missing required packages: {', '.join(missing_required)}")
        print("  Run: pip install -r requirements.txt")
        print("  Then re-run this wizard.")
        sys.exit(1)

    ok("All required dependencies present")
    return True


# ─── STEP 3: Directory structure ─────────────────────────────────────────────

def setup_dirs():
    step(3, "Directory Setup")
    home = Path.home()
    memory_root = home / ".claude-memory"
    dirs = [
        memory_root,
        memory_root / "data",
        memory_root / "logs",
        memory_root / "automation",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        ok(f"Created: {d}")

    # Write onboarding marker
    marker = memory_root / "onboarding_complete.json"
    marker.write_text(json.dumps({
        "version": "0.1",
        "completed": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }, indent=2))
    ok(f"Wrote onboarding marker: {marker}")
    return str(memory_root)

# ─── STEP 4: API key check ────────────────────────────────────────────────────

def check_api_key():
    step(4, "API Key Check")
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        warn("ANTHROPIC_API_KEY environment variable not set.")
        print("\n  You'll need this for ChromaDB embeddings and Claude API calls.")
        print("  Get your key at: https://console.anthropic.com/account/keys")
        print("\n  To set it permanently on Windows:")
        print('    setx ANTHROPIC_API_KEY "sk-ant-your-key-here"')
        print("  Then close and reopen your terminal.\n")
        print("  You can continue setup now and add the key later,")
        print("  but memory won't work until it's set.")
        pause("Press Enter to continue anyway...")
        return False
    if not key.startswith("sk-"):
        warn("API key found but format looks unusual. Continuing anyway.")
        return True
    ok("ANTHROPIC_API_KEY is set")
    masked = key[:8] + "..." + key[-4:]
    print(f"  Key: {masked}")
    return True


# ─── STEP 5: ChromaDB smoke test ─────────────────────────────────────────────

def smoke_test():
    step(5, "ChromaDB Smoke Test")
    try:
        import chromadb
        client = chromadb.PersistentClient(
            path=str(Path.home() / ".claude-memory" / "data")
        )
        # Create a test collection
        col = client.get_or_create_collection("__onboarding_test__")
        col.add(
            documents=["Continuity onboarding test entry"],
            ids=["onboarding_test_001"]
        )
        result = col.query(query_texts=["onboarding"], n_results=1)
        if result["documents"][0]:
            ok("ChromaDB write + query succeeded")
        else:
            warn("ChromaDB write succeeded but query returned no results.")

        # Clean up test collection
        client.delete_collection("__onboarding_test__")
        ok("ChromaDB test collection cleaned up")
        return True

    except Exception as e:
        fail(f"ChromaDB smoke test failed: {e}")
        print("\n  This usually means chromadb isn't installed correctly.")
        print("  Try: pip install chromadb --upgrade")
        return False

# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    header()

    results = {}
    results["python"] = check_python()
    pause()

    results["deps"] = check_deps()
    pause()

    memory_root = setup_dirs()
    results["dirs"] = True
    pause()

    results["api_key"] = check_api_key()
    pause()

    results["chromadb"] = smoke_test()

    # Summary
    print("\n" + "="*60)
    print("  SETUP COMPLETE")
    print("="*60)
    all_pass = all([results.get("python"), results.get("deps"),
                    results.get("dirs"), results.get("chromadb")])

    if all_pass:
        print("\n  ✅ All checks passed. Continuity is ready to configure.")
    else:
        print("\n  ⚠️  Some checks had issues — see warnings above.")

    print(f"\n  Memory directory: {memory_root}")
    print("\n  NEXT STEPS:")
    print("  1. Add claude-memory to your Claude Desktop MCP config")
    print("     See: docs/INSTALL.md → Step 5")
    print("  2. Paste docs/SYSTEM_PROMPT_TEMPLATE.md into Claude Desktop")
    print("     Settings → Profile → Custom Instructions")
    print("  3. Restart Claude Desktop")
    print("  4. Say 'check memory status' to verify it's working\n")

    if not QUICK:
        input("  Press Enter to exit...")

if __name__ == "__main__":
    main()
