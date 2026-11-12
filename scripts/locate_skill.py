#!/usr/bin/env python3
"""Find SKILL.md directory inside a cloned repo (monorepo-aware)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def find_skill_dirs(root: Path) -> list[Path]:
    found = []
    for p in root.rglob("SKILL.md"):
        # skip nested installs
        if any(x in p.parts for x in (".git", "node_modules", ".claude", ".cursor", ".codex", ".gemini", ".agents", "platforms")):
            continue
        found.append(p.parent)
    return found


def pick(root: Path, skill_name: str | None, subdir: str | None) -> Path:
    if subdir and subdir not in (".", ""):
        cand = root / subdir
        if (cand / "SKILL.md").exists():
            return cand
    dirs = find_skill_dirs(root)
    if skill_name:
        for d in dirs:
            if d.name == skill_name or skill_name in str(d):
                return d
    if len(dirs) == 1:
        return dirs[0]
    if (root / "SKILL.md").exists():
        return root
    if not dirs:
        raise SystemExit(f"no SKILL.md under {root}")
    # prefer shortest path
    return sorted(dirs, key=lambda p: len(p.parts))[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--skill-name", default=None)
    ap.add_argument("--subdir", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="Omit all_skill_dirs from JSON (monorepo noise)")
    args = ap.parse_args()
    chosen = pick(args.repo, args.skill_name, args.subdir)
    all_dirs = [str(p) for p in find_skill_dirs(args.repo)]
    out = {"skill_dir": str(chosen)}
    if not args.quiet:
        out["all_skill_dirs"] = all_dirs
    else:
        out["n_skill_dirs"] = len(all_dirs)
    print(json.dumps(out, indent=2) if args.json else out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
