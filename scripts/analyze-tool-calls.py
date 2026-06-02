"""Scan recent Claude Code transcripts and count bash/MCP tool patterns."""
from __future__ import annotations
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

PROJECTS_DIR = Path(os.path.expanduser("~/.claude/projects"))

# Already auto-allowed by Claude Code — never suggest these
AUTO_ALLOWED_ANY_ARGS = {
    "cal", "uptime", "cat", "head", "tail", "wc", "stat", "strings", "hexdump",
    "od", "nl", "id", "uname", "free", "df", "du", "locale", "groups", "nproc",
    "basename", "dirname", "realpath", "cut", "paste", "tr", "column", "tac",
    "rev", "fold", "expand", "unexpand", "fmt", "comm", "cmp", "numfmt",
    "readlink", "diff", "true", "false", "sleep", "which", "type", "expr",
    "test", "getconf", "seq", "tsort", "pr", "echo", "printf", "ls", "cd", "find",
    "xargs", "file", "sed", "sort", "man", "help", "netstat", "ps", "base64",
    "grep", "egrep", "fgrep", "sha256sum", "sha1sum", "md5sum", "tree", "date",
    "hostname", "info", "lsof", "pgrep", "tput", "ss", "fd", "fdfind", "aki",
    "rg", "jq", "uniq", "history", "arch", "ifconfig", "pyright",
}
AUTO_ALLOWED_NOARGS = {"pwd", "whoami", "alias"}

# git read-only subcommands — all auto-allowed
GIT_READONLY = {
    "status", "log", "diff", "show", "blame", "branch", "tag", "remote",
    "ls-files", "ls-remote", "config", "rev-parse", "describe", "stash",
    "reflog", "shortlog", "cat-file", "for-each-ref", "worktree",
}
# gh read-only subcommands — all auto-allowed
GH_READONLY = {
    "pr", "issue", "run", "workflow", "repo", "release", "api", "auth",
}
# docker read-only subcommands — auto-allowed
DOCKER_READONLY = {"ps", "images", "logs", "inspect"}

# Code-execution interpreters / package runners — never allowlist with wildcard
NEVER_WILDCARD = {
    "python", "python3", "node", "bun", "deno", "ruby", "perl", "php", "lua",
    "bash", "sh", "zsh", "fish", "eval", "exec", "ssh",
    "npx", "bunx", "uvx", "uv",
    "npm", "yarn", "pnpm", "make", "just", "cargo", "go",
    "sudo", "docker", "kubectl",
}

# Mutating commands — never allowlist regardless
MUTATING = {
    "rm", "mv", "cp", "mkdir", "rmdir", "touch", "chmod", "chown", "ln",
    "git push", "git commit", "git add", "git pull", "git merge", "git rebase",
    "git reset", "git checkout", "git stash push", "git stash pop", "git tag",
    "git rm", "git mv", "git fetch", "git clone", "git init", "git remote add",
    "gh pr create", "gh pr close", "gh pr merge", "gh pr edit", "gh pr comment",
    "gh pr review", "gh issue create", "gh issue close", "gh issue edit",
    "gh run rerun", "gh run cancel", "gh release create", "gh release delete",
}


def extract_first_command(cmd: str) -> str | None:
    """From a shell command string, extract the leading command + first subcommand.
    Strips env-var prefixes, sudo, timeout, cd chains, pipes."""
    cmd = cmd.strip()
    if not cmd:
        return None
    # Take only the first segment before pipes/&&/;
    for sep in ["|", "&&", ";", "||"]:
        if sep in cmd:
            cmd = cmd.split(sep)[0].strip()
    # Strip env-var assignments at the start (FOO=bar BAR=baz cmd)
    while re.match(r"^[A-Z_][A-Z0-9_]*=", cmd):
        parts = cmd.split(None, 1)
        if len(parts) < 2:
            return None
        cmd = parts[1]
    # Strip leading sudo / timeout / nohup
    tokens = cmd.split()
    while tokens and tokens[0] in ("sudo", "timeout", "nohup"):
        tokens = tokens[1:]
        # timeout takes a duration arg
        if tokens and tokens[0].replace(".", "").isdigit():
            tokens = tokens[1:]
    if not tokens:
        return None
    first = tokens[0]
    # Strip path: /usr/bin/git → git
    first = os.path.basename(first)
    if not first:
        return None
    if len(tokens) > 1:
        sub = tokens[1]
        # Skip flag-style args, take the first non-flag arg
        i = 1
        while i < len(tokens) and tokens[i].startswith("-"):
            i += 1
        if i < len(tokens) and not tokens[i].startswith("-"):
            return f"{first} {tokens[i]}"
        return first
    return first


