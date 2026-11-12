#!/usr/bin/env python3
"""Measure character churn for a forge round commit (strict ≥1000 gate helper).

Usage:
  measure_chars.py --repo DIR [--commit HEAD] [--json]
  measure_chars.py --repo DIR --since-commit SHA --json   # diff since SHA..HEAD

Counts inserted+deleted characters across non-binary file diffs (git).
Excludes forge log copies that don't count as product work if only usefulness_forge.jsonl.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Paths that never count toward the ≥1000 product-edit requirement
EXCLUDE_SUFFIXES = (
    "/usefulness_forge.jsonl",
    "/USEFULNESS_FORGE.md",
)


def run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def excluded(path: str) -> bool:
    norm = path.replace("\\", "/")
    return any(norm.endswith(sfx) or sfx.lstrip("/") in norm for sfx in EXCLUDE_SUFFIXES)


def measure(repo: Path, commit: str | None, since: str | None) -> dict:
    if since:
        # Aggregate since..HEAD
        diff = run_git(repo, "diff", f"{since}..HEAD", "--numstat")
        show = run_git(repo, "diff", f"{since}..HEAD", "--")
        commit_label = f"{since}..HEAD"
    else:
        commit = commit or "HEAD"
        # numstat for file list; full patch for char count
        diff = run_git(repo, "show", commit, "--numstat", "--format=")
        show = run_git(repo, "show", commit, "--format=", "--")
        commit_label = commit

    files: list[str] = []
    for line in diff.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            path = parts[2]
            if path and not excluded(path):
                files.append(path)

    # Character churn from patch lines that are +/- content (not headers)
    added = 0
    deleted = 0
    current_file = None
    skip = False
    for line in show.splitlines():
        if line.startswith("diff --git "):
            # diff --git a/path b/path
            bits = line.split(" ")
            current_file = bits[-1][2:] if bits[-1].startswith("b/") else bits[-1]
            skip = excluded(current_file or "")
            continue
        if skip:
            continue
        if line.startswith("+++ ") or line.startswith("--- ") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            added += len(line[1:])
        elif line.startswith("-"):
            deleted += len(line[1:])

    total = added + deleted
    return {
        "commit": commit_label,
        "chars_added": added,
        "chars_deleted": deleted,
        "chars_changed": total,
        "files": sorted(set(files)),
        "n_files": len(set(files)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--since-commit", default=None)
    ap.add_argument("--min-chars", type=int, default=1000)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not (args.repo / ".git").exists() and not (args.repo / ".git").is_file():
        # allow worktrees / bare check
        try:
            run_git(args.repo, "rev-parse", "--is-inside-work-tree")
        except SystemExit as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 2

    out = measure(args.repo, args.commit, args.since_commit)
    out["min_chars"] = args.min_chars
    out["decision"] = "PASS" if out["chars_changed"] >= args.min_chars else "FAIL"
    if out["decision"] == "FAIL":
        out["reason"] = (
            f"chars_changed={out['chars_changed']} < min_chars={args.min_chars} "
            "(forge log / USEFULNESS_FORGE.md do not count)"
        )
    print(json.dumps(out, indent=2) if args.json else out)
    return 0 if out["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
