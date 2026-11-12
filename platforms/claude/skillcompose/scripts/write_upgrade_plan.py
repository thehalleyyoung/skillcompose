#!/usr/bin/env python3
"""Write UPGRADE_PLAN.md from forge_phases.json (legacy: upgrade_themes.json)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--themes", type=Path, help="forge_phases.json or legacy upgrade_themes.json")
    ap.add_argument("--phases", type=Path, help="Alias for --themes")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--incumbent", default="")
    args = ap.parse_args()
    path = args.phases or args.themes
    if not path:
        raise SystemExit("need --phases or --themes")
    doc = json.loads(path.read_text(encoding="utf-8"))
    phases = doc.get("phases") or doc.get("themes") or doc
    rounds = doc.get("forge_rounds") or 50
    lines = [
        f"# Upgrade plan ({rounds}-round forge phases)",
        "",
        f"Incumbent: `{args.incumbent}`" if args.incumbent else "",
        "",
        "Replaces the old T1–T5 theme ladder. Fixed phases:",
        "",
        "| Rounds | Phase | Job |",
        "|---|---|---|",
        "| 1–10 | **unify** | Unified whole strictly more than the sum of its parts |",
        "| 11–20 | **enhance** | Focused, enhanced abilities |",
        "| 21–44 | **metrics** | Undeniable reproducible best-in-some-way metrics; fix when not |",
        "| 45–50 | **awesome** | Real artifact (e.g. a novel) or ≥99%-confident third-party bug find |",
        "",
    ]
    for t in phases:
        rr = t.get("rounds") or ["?", "?"]
        lines += [
            f"## {t.get('id')} — {t.get('title')}",
            "",
            f"- **Kind:** `{t.get('kind', '')}`",
            f"- **Rounds:** {rr[0]}–{rr[1]}",
            f"- **Job:** {t.get('job') or t.get('incumbent_gap')}",
            f"- **Done when:** {t.get('done_when') or t.get('success_signal')}",
            f"- **Surfaces:** {', '.join(t.get('surfaces_planned') or [])}",
            "",
        ]
    args.out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "n": len(phases), "forge_rounds": rounds}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