def is_readonly_and_not_auto(pattern: str) -> tuple[bool, str]:
    """Return (allowlistable, reason). Reason is for debugging skipped entries."""
    parts = pattern.split(None, 1)
    cmd = parts[0]
    sub = parts[1] if len(parts) > 1 else None

    # Already auto-allowed
    if cmd in AUTO_ALLOWED_ANY_ARGS:
        return False, "auto-allowed"
    if cmd in AUTO_ALLOWED_NOARGS and sub is None:
        return False, "auto-allowed (no args)"
    # git read-only
    if cmd == "git" and sub in GIT_READONLY:
        return False, "auto-allowed (git read-only)"
    if cmd == "git" and sub is not None and f"git {sub}" in MUTATING:
        return False, "mutating"
    # gh read-only
    if cmd == "gh" and sub in GH_READONLY:
        return False, "auto-allowed (gh)"
    if cmd == "gh" and sub is not None and f"gh {sub}" in MUTATING:
        return False, "mutating"
    # docker read-only
    if cmd == "docker" and sub in DOCKER_READONLY:
        return False, "auto-allowed (docker)"
    # Mutating commands
    if cmd in MUTATING or pattern in MUTATING:
        return False, "mutating"
    # Never wildcard
    if cmd in NEVER_WILDCARD:
        return False, f"interpreter/runner ({cmd}) — would grant code exec"
    # Unknown — likely allowlistable if it looks like a CLI tool
    return True, "candidate"


def scan_transcripts(limit: int = 50) -> tuple[Counter, Counter]:
    """Return (bash_patterns, mcp_tools)."""
    bash_counter: Counter[str] = Counter()
    mcp_counter: Counter[str] = Counter()
    jsonls = sorted(
        PROJECTS_DIR.glob("*/*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]
    for f in jsonls:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                for line in fp:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = obj.get("message")
                    if not isinstance(msg, dict):
                        continue
                    if msg.get("role") != "assistant":
                        continue
                    content = msg.get("content")
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") != "tool_use":
                            continue
                        name = block.get("name", "")
                        inp = block.get("input", {})
                        if name == "Bash":
                            cmd_str = inp.get("command", "") if isinstance(inp, dict) else ""
                            pat = extract_first_command(cmd_str)
                            if pat:
                                bash_counter[pat] += 1
                        elif name.startswith("mcp__"):
                            mcp_counter[name] += 1
        except (OSError, PermissionError):
            continue
    return bash_counter, mcp_counter


def main() -> int:
    bash, mcp = scan_transcripts(50)
    print(f"# Scanned 50 transcripts")
    print(f"# Bash patterns: {len(bash)} unique, {sum(bash.values())} total calls")
    print(f"# MCP tool calls: {sum(mcp.values())} total\n")

    print("## Bash candidates (>=3 occurrences, read-only, not auto-allowed):")
    candidates = []
    skipped = []
    for pat, count in bash.most_common():
        if count < 3:
            break
        ok, reason = is_readonly_and_not_auto(pat)
        if ok:
            candidates.append((pat, count))
        else:
            skipped.append((pat, count, reason))
    for pat, count in candidates[:30]:
        print(f"  {count:4d}  {pat}")

    print("\n## MCP tools (any count):")
    for tool, count in mcp.most_common():
        print(f"  {count:4d}  {tool}")

    print("\n## Skipped (top 20, with reason):")
    for pat, count, reason in skipped[:20]:
        print(f"  {count:4d}  {pat:40s}  [{reason}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
