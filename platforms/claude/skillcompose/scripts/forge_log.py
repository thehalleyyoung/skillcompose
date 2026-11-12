#!/usr/bin/env python3
"""Append / validate /skillremix forge round log (strict 50×≥1000-char phase rounds)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

QUESTION = (
    "How can I make this fundamentally better/more useful/more likely to be used "
    "(looking at what's available/what it would be compared to)?"
)
ALLOWED_SURFACES = {"procedure", "code", "proof", "docs", "ux"}
DEFAULT_MIN_CHARS = 1000
DEFAULT_ROUNDS = 50
# Rounds 1–10 must be unification (fixed phase model)
UNIFY_ROUNDS = set(range(1, 11))


def expected_kind(i: int) -> str | None:
    if 1 <= i <= 10:
        return "unify"
    if 11 <= i <= 20:
        return "enhance"
    if 21 <= i <= 44:
        return "metrics"
    if 45 <= i <= 50:
        return "awesome"
    return None


def append_row(args: argparse.Namespace) -> dict:
    compared = json.loads(args.compared_to)
    paths = json.loads(args.paths)
    surfaces = json.loads(args.surfaces)
    if isinstance(surfaces, str):
        surfaces = [surfaces]
    chars = int(args.chars_changed)
    kind = str(args.kind or "buff").lower()
    rnd = int(args.round)
    unify = (
        bool(args.unify)
        or kind in {"unify", "subskill", "superskill"}
        or "unif" in str(args.theme or "").lower()
    )
    if rnd in UNIFY_ROUNDS and not unify and kind != "unify":
        raise SystemExit(
            f"refuse append: round {rnd} is in P1-unify (1–10); pass --kind unify (or --unify)"
        )
    expect = expected_kind(rnd)
    if expect and kind not in {expect, "buff", "subskill", "superskill"} and expect not in str(args.theme or "").lower():
        # Allow legacy kinds only when theme encodes the phase; otherwise nudge
        if kind not in {"unify", "enhance", "metrics", "awesome"}:
            kind = expect
    row = {
        "round": rnd,
        "total": int(args.total),
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": QUESTION,
        "theme": args.theme,
        "kind": kind if kind in {"unify", "enhance", "metrics", "awesome"} else (expect or kind),
        "unify": unify or rnd in UNIFY_ROUNDS,
        "compared_to": compared,
        "gap": args.gap,
        "addition": args.addition,
        "surfaces": surfaces,
        "radical": bool(args.radical),
        "chars_changed": chars,
        "commit": args.commit,
        "paths": paths,
    }
    if chars < int(args.min_chars):
        raise SystemExit(
            f"refuse append: chars_changed={chars} < min_chars={args.min_chars} "
            "(round does not count — keep editing, then re-commit)"
        )
    os.makedirs(os.path.dirname(os.path.abspath(args.log)) or ".", exist_ok=True)
    with open(args.log, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def validate(args: argparse.Namespace) -> dict:
    need = int(args.rounds)
    min_chars = int(args.min_chars)
    rows = []
    if os.path.isfile(args.log):
        with open(args.log, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    by_round = {int(r["round"]): r for r in rows if "round" in r}
    missing = [i for i in range(1, need + 1) if i not in by_round]
    empty = [
        i
        for i, r in by_round.items()
        if not (r.get("gap") and r.get("addition") and r.get("commit") and r.get("theme"))
    ]
    thin = []
    thin_chars = []
    commits: dict[str, list[int]] = {}
    total_chars = 0
    unify_missing = []
    phase_mismatches = []
    for i, r in by_round.items():
        surfaces = r.get("surfaces") or []
        if not isinstance(surfaces, list):
            surfaces = []
        ok = {s for s in surfaces if s in ALLOWED_SURFACES}
        if len(ok) < 3 or r.get("radical") is not True:
            thin.append(i)
        try:
            chars = int(r.get("chars_changed") or 0)
        except (TypeError, ValueError):
            chars = 0
        total_chars += chars
        if chars < min_chars:
            thin_chars.append(i)
        c = r.get("commit")
        if c:
            commits.setdefault(str(c), []).append(i)
        kind = str(r.get("kind") or "").lower()
        theme = str(r.get("theme") or "").lower()
        if i in UNIFY_ROUNDS:
            if not (
                r.get("unify") is True
                or kind in {"unify", "subskill", "superskill"}
                or "unif" in theme
                or "p1-unify" in theme
            ):
                unify_missing.append(i)
        expect = expected_kind(i) if need >= 50 else None
        if expect and getattr(args, "strict_phases", True):
            ok_phase = (
                kind == expect
                or expect in theme
                or (
                    expect == "unify"
                    and (r.get("unify") or kind in {"subskill", "superskill"})
                )
            )
            if not ok_phase:
                phase_mismatches.append({"round": i, "expected": expect, "got": kind or theme})

    dup_commits = {c: rs for c, rs in commits.items() if len(rs) > 1}
    reasons = []
    if missing:
        reasons.append(f"missing rounds: {missing[:10]}{'…' if len(missing) > 10 else ''}")
    if empty:
        reasons.append(f"empty gap/addition/commit/theme: {empty[:10]}")
    if thin:
        reasons.append(f"thin rounds (<3 surfaces or radical!=true): {thin[:10]}")
    if thin_chars:
        reasons.append(
            f"rounds with chars_changed < {min_chars}: {thin_chars[:10]}"
            f"{'…' if len(thin_chars) > 10 else ''}"
        )
    if dup_commits:
        sample = list(dup_commits.items())[:3]
        reasons.append(
            f"batched rounds sharing one commit (forbidden): {sample} — each round needs its own commit"
        )
    if len(by_round) >= need and total_chars < need * min_chars:
        reasons.append(f"total chars_changed={total_chars} < required {need * min_chars}")
    if unify_missing:
        reasons.append(
            f"P1-unify rounds not tagged unify: {unify_missing[:10]} "
            "(rounds 1–10 must be kind=unify / --unify)"
        )
    if phase_mismatches and getattr(args, "strict_phases", True):
        reasons.append(f"phase kind mismatches: {phase_mismatches[:8]}")

    decision = "PASS" if not reasons else "FAIL"
    return {
        "decision": decision,
        "rounds_required": need,
        "rounds_present": len(by_round),
        "min_chars_per_round": min_chars,
        "total_chars_changed": total_chars,
        "unify_rounds_ok": not unify_missing,
        "distinct_commits": len(commits),
        "phase_mismatches": phase_mismatches,
        "reasons": reasons,
        "missing": missing,
        "thin": thin,
        "thin_chars": thin_chars,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("append")
    a.add_argument("--log", required=True)
    a.add_argument("--round", required=True)
    a.add_argument("--total", required=True)
    a.add_argument("--theme", required=True)
    a.add_argument("--gap", required=True)
    a.add_argument("--addition", required=True)
    a.add_argument("--commit", required=True)
    a.add_argument("--compared-to", required=True, help="JSON list")
    a.add_argument("--paths", default="[]")
    a.add_argument("--surfaces", required=True, help="JSON list")
    a.add_argument("--chars-changed", type=int, required=True)
    a.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS)
    a.add_argument(
        "--kind",
        default="buff",
        help="unify|enhance|metrics|awesome (or legacy buff|subskill|superskill)",
    )
    a.add_argument("--unify", action="store_true", help="Mark round as unification work")
    a.add_argument("--radical", action="store_true", default=True)
    a.add_argument("--json", action="store_true")

    v = sub.add_parser("validate")
    v.add_argument("--log", required=True)
    v.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    v.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS)
    v.add_argument(
        "--require-unify-fraction",
        type=float,
        default=None,
        help="Deprecated: P1 rounds 1–10 must be unify regardless",
    )
    v.add_argument(
        "--strict-phases",
        action="store_true",
        default=True,
        help="Require kind to match P1–P4 phase for each round (default on)",
    )
    v.add_argument("--no-strict-phases", action="store_true")
    v.add_argument("--json", action="store_true")

    args = ap.parse_args()
    if args.cmd == "append":
        row = append_row(args)
        print(json.dumps(row, indent=2) if args.json else row)
        return 0
    if getattr(args, "no_strict_phases", False):
        args.strict_phases = False
    out = validate(args)
    print(json.dumps(out, indent=2) if args.json else out)
    return 0 if out["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
