#!/usr/bin/env python3
"""Filter/pick an eligible marketplace skill (adoption floor, no popularity ceiling).

Highly popular skills are allowed. There is no default max on installs/stars.

Input JSONL rows:
  {"id":"owner/repo@skill","url":"...","installs":626,"stars":40,"skill_subdir":".","license":"MIT"}

Usage:
  pick_eligible.py --candidates FILE.jsonl [--seed HEX] [--pin ID] [--min-installs 80] [--json]
  Optional caps: [--max-installs N] [--max-stars N] (omit = no upper bound; highly popular allowed)

Legacy alias: pick_middling.py (same behavior).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def in_band(
    row: dict,
    min_i: int,
    max_i: int | None,
    min_s: int,
    max_s: int | None,
) -> bool:
    """Keep if installs/stars meet the floor; max_* None means no upper cap."""
    installs = row.get("installs")
    stars = row.get("stars")
    if installs is not None:
        try:
            n = int(installs)
        except (TypeError, ValueError):
            return False
        if n < min_i:
            return False
        if max_i is not None and n > max_i:
            return False
        return True
    if stars is not None:
        try:
            n = int(stars)
        except (TypeError, ValueError):
            return False
        if n < min_s:
            return False
        if max_s is not None and n > max_s:
            return False
        return True
    return False


def pick(rows: list[dict], seed: str) -> dict:
    if not rows:
        raise SystemExit("no eligible candidates")
    h = hashlib.sha256(seed.encode()).hexdigest()
    idx = int(h[:16], 16) % len(rows)
    return rows[idx]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, required=True)
    ap.add_argument("--seed", default="skillremix")
    ap.add_argument("--pin", default=None, help="Exact id to select if present")
    ap.add_argument("--exclude", action="append", default=[], help="Ids to skip (repeatable)")
    ap.add_argument("--write-chosen", type=Path, default=None, help="Write chosen.json for downstream")
    ap.add_argument("--min-installs", type=int, default=80)
    ap.add_argument(
        "--max-installs",
        type=int,
        default=None,
        help="Optional upper install cap (default: none — highly popular skills allowed)",
    )
    ap.add_argument("--min-stars", type=int, default=15)
    ap.add_argument(
        "--max-stars",
        type=int,
        default=None,
        help="Optional upper star cap (default: none — highly popular skills allowed)",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = load_rows(args.candidates)
    exclude = set(args.exclude or [])
    rows = [r for r in rows if r.get("id") not in exclude]
    if args.pin:
        for r in rows:
            if r.get("id") == args.pin:
                chosen = r
                band = "pinned"
                break
        else:
            # pin_fastpath: resolve single pin without a prior discover pass
            from pin_fastpath import resolve_pin  # noqa: WPS433 — sibling script

            resolved = resolve_pin(
                args.pin,
                min_installs=args.min_installs,
                min_stars=args.min_stars,
                allow_below_floor=False,
            )
            if not resolved.get("ok"):
                print(
                    json.dumps(
                        {
                            "error": "pin not found",
                            "pin": args.pin,
                            "fastpath": resolved,
                        }
                    ),
                    file=sys.stderr,
                )
                return 2
            chosen = resolved["chosen"]
            band = "pinned_fastpath"
            rows = [chosen]
    else:
        eligible = [
            r
            for r in rows
            if in_band(
                r,
                args.min_installs,
                args.max_installs,
                args.min_stars,
                args.max_stars,
            )
        ]
        if not eligible:
            out = {
                "error": "no candidates meeting adoption floor",
                "min_installs": args.min_installs,
                "max_installs": args.max_installs,
                "n_input": len(rows),
            }
            print(json.dumps(out, indent=2) if args.json else out)
            return 1
        chosen = pick(eligible, args.seed)
        band = "eligible"

    # Normalize chosen for downstream phases
    chosen = dict(chosen)
    if "installs_approx" not in chosen and chosen.get("installs") is not None:
        chosen["installs_approx"] = chosen["installs"]
    if chosen.get("url") is None and chosen.get("id"):
        owner_repo = str(chosen["id"]).split("@", 1)[0]
        chosen["url"] = f"https://github.com/{owner_repo}"
    why = (
        f"{chosen.get('installs_approx', chosen.get('stars'))} signal — meets adoption floor "
        "(no popularity ceiling; highly popular allowed)"
    )
    chosen["why_eligible"] = chosen.get("why_eligible") or why
    # Legacy key for older forge logs / WIP resumes
    chosen["why_middling"] = chosen.get("why_middling") or chosen["why_eligible"]

    n_eligible = len(
        [
            r
            for r in rows
            if in_band(
                r,
                args.min_installs,
                args.max_installs,
                args.min_stars,
                args.max_stars,
            )
        ]
    )
    out = {
        "decision": "PASS",
        "band": band,
        "chosen": chosen,
        "n_input": len(rows),
        "n_eligible": n_eligible,
        "n_middling": n_eligible,  # legacy alias
        "excluded": sorted(exclude),
    }
    if args.write_chosen:
        args.write_chosen.parent.mkdir(parents=True, exist_ok=True)
        args.write_chosen.write_text(json.dumps(chosen, indent=2), encoding="utf-8")
        out["chosen_path"] = str(args.write_chosen)
    print(json.dumps(out, indent=2) if args.json else out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
