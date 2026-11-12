#!/usr/bin/env python3
"""Validate SKILL.md frontmatter (name+description) and relative links."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def check(root: Path) -> dict:
    skill = root / "SKILL.md"
    reasons: list[str] = []
    if not skill.is_file():
        return {"decision": "FAIL", "reasons": ["missing SKILL.md"], "root": str(root)}
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---"):
        reasons.append("missing YAML frontmatter")
    else:
        parts = text.split("---", 2)
        fm = parts[1] if len(parts) >= 3 else ""
        if not re.search(r"(?m)^name:\s*\S+", fm):
            reasons.append("frontmatter missing name:")
        if not re.search(r"(?m)^description:\s*", fm):
            reasons.append("frontmatter missing description:")
    broken = []
    for _t, href in LINK_RE.findall(text):
        h = href.strip()
        if h.startswith(("http://", "https://", "mailto:", "#")):
            continue
        h = h.split("#", 1)[0]
        if not h:
            continue
        target = (root / h).resolve()
        if not target.exists():
            broken.append(h)
    if broken:
        reasons.append(f"broken relative links: {broken}")
    return {
        "decision": "PASS" if not reasons else "FAIL",
        "reasons": reasons,
        "root": str(root),
        "broken_links": broken if broken else [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    out = check(args.root)
    print(json.dumps(out, indent=2) if args.json else out)
    return 0 if out["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
