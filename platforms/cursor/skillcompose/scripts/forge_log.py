#!/usr/bin/env python3
"""Append / validate /skillcompose forge round log (strict 50×≥1000-char phase rounds).

From round 11 each round also carries outcome evidence (outcome_round.py): the skill's output on a
real domain task before and after the change. Validation fails when rounds lack it, when more than
20% of them are mostly self-measurement (evals/metrics/tests), or when the output improved in fewer
than half of them.

Every round also carries the contract ratchet (concrete_term.py): the theory's obligations on the term
the package actually runs. No round may raise the contract potential Φ_c or any component of the vector
Lyapunov debt, and from round 11 Φ_c must be 0.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outcome_round import (  # noqa: E402
    MAX_SELF_MEASURE_FRACTION,
    MIN_BETTER_FRACTION,
    OUTCOME_FROM_ROUND,
    focus,
)
from concrete_term import ratchet  # noqa: E402

CONTRACT_ZERO_AFTER = 10

QUESTION = (
    "What is the worst thing about what this skill produces for its user right now, next to what they "
    "could get elsewhere, and what change to the skill makes the next output better?"
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
    if args.contract:
        ct = json.loads(args.contract)
        row["contract"] = {k: ct.get(k) for k in ("decision", "phi_before", "phi", "lyapunov_before", "lyapunov",
                                                  "debts", "reasons")}
    if args.outcome:
        oc = json.loads(args.outcome)
        row["outcome"] = oc.get("outcome", oc)
        if "focus" in oc:
            row["focus"] = oc["focus"]
    if rnd >= OUTCOME_FROM_ROUND and not args.outcome:
        raise SystemExit(
            f"refuse append: round {rnd} has no outcome evidence (before/after output of the skill); "
            "run outcome_round.py check and pass its JSON as --outcome"
        )
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
    no_contract: list[int] = []
    contract_rose: list[int] = []
    contract_nonzero: list[int] = []
    fork = getattr(args, "fork", None)
    no_outcome: list[int] = []
    self_measure: list[int] = []
    better: list[int] = []
    scoped: list[int] = []
    for i, r in sorted(by_round.items()):
        ct = r.get("contract") if isinstance(r.get("contract"), dict) else None
        if ct is None and fork and r.get("commit"):
            try:
                ct = ratchet(Path(fork), f"{r['commit']}~1", str(r["commit"]), False)
            except Exception:
                ct = None
        if ct is None:
            no_contract.append(i)
        else:
            rose = (ct.get("phi") or 0) > (ct.get("phi_before") or 0) or any(
                str(x).startswith("ΔΦ") for x in ct.get("reasons") or [])
            if rose or (ct.get("decision") == "FAIL" and "reasons" not in ct):
                contract_rose.append(i)
            if i > CONTRACT_ZERO_AFTER and ct.get("phi"):
                contract_nonzero.append(i)
        if i >= OUTCOME_FROM_ROUND:
            scoped.append(i)
            oc = r.get("outcome") if isinstance(r.get("outcome"), dict) else {}
            if not (oc.get("before") and oc.get("after") and oc.get("verdict")):
                no_outcome.append(i)
            elif oc.get("verdict") == "better":
                better.append(i)
            fo = r.get("focus") if isinstance(r.get("focus"), dict) else {}
            if not fo and fork and r.get("commit"):
                try:
                    fo = focus(Path(fork), str(r["commit"]))
                except SystemExit:
                    fo = {}
            if fo.get("self_measurement") is True:
                self_measure.append(i)
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
    if no_contract:
        reasons.append(
            f"rounds without a contract ratchet: {no_contract[:10]}{'…' if len(no_contract) > 10 else ''} "
            "(concrete_term.py ratchet; pass --fork to recompute from the commits)"
        )
    if contract_rose:
        reasons.append(
            f"rounds that raised the contract potential or a Lyapunov debt: {contract_rose[:10]} "
            "(the theory's obligations on the package's concrete term must not get worse)"
        )
    if contract_nonzero:
        reasons.append(
            f"rounds after P1-unify with contract obligations still failing: {contract_nonzero[:10]}"
            f"{'…' if len(contract_nonzero) > 10 else ''} (Φ_c must be 0 from round {CONTRACT_ZERO_AFTER + 1})"
        )
    if no_outcome:
        reasons.append(
            f"rounds without before/after output evidence: {sorted(no_outcome)[:10]}"
            f"{'…' if len(no_outcome) > 10 else ''} (from round {OUTCOME_FROM_ROUND}, each round must show "
            "what the skill produced before and after its change: outcome_round.py)"
        )
    if scoped and len(self_measure) > MAX_SELF_MEASURE_FRACTION * len(scoped):
        reasons.append(
            f"self-measurement drift: {len(self_measure)} of {len(scoped)} rounds spent most of their change "
            f"on evals/metrics/tests (max {MAX_SELF_MEASURE_FRACTION:.0%}): {sorted(self_measure)[:10]}"
        )
    with_outcome = len(scoped) - len(no_outcome)
    if with_outcome and len(better) < MIN_BETTER_FRACTION * with_outcome:
        reasons.append(
            f"the output got better in only {len(better)} of {with_outcome} rounds "
            f"(need {MIN_BETTER_FRACTION:.0%}): the forge is not improving what users get"
        )

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
        "contract": {"without": no_contract, "rose": contract_rose, "nonzero_after_unify": contract_nonzero},
        "outcome": {
            "from_round": OUTCOME_FROM_ROUND,
            "without_evidence": sorted(no_outcome),
            "better": sorted(better),
            "self_measurement": sorted(self_measure),
        },
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
    a.add_argument("--contract", default="", help="JSON from concrete_term.py ratchet")
    a.add_argument("--outcome", default="", help="JSON from outcome_round.py check (required from round 11)")
    a.add_argument("--radical", action="store_true", default=True)
    a.add_argument("--json", action="store_true")

    v = sub.add_parser("validate")
    v.add_argument("--log", required=True)
    v.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    v.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS)
    v.add_argument("--fork", default=None, help="package repo: measure focus for rounds logged without it")
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
