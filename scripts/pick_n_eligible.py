#!/usr/bin/env python3
"""Pick N diverse eligible marketplace skills for remix mode (adoption floor; popular OK).

Diversity heuristic: prefer different repo owners and dissimilar skill-name tokens
so the set can compose into an end-to-end workflow instead of N near-duplicates.
Highly popular skills are eligible — there is no mid-band preference.

Legacy alias: pick_n_middling.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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


def skill_token(row: dict) -> str:
    sid = str(row.get("id") or "")
    if "@" in sid:
        return sid.split("@", 1)[1].lower()
    return sid.lower()


def owner_token(row: dict) -> str:
    sid = str(row.get("id") or "")
    return sid.split("/", 1)[0].lower() if "/" in sid else sid.lower()


def name_tokens(name: str) -> set[str]:
    parts = re.split(r"[-_/.\s]+", name.lower())
    stop = {"skill", "skills", "ai", "the", "a", "an", "and", "for", "to"}
    return {p for p in parts if p and p not in stop and len(p) > 1}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def seeded_order(rows: list[dict], seed: str) -> list[dict]:
    def key(r: dict) -> str:
        return hashlib.sha256(f"{seed}:{r.get('id')}".encode()).hexdigest()

    return sorted(rows, key=key)


def pick_diverse(
    rows: list[dict],
    n: int,
    seed: str,
    max_name_sim: float = 0.55,
    practice_mix: bool = False,
) -> list[dict]:
    """Greedy diversity; when practice_mix, balance domain_core vs practice_support."""
    ordered = seeded_order(rows, seed)
    chosen: list[dict] = []
    chosen_owners: set[str] = set()
    chosen_names: list[set[str]] = []

    def try_add(r: dict) -> bool:
        if any(r.get("id") == c.get("id") for c in chosen):
            return False
        ow = owner_token(r)
        nt = name_tokens(skill_token(r))
        if ow in chosen_owners:
            return False
        if any(jaccard(nt, prev) > max_name_sim for prev in chosen_names):
            return False
        chosen.append(r)
        chosen_owners.add(ow)
        chosen_names.append(nt)
        return True

    if practice_mix:
        # Target ~half domain-core, rest practice-support (min 2 core when n>=4)
        core = [r for r in ordered if r.get("discovery_role") == "domain_core"]
        support = [r for r in ordered if r.get("discovery_role") == "practice_support"]
        other = [
            r
            for r in ordered
            if r.get("discovery_role") not in {"domain_core", "practice_support"}
        ]
        n_core_target = max(2, (n + 1) // 2) if n >= 4 else max(1, n // 2)
        n_support_target = n - n_core_target
        for r in core:
            if sum(1 for c in chosen if c.get("discovery_role") == "domain_core") >= n_core_target:
                break
            try_add(r)
        for r in support:
            if sum(1 for c in chosen if c.get("discovery_role") == "practice_support") >= n_support_target:
                break
            if len(chosen) >= n:
                break
            try_add(r)
        # Fill from remaining pools
        for pool in (core, support, other, ordered):
            for r in pool:
                if len(chosen) >= n:
                    break
                try_add(r)
            if len(chosen) >= n:
                break
        # Relax owner constraint if still short
        if len(chosen) < n:
            for r in ordered:
                if len(chosen) >= n:
                    break
                if any(r.get("id") == c.get("id") for c in chosen):
                    continue
                nt = name_tokens(skill_token(r))
                if any(jaccard(nt, prev) > max_name_sim for prev in chosen_names):
                    continue
                chosen.append(r)
                chosen_names.append(nt)
        return chosen[:n]

    # Pass 1: unique owners + dissimilar names
    for r in ordered:
        if len(chosen) >= n:
            break
        try_add(r)

    # Pass 2: fill remaining allowing same owner if names differ
    if len(chosen) < n:
        for r in ordered:
            if len(chosen) >= n:
                break
            if any(r.get("id") == c.get("id") for c in chosen):
                continue
            nt = name_tokens(skill_token(r))
            if any(jaccard(nt, prev) > max_name_sim for prev in chosen_names):
                continue
            chosen.append(r)
            chosen_names.append(nt)

    # Pass 3: fill anything left
    if len(chosen) < n:
        for r in ordered:
            if len(chosen) >= n:
                break
            if any(r.get("id") == c.get("id") for c in chosen):
                continue
            chosen.append(r)

    return chosen[:n]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--seed", default="skillremix")
    ap.add_argument("--exclude", action="append", default=[])
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
    ap.add_argument("--write-chosen", type=Path, default=None, help="Write chosen_n.json")
    ap.add_argument(
        "--practice-mix",
        choices=["auto", "on", "off"],
        default="auto",
        help="When on/auto(n>=5), balance domain_core vs practice_support roles in the pick",
    )
    ap.add_argument(
        "--strategy",
        choices=["auto", "submodular", "diverse"],
        default="auto",
        help="Selection engine: submodular mutual-information cover (default when metadata present) or legacy diverse",
    )
    ap.add_argument("--domain", default=None, help="Domain pack hint for submodular off-domain divergence")
    ap.add_argument("--query", default="", help="Query hint for submodular selection")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.n < 2:
        print(json.dumps({"error": "--n must be >= 2"}), file=sys.stderr)
        return 2

    rows = load_rows(args.candidates)
    exclude = set(args.exclude or [])
    eligible = [
        r
        for r in rows
        if r.get("id") not in exclude
        and in_band(r, args.min_installs, args.max_installs, args.min_stars, args.max_stars)
    ]
    if len(eligible) < args.n:
        out = {
            "decision": "FAIL",
            "error": f"need ≥{args.n} eligible candidates, got {len(eligible)}",
            "n_eligible": len(eligible),
            "n_middling": len(eligible),  # legacy alias
            "n_requested": args.n,
        }
        print(json.dumps(out, indent=2) if args.json else out)
        return 1

    has_roles = any(r.get("discovery_role") in {"domain_core", "practice_support"} for r in eligible)
    mix = args.practice_mix == "on" or (
        args.practice_mix == "auto" and args.n >= 5 and has_roles
    )

    has_rich_signal = bool(args.domain or args.query) or any(
        r.get("github_description") or r.get("query") for r in eligible
    )
    use_submodular = args.strategy == "submodular" or (
        args.strategy == "auto" and has_rich_signal
    )

    info_comp = None
    if use_submodular:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from submodular_select import compare_vs_github_top

        info_comp = compare_vs_github_top(
            eligible,
            args.n,
            domain=args.domain,
            query=args.query,
            seed=args.seed,
        )
        chosen = info_comp["chosen"]
    else:
        chosen = pick_diverse(eligible, args.n, args.seed, practice_mix=mix)

    for c in chosen:
        if "installs_approx" not in c and c.get("installs") is not None:
            c["installs_approx"] = c["installs"]

    role_counts: dict[str, int] = {}
    for c in chosen:
        role = str(c.get("discovery_role") or "unknown")
        role_counts[role] = role_counts.get(role, 0) + 1

    warnings: list[dict] = []
    n_support = int(role_counts.get("practice_support") or 0)
    n_core = int(role_counts.get("domain_core") or 0)
    if args.n >= 3 and n_support == 0:
        warnings.append(
            {
                "code": "all_domain_core",
                "message": (
                    f"picked {args.n} skills with 0 practice_support "
                    f"(domain_core={n_core}); remix may lack verify/eval/continuity members"
                ),
                "hint": (
                    "practice-mix auto only engages at --n >= 5; "
                    "pass --practice-mix on or raise --n, and ensure discover used "
                    "--practice-support on/auto"
                ),
                "practice_mix_active": mix,
                "auto_mix_threshold": 5,
            }
        )

    payload = {
        "decision": "PASS",
        "mode": "remix",
        "n": args.n,
        "n_eligible": len(eligible),
        "n_middling": len(eligible),  # legacy alias
        "practice_mix": mix,
        "role_counts": role_counts,
        "warnings": warnings,
        "chosen": chosen,
        "ids": [c.get("id") for c in chosen],
        "diversity": {
            "owners": sorted({owner_token(c) for c in chosen}),
            "skill_names": [skill_token(c) for c in chosen],
            "discovery_roles": role_counts,
        },
        "strategy_used": "submodular" if use_submodular else "diverse",
    }
    if info_comp is not None:
        payload["information_telemetry"] = info_comp["principled"]
        payload["vs_github_popularity_top_n"] = {
            "github_top_ids": info_comp["github_top_ids"],
            "github_top_telemetry": info_comp["github_top"],
            "lift": info_comp["lift"],
        }
    if args.write_chosen:
        args.write_chosen.parent.mkdir(parents=True, exist_ok=True)
        args.write_chosen.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2) if args.json else payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
