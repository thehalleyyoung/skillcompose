#!/usr/bin/env python3
"""Resume / status helpers for skillremix WIP forge runs (50-round phase model)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from args_preflight import validate_wip_path  # noqa: E402
from forge_phases import FORGE_ROUNDS, phase_for_round  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_json(path: Path) -> dict | list | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def find_fork_dir(wip: Path) -> Path | None:
    candidates = []
    for p in wip.iterdir():
        if p.is_dir() and p.name not in {"discovery", "forge", "upstream"} and (p / "SKILL.md").exists():
            candidates.append(p)
    if candidates:
        return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    return None


def detect_mode(wip: Path, chosen_n: dict | None, remix_plan: dict | None) -> str:
    if chosen_n or remix_plan:
        return "remix"
    if (wip / "discovery" / "chosen.json").exists():
        return "upgrade"
    if (wip / "forge" / "remix_plan.json").exists():
        return "remix"
    return "upgrade"


def resume_hint(
    *,
    mode: str,
    next_r: int | None,
    done: bool,
    fork: Path | None,
    chosen: dict | None,
    chosen_n: dict | None,
    remix_plan_path: Path | None,
    phases_path: Path | None,
    n_log_rows: int,
) -> str:
    if done:
        return "Forge complete — run ship_check.py on fork/package, then dual-install if PASS."
    if next_r and fork:
        return f"Continue Phase 4 forge round {next_r} in {fork} (kind from status.active_kind)."
    if next_r and not fork and remix_plan_path:
        return (
            f"Remix plan exists at {remix_plan_path}; init package (R5) then forge round {next_r}."
        )
    if next_r and not fork and chosen_n:
        return "Remix members chosen — finish R3 audits + R4 propose_remix / R5 package init before forge."
    if next_r and not fork and chosen:
        return "Single-upgrade chosen — clone+init_fork+audit if missing, then forge round 1."
    if phases_path and fork and n_log_rows == 0:
        return f"Audit/plan ready under {fork}; start forge round 1 (or stop if --audit-only)."
    if mode == "remix" and remix_plan_path and not fork:
        return f"Refine and materialize package from {remix_plan_path}."
    return "Inspect discovery/ and forge/ under --wip; ensure chosen/chosen_n and package SKILL.md exist."


def status(wip: Path, rounds: int = FORGE_ROUNDS, *, full: bool = False) -> dict:
    log = wip / "forge" / "usefulness_forge.jsonl"
    phases_path = wip / "forge" / "forge_phases.json"
    if not phases_path.exists():
        phases_path = wip / "forge" / "upgrade_themes.json"
    chosen_path = wip / "discovery" / "chosen.json"
    chosen_n_path = wip / "discovery" / "chosen_n.json"
    remix_plan_path = wip / "forge" / "remix_plan.json"

    chosen = load_json(chosen_path) if chosen_path.exists() else None
    chosen_n = load_json(chosen_n_path) if chosen_n_path.exists() else None
    remix_plan = load_json(remix_plan_path) if remix_plan_path.exists() else None

    rows = load_jsonl(log)
    by_round = sorted({int(r["round"]) for r in rows if "round" in r})
    last = by_round[-1] if by_round else 0
    next_r = last + 1 if last < rounds else None
    fork = find_fork_dir(wip)
    active = phase_for_round(next_r) if next_r else None
    mode = detect_mode(wip, chosen_n if isinstance(chosen_n, dict) else None, remix_plan if isinstance(remix_plan, dict) else None)

    chosen_ids = None
    if isinstance(chosen_n, dict):
        chosen_ids = chosen_n.get("ids")
        if not chosen_ids and isinstance(chosen_n.get("chosen"), list):
            chosen_ids = [c.get("id") for c in chosen_n["chosen"] if isinstance(c, dict)]
    elif isinstance(chosen, dict) and chosen.get("id"):
        chosen_ids = [chosen["id"]]

    # Fallback: ids from remix plan members
    if not chosen_ids and isinstance(remix_plan, dict):
        members = remix_plan.get("members") or remix_plan.get("buffs") or []
        ids = []
        for m in members:
            if isinstance(m, dict) and m.get("id"):
                ids.append(m["id"])
        chosen_ids = ids or None

    package_dir = str(fork) if fork else None
    rp = str(remix_plan_path) if remix_plan_path.exists() else None
    pp = str(phases_path) if phases_path.exists() else None
    hint = resume_hint(
        mode=mode,
        next_r=next_r,
        done=last >= rounds,
        fork=fork,
        chosen=chosen if isinstance(chosen, dict) else None,
        chosen_n=chosen_n if isinstance(chosen_n, dict) else None,
        remix_plan_path=Path(rp) if rp else None,
        phases_path=Path(pp) if pp else None,
        n_log_rows=len(rows),
    )
    resume_ready = bool(
        (fork and next_r)
        or (rp and chosen_ids)
        or (chosen and fork)
        or (pp and fork)
    )

    progress = {
        "rounds_required": rounds,
        "rounds_completed": last,
        "rounds_present": by_round,
        "next_round": next_r,
        "n_log_rows": len(rows),
        "kind": (active or {}).get("kind") if active else None,
        "done": last >= rounds,
    }

    # Compact by default (UC01): do not dump full chosen_n / chosen blobs
    if full:
        chosen_out = chosen if isinstance(chosen, dict) else None
        chosen_n_out = chosen_n if isinstance(chosen_n, dict) else None
    else:
        chosen_out = (
            {"id": chosen.get("id"), "installs": chosen.get("installs")}
            if isinstance(chosen, dict) and chosen.get("id")
            else None
        )
        if isinstance(chosen_n, dict):
            chosen_n_out = {
                "n": chosen_n.get("n") or len(chosen_ids or []),
                "decision": chosen_n.get("decision"),
                "ids": chosen_ids,
                "note": "full member blobs omitted; pass --full to include chosen_n_full",
            }
        else:
            chosen_n_out = None

    out = {
        "wip": str(wip),
        "mode": mode,
        "fork_dir": package_dir,
        "package_dir": package_dir,
        "chosen": chosen_out,
        "chosen_n": chosen_n_out,
        "chosen_ids": chosen_ids,
        "progress": progress,
        "remix_plan_path": rp,
        "rounds_required": rounds,
        "rounds_completed": last,
        "next_round": next_r,
        "done": last >= rounds,
        "active_phase": active if full else None,
        "active_theme": (active or {}).get("id") if active else None,
        "active_kind": (active or {}).get("kind") if active else None,
        "n_log_rows": len(rows),
        "phases_path": pp,
        "resume_hint": hint,
        "resume_ready": resume_ready,
        "full": full,
    }
    if full and isinstance(chosen_n, dict):
        out["chosen_n_full"] = chosen_n
    if full and isinstance(chosen, dict):
        out["chosen_full"] = chosen
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status")
    s.add_argument("--wip", type=Path, required=True)
    s.add_argument("--rounds", type=int, default=FORGE_ROUNDS)
    s.add_argument("--json", action="store_true")
    s.add_argument(
        "--full",
        action="store_true",
        help="Include full chosen/chosen_n member blobs (default is compact)",
    )

    r = sub.add_parser("next")
    r.add_argument("--wip", type=Path, required=True)
    r.add_argument("--rounds", type=int, default=FORGE_ROUNDS)
    r.add_argument("--json", action="store_true")

    args = ap.parse_args()
    vw = validate_wip_path(args.wip, must_exist=True)
    if not vw.get("ok"):
        print(json.dumps(vw, indent=2))
        return 2
    wip = Path(vw["wip"])
    full = bool(getattr(args, "full", False))
    st = status(wip, args.rounds, full=full)
    if args.cmd == "next":
        out = {
            "next_round": st["next_round"],
            "theme": st["active_theme"],
            "kind": st["active_kind"],
            "phase": st["active_phase"],
            "fork_dir": st["fork_dir"],
            "mode": st["mode"],
            "resume_hint": st["resume_hint"],
            "done": st["done"],
            "chosen_ids": st.get("chosen_ids"),
            "progress": st.get("progress"),
        }
        print(json.dumps(out, indent=2) if args.json else out)
        return 0 if not st["done"] else 1
    print(json.dumps(st, indent=2) if args.json else st)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
