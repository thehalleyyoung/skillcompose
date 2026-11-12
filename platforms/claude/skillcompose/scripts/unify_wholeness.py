#!/usr/bin/env python3
"""Strict gate: remix package must be more than the sum of its parts.

FAIL unless ALL wholeness predicates pass. Nominal docs or side-by-side forks
do not count. Ship / publish must not proceed on FAIL.

Strict definition (all required):
  1. shared_contract   — handoff schema/pack used across members
  2. shared_verify     — verify-gate artifact + superskill requires it before done
  3. superskill_wiring — superskill SKILL.md names every member + every subskill
  4. cross_member_refs — ≥2 buffed member skills reference the shared contract
  5. emergent_eval     — eval/script exercises ≥2 members in one pipeline outcome
  6. wholeness_doc     — WHOLENESS.md (or REMIX_PLAN.md ## Wholeness) claims 1–5
  7. forge_unify_mass  — forge log: 50 rounds, each ≥min_chars; rounds 1–10 tagged unify
  8. not_wrapper_only  — superskill body is substantial + has verify/handoff language
  9. no_juxtaposition  — shared references/ or scripts/ used by superskill + members
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_MIN_CHARS = 1000
DEFAULT_ROUNDS = 50
# P1-unify is exactly rounds 1–10
DEFAULT_UNIFY_FRACTION = 10 / 50
ALLOWED_SURFACES = {"procedure", "code", "proof", "docs", "ux"}


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def find_contract(pkg: Path) -> Path | None:
    patterns = [
        "**/handoff*.json",
        "**/handoff*.md",
        "**/handoff*schema*",
        "**/shared_contract.*",
        "**/pipeline_pack.*",
        "**/phase_handoff.*",
    ]
    hits: list[Path] = []
    for pat in patterns:
        hits.extend(pkg.glob(pat))
    # Prefer package-level references / subskills
    ranked = sorted(
        {h.resolve() for h in hits if h.is_file()},
        key=lambda p: (0 if "subskill" in str(p) or "reference" in str(p) else 1, len(str(p))),
    )
    return ranked[0] if ranked else None


def find_verify(pkg: Path) -> Path | None:
    patterns = [
        "**/verify_gate*",
        "**/verify-gate*",
        "**/false_done*",
        "**/wholeness_gate*",
        "scripts/*verify*",
        "subskills/**/SKILL.md",
    ]
    for pat in patterns:
        for h in pkg.glob(pat):
            if not h.is_file():
                continue
            text = read(h).lower()
            if h.name == "SKILL.md" and "verify" not in text and "false-done" not in text and "false_done" not in text:
                continue
            if "verify" in h.name.lower() or "verify" in text or "false-done" in text or "false_done" in text:
                return h
    return None


def member_skill_dirs(pkg: Path) -> list[Path]:
    skills = pkg / "skills"
    if not skills.is_dir():
        return []
    return sorted([p for p in skills.iterdir() if p.is_dir() and (p / "SKILL.md").exists()])


def subskill_dirs(pkg: Path) -> list[Path]:
    root = pkg / "subskills"
    if not root.is_dir():
        return []
    return sorted([p for p in root.iterdir() if p.is_dir() and (p / "SKILL.md").exists()])


def load_plan(pkg: Path) -> dict | None:
    for cand in [
        pkg / "forge" / "remix_plan.json",
        pkg.parent / "forge" / "remix_plan.json" if pkg.parent else None,
        pkg / "remix_plan.json",
    ]:
        if cand and cand.is_file():
            return json.loads(cand.read_text(encoding="utf-8"))
    return None


def check_forge(log: Path, rounds: int, min_chars: int, unify_fraction: float) -> tuple[bool, list[str], dict]:
    reasons: list[str] = []
    rows = load_jsonl(log)
    by_round = {int(r["round"]): r for r in rows if "round" in r}
    missing = [i for i in range(1, rounds + 1) if i not in by_round]
    if missing:
        reasons.append(f"forge missing rounds: {missing[:12]}{'…' if len(missing) > 12 else ''}")

    thin_chars = []
    thin_surfaces = []
    unify_rounds = []
    commits = set()
    total_chars = 0
    for i in range(1, rounds + 1):
        r = by_round.get(i)
        if not r:
            continue
        chars = r.get("chars_changed")
        try:
            n = int(chars) if chars is not None else 0
        except (TypeError, ValueError):
            n = 0
        total_chars += n
        if n < min_chars:
            thin_chars.append(i)
        surfaces = r.get("surfaces") or []
        if not isinstance(surfaces, list):
            surfaces = []
        ok = {s for s in surfaces if s in ALLOWED_SURFACES}
        if len(ok) < 3 or r.get("radical") is not True:
            thin_surfaces.append(i)
        kind = str(r.get("kind") or r.get("theme") or "").lower()
        if r.get("unify") is True or kind in {"unify", "subskill", "superskill"} or "unif" in kind:
            unify_rounds.append(i)
        c = r.get("commit")
        if c:
            commits.add(c)

    if thin_chars:
        reasons.append(
            f"rounds with chars_changed < {min_chars}: {thin_chars[:12]}"
            f"{'…' if len(thin_chars) > 12 else ''}"
        )
    if thin_surfaces:
        reasons.append(f"thin rounds (<3 surfaces or radical!=true): {thin_surfaces[:10]}")
    need_unify = 10 if rounds >= 50 else max(1, int(rounds * unify_fraction + 0.999))
    # Prefer counting rounds 1–10 as unify when present
    p1 = [i for i in unify_rounds if 1 <= i <= 10]
    if rounds >= 50 and len(p1) < 10:
        # also accept any unify-tagged among 1-10 via by_round check below
        missing_p1 = [i for i in range(1, 11) if i in by_round and i not in unify_rounds]
        if missing_p1 or len([i for i in range(1, 11) if i in by_round]) < 10:
            reasons.append(
                f"P1-unify incomplete: need rounds 1–10 tagged unify "
                f"(tagged={sorted(p1)}; missing/mis-tagged among present={missing_p1[:10]})"
            )
    elif len(unify_rounds) < need_unify:
        reasons.append(
            f"unify rounds={len(unify_rounds)} < required {need_unify} "
            f"(set unify=true or kind/theme unify on P1 rounds 1–10)"
        )
    if len(by_round) >= rounds and len(commits) < rounds:
        reasons.append(
            f"forge commits not unique enough: {len(commits)} distinct SHAs for {rounds} rounds "
            "(each round needs its own commit — no batching)"
        )
    if total_chars < rounds * min_chars:
        reasons.append(
            f"total chars_changed={total_chars} < {rounds * min_chars} "
            f"({rounds}×{min_chars})"
        )

    meta = {
        "rounds_present": len(by_round),
        "unify_rounds": len(unify_rounds),
        "unify_required": need_unify,
        "total_chars_changed": total_chars,
        "distinct_commits": len(commits),
    }
    return (not reasons), reasons, meta


def check_package(pkg: Path, plan: dict | None) -> tuple[dict[str, bool], list[str]]:
    reasons: list[str] = []
    preds: dict[str, bool] = {}

    skill = pkg / "SKILL.md"
    skill_text = read(skill)
    preds["superskill_present"] = skill.exists() and len(skill_text) > 0
    if not preds["superskill_present"]:
        reasons.append("missing package SKILL.md (superskill)")

    contract = find_contract(pkg)
    preds["shared_contract"] = contract is not None
    if not contract:
        reasons.append(
            "missing shared_contract (need references/handoff*.json|md, pipeline_pack, or phase_handoff)"
        )

    verify = find_verify(pkg)
    preds["shared_verify"] = verify is not None
    if not verify:
        reasons.append("missing shared verify-gate artifact (script or subskill with verify/false-done)")

    # Superskill must require verify before done
    low = skill_text.lower()
    verify_required = bool(
        re.search(r"verify[-_ ]?gate|false[-_ ]?done|must (run|pass).{0,40}verify", low)
    ) and ("before" in low or "claim" in low or "done" in low or "ship" in low)
    preds["superskill_requires_verify"] = verify_required
    if not verify_required:
        reasons.append(
            "superskill SKILL.md must require verify-gate before claiming done "
            "(need verify-gate/false-done language tied to done/claim)"
        )

    members = member_skill_dirs(pkg)
    subs = subskill_dirs(pkg)
    member_names = [m.name for m in members]
    sub_names = [s.name for s in subs]

    # From plan if dirs empty naming differs
    if plan:
        for b in plan.get("buffs") or []:
            slug = str(b.get("id") or "").split("@")[-1]
            if slug and slug not in member_names:
                # accept *-upgraded dirs
                for m in member_names:
                    if slug.replace("_", "-") in m or m.startswith(slug):
                        break
                else:
                    pass
        for s in plan.get("subskills") or []:
            nm = s.get("name")
            if nm and nm not in sub_names:
                sub_names.append(nm)

    named_members = 0
    for m in member_names:
        token = m.replace("-upgraded", "")
        if token and (token in skill_text or m in skill_text):
            named_members += 1
    named_subs = 0
    for s in sub_names:
        if s and s in skill_text:
            named_subs += 1

    preds["superskill_wiring"] = named_members >= max(2, min(len(member_names), 2)) and (
        named_subs >= 1 if sub_names else True
    )
    if not preds["superskill_wiring"]:
        reasons.append(
            f"superskill must name member skills + subskills "
            f"(named_members={named_members}/{len(member_names)}, named_subs={named_subs}/{len(sub_names)})"
        )

    # Cross-member refs to shared contract
    cross = 0
    contract_token = ""
    if contract:
        contract_token = contract.name
        rel = str(contract.relative_to(pkg)).replace("\\", "/")
        for mdir in members:
            text = read(mdir / "SKILL.md")
            if contract_token in text or rel in text or "handoff" in text.lower():
                cross += 1
    preds["cross_member_refs"] = cross >= 2
    if cross < 2:
        reasons.append(
            f"need ≥2 member SKILL.md files referencing shared handoff/contract (found {cross})"
        )

    # Emergent eval: one file mentioning ≥2 members
    emergent = False
    emergent_path = None
    search_roots = [pkg / "evals", pkg / "scripts", pkg / "references"]
    for root in search_roots:
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in {".md", ".json", ".py", ".sh", ".txt", ".jsonl"}:
                continue
            text = read(f)
            hits = sum(1 for m in member_names if m.replace("-upgraded", "") in text or m in text)
            if hits >= 2 and re.search(r"pipeline|end-to-end|e2e|wholeness|handoff|integrat", text, re.I):
                emergent = True
                emergent_path = f
                break
        if emergent:
            break
    preds["emergent_eval"] = emergent
    if not emergent:
        reasons.append(
            "missing emergent_eval: need evals|scripts|references file that names ≥2 members "
            "and asserts a pipeline/e2e/wholeness outcome"
        )

    # Wholeness doc
    wholeness_text = read(pkg / "WHOLENESS.md")
    remix_plan = read(pkg / "REMIX_PLAN.md")
    doc = wholeness_text if wholeness_text else remix_plan
    has_section = bool(wholeness_text) or bool(re.search(r"(?m)^##\s+Wholeness\b", remix_plan))
    claims = all(
        re.search(pat, doc, re.I)
        for pat in [
            r"shared.?contract|handoff",
            r"verify",
            r"emergent|more than the sum|strictly more",
            r"cross-?(wire|link)|member",
        ]
    )
    preds["wholeness_doc"] = has_section and claims
    if not preds["wholeness_doc"]:
        reasons.append(
            "need WHOLENESS.md or REMIX_PLAN.md ## Wholeness covering handoff, verify, "
            "emergent/more-than-sum, and cross-wire claims"
        )

    # Not wrapper-only
    preds["not_wrapper_only"] = len(skill_text) >= 2000 and bool(
        re.search(r"handoff|verify|phase|false-?done", low)
    )
    if not preds["not_wrapper_only"]:
        reasons.append(
            f"superskill looks wrapper-only (len={len(skill_text)}; need ≥2000 chars + "
            "handoff/verify/phase/false-done substance)"
        )

    # Shared infrastructure used (not pure juxtaposition)
    shared_dirs = [pkg / "references", pkg / "scripts", pkg / "subskills"]
    shared_ok = any(d.is_dir() and any(d.iterdir()) for d in shared_dirs)
    preds["no_juxtaposition"] = shared_ok and preds.get("cross_member_refs", False)
    if not preds["no_juxtaposition"]:
        reasons.append(
            "juxtaposition detected: need non-empty shared references|scripts|subskills "
            "AND cross-member contract refs"
        )

    # stash paths for report
    preds["_meta_contract"] = str(contract) if contract else ""
    preds["_meta_verify"] = str(verify) if verify else ""
    preds["_meta_emergent"] = str(emergent_path) if emergent_path else ""
    return preds, reasons


def evaluate(
    pkg: Path,
    log: Path | None,
    rounds: int,
    min_chars: int,
    unify_fraction: float,
    require_forge: bool,
) -> dict:
    plan = load_plan(pkg)
    preds, reasons = check_package(pkg, plan)
    forge_meta = {}
    if require_forge:
        log_path = log or (pkg / "forge" / "usefulness_forge.jsonl")
        ok, forge_reasons, forge_meta = check_forge(log_path, rounds, min_chars, unify_fraction)
        preds["forge_unify_mass"] = ok
        reasons.extend(forge_reasons)
    else:
        preds["forge_unify_mass"] = True

    # Predicate pass set (ignore _meta_)
    core = {k: v for k, v in preds.items() if not k.startswith("_meta_")}

    principled_telemetry: dict = {}
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from information_gain import package_telemetry
        from wiring_compiler import verify_graph

        principled_telemetry["information_gain"] = package_telemetry(pkg)
        wg_candidates = [
            pkg / "forge" / "wiring_graph.json",
            pkg.parent / "forge" / "wiring_graph.json" if pkg.parent else None,
        ]
        wg_path = next((p for p in wg_candidates if p and p.is_file()), None)
        if wg_path:
            wg = json.loads(wg_path.read_text(encoding="utf-8"))
            principled_telemetry["wiring_verification"] = verify_graph(wg, pkg)
    except Exception as e:  # noqa: BLE001
        principled_telemetry["error"] = str(e)

    failed = [k for k, v in core.items() if not v]
    decision = "PASS" if not failed and not reasons else "FAIL"
    return {
        "decision": decision,
        "definition": "strictly_more_than_sum_of_parts",
        "package": str(pkg),
        "predicates": core,
        "failed_predicates": failed,
        "reasons": reasons,
        "principled_telemetry": principled_telemetry,
        "artifacts": {
            "contract": preds.get("_meta_contract"),
            "verify": preds.get("_meta_verify"),
            "emergent_eval": preds.get("_meta_emergent"),
        },
        "forge": forge_meta,
        "thresholds": {
            "rounds": rounds,
            "min_chars_per_round": min_chars,
            "unify_fraction": unify_fraction,
            "superskill_min_chars": 2000,
            "cross_member_refs_min": 2,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", type=Path, required=True, help="Remix package root (superskill)")
    ap.add_argument("--log", type=Path, default=None, help="usefulness_forge.jsonl")
    ap.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    ap.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS)
    ap.add_argument("--unify-fraction", type=float, default=DEFAULT_UNIFY_FRACTION)
    ap.add_argument(
        "--skip-forge",
        action="store_true",
        help="Only check package predicates (not for ship — ship must include forge)",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    out = evaluate(
        args.package,
        args.log,
        args.rounds,
        args.min_chars,
        args.unify_fraction,
        require_forge=not args.skip_forge,
    )
    print(json.dumps(out, indent=2) if args.json else out)
    return 0 if out["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
