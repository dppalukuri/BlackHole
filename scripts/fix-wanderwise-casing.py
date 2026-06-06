"""Casing fix: 'WanderWise' → 'WanderWise' across all text source files.

Only touches the CamelCase display form. The lowercase 'wanderwise' is left
untouched (it's used in URLs, directory paths, IDs). Also leaves any
all-caps WANDERWISE untouched.

Skips: .git, node_modules, .astro, passport-index-data, logs, lockfiles,
verified-visas.json.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD = "WanderWise"
NEW = "WanderWise"

TEXT_EXTS = {
    ".astro", ".tsx", ".ts", ".js", ".mjs", ".cjs", ".jsx",
    ".json", ".md", ".mdx", ".html", ".htm", ".xml",
    ".css", ".scss",
    ".toml", ".yml", ".yaml",
    ".txt", ".py", ".sh", ".bat",
    ".svg",
}
SKIP_DIRS = {".git", "node_modules", ".astro", ".vscode", ".idea", "passport-index-data"}
SKIP_FILES = {"verified-visas.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}


def should_skip(p: Path) -> bool:
    if any(part in SKIP_DIRS for part in p.parts):
        return True
    if p.name in SKIP_FILES:
        return True
    if p.suffix == ".log":
        return True
    if p.suffix not in TEXT_EXTS:
        return True
    return False


def main() -> int:
    files = 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dp = Path(dirpath)
        if any(part in SKIP_DIRS for part in dp.parts):
            dirnames.clear()
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            fp = dp / fn
            if should_skip(fp):
                continue
            try:
                text = fp.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            n = text.count(OLD)
            if n:
                fp.write_text(text.replace(OLD, NEW), encoding="utf-8")
                files += 1
                total += n
    print(f"updated {files} files with {total} '{OLD}' -> '{NEW}' replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
