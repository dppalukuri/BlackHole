"""One-off rebrand: wanderwise/pennymath/tooljury → wanderwise/pennymath/tooljury.

Walks the repo and replaces all case variants of the old names in source/text files.
Skips: .git, node_modules, .astro, passport-index-data, logs, verified-visas.json.

Run with --dry-run first to see what would change. Then run without flag to apply.
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (old, new) pairs. Order matters: do CamelCase before lowercase so
# replacements don't double-apply.
REPLACEMENTS = [
    ("WanderWise", "WanderWise"),
    ("WanderWise", "WanderWise"),
    ("WANDERWISE", "WANDERWISE"),
    ("wanderwise", "wanderwise"),
    ("PennyMath", "PennyMath"),
    ("Pennymath", "Pennymath"),
    ("PENNYMATH", "PENNYMATH"),
    ("pennymath", "pennymath"),
    ("ToolJury", "ToolJury"),
    ("Tooljury", "Tooljury"),
    ("TOOLJURY", "TOOLJURY"),
    ("tooljury", "tooljury"),
]

# File extensions we'll touch. Anything else is skipped.
TEXT_EXTS = {
    ".astro", ".tsx", ".ts", ".js", ".mjs", ".cjs", ".jsx",
    ".json", ".md", ".mdx", ".html", ".htm", ".xml",
    ".css", ".scss",
    ".toml", ".yml", ".yaml",
    ".txt", ".py", ".sh", ".bat", ".env",
    ".svg",
}

# Path fragments that mean "skip this entire subtree."
SKIP_DIRS = {
    ".git", "node_modules", ".astro", ".vscode", ".idea",
    "passport-index-data",  # third-party data product
}

# Specific files to skip (huge data files with no brand text).
SKIP_FILES = {
    "verified-visas.json",  # 400KB+ of data, no brand text
    "package-lock.json",    # dependency lockfile
    "pnpm-lock.yaml",
    "yarn.lock",
}


def should_skip_dir(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def should_skip_file(path: Path) -> bool:
    if path.name in SKIP_FILES:
        return True
    # Log files in autonomous-agents/visa-verifier/output/
    if path.suffix == ".log":
        return True
    if path.suffix not in TEXT_EXTS:
        return True
    return False


def process_file(path: Path, dry_run: bool) -> tuple[int, dict[str, int]]:
    """Return (total_replacements, per-pattern counts)."""
    try:
        original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return 0, {}
    new = original
    counts: dict[str, int] = {}
    for old, replacement in REPLACEMENTS:
        n = new.count(old)
        if n:
            counts[f"{old} -> {replacement}"] = n
            new = new.replace(old, replacement)
    total = sum(counts.values())
    if total and not dry_run:
        path.write_text(new, encoding="utf-8")
    return total, counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    ap.add_argument("--verbose", "-v", action="store_true", help="List every file with changes")
    args = ap.parse_args()

    files_changed = 0
    total_replacements = 0
    global_counts: dict[str, int] = {}

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dp = Path(dirpath)
        if should_skip_dir(dp):
            dirnames.clear()
            continue
        # Prune subdirs that match skip rules
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            fp = dp / fn
            if should_skip_file(fp):
                continue
            n, counts = process_file(fp, args.dry_run)
            if n:
                files_changed += 1
                total_replacements += n
                for k, v in counts.items():
                    global_counts[k] = global_counts.get(k, 0) + v
                if args.verbose:
                    rel = fp.relative_to(ROOT)
                    print(f"  {rel}: {n}")

    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"\n[{mode}] {files_changed} files, {total_replacements} replacements")
    for k, v in sorted(global_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
