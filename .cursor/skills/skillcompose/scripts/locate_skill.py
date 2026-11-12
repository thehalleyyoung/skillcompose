#!/usr/bin/env python3
"""Find SKILL.md directory inside a cloned repo (monorepo-aware)."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MIRROR_DIRS = {"distributions", "dist", "build", "examples", "example"}
NAME_RE = re.compile(r"^name:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", re.M)


def frontmatter_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    m = NAME_RE.search(text[: end if end > 0 else 2000])
    return m.group(1).strip() if m else None


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
        def rank(d: Path) -> tuple[bool, int, str]:
            mirror = any(x in d.relative_to(root).parts for x in MIRROR_DIRS)
            return (mirror, len(d.parts), str(d))

        declared = [d for d in dirs if frontmatter_name(d / "SKILL.md") == skill_name]
        named = [d for d in dirs if d.name == skill_name]
        loose = [d for d in dirs if skill_name in str(d)]
        for group in (declared, named, loose):
            if group:
                return sorted(group, key=rank)[0]
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
