#!/usr/bin/env python3
"""Validate skillremix CLI args / WIP paths before Phase 0 work.

Used by parse_args.py and resume_forge.py so --status/--resume never
silently operate on CALLER_CWD (empty --wip → ".") and invent a fork_dir.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PIN_RE = re.compile(r"^[^/\s]+/[^@\s]+@[^\s]+$")

WIP_NAME_RE = re.compile(r"(^|/)(skillremix-wip-|randomupgrade-wip-)[^/]*$", re.I)


def wip_error(code: str, message: str, **extra) -> dict:
    return {"ok": False, "error": code, "message": message, **extra}


def validate_wip_path(wip: str | Path | None, *, must_exist: bool = True) -> dict:
    if wip is None or (isinstance(wip, str) and not str(wip).strip()):
        return wip_error(
            "wip_required",
            "--wip is required and must be a skillremix-wip-* or randomupgrade-wip-* directory",
        )
    raw = str(wip).strip()
    if raw in {".", "./", ""}:
        return wip_error(
            "wip_invalid",
            "refusing empty or cwd --wip (would false-status a random SKILL.md in CALLER_CWD)",
            wip=raw,
        )
    path = Path(raw).expanduser()
    # Resolve only after rejecting cwd sentinels; still reject if resolve lands on cwd-looking names
    try:
        resolved = path.resolve()
    except OSError as e:
        return wip_error("wip_invalid", f"cannot resolve --wip: {e}", wip=raw)

    name_ok = bool(WIP_NAME_RE.search(resolved.as_posix())) or bool(
        WIP_NAME_RE.search(path.as_posix())
    )
    if not name_ok:
        return wip_error(
            "wip_name",
            "--wip must look like skillremix-wip-<id> or randomupgrade-wip-<id>",
            wip=str(resolved),
        )
    if must_exist and not resolved.is_dir():
        return wip_error("wip_missing", f"--wip directory does not exist: {resolved}", wip=str(resolved))
    return {"ok": True, "wip": str(resolved)}


def contradictory_flags(args: dict) -> dict | None:
    """Reject flag pairs that make Phase 0 branch choice ambiguous (UC04)."""
    status = bool(args.get("status"))
    resume = bool(args.get("resume"))
    early = [k for k in ("discover_only", "audit_only", "remix_plan_only") if args.get(k)]
    if status and resume:
        return wip_error(
            "contradictory_flags",
            "refusing --status together with --resume (pick one Phase 0 branch)",
            flags=["status", "resume"],
            hint="use --status --wip PATH  OR  --resume --wip PATH",
        )
    if resume and early:
        return wip_error(
            "contradictory_flags",
            f"refusing --resume together with early-stop flags: {early}",
            flags=["resume", *early],
            hint="early-stop modes print and exit; do not combine with --resume",
        )
    return None


def validate_parsed(args: dict) -> dict:
    """Validate a parse_args-style dict. Returns {ok, ...} or error dict."""
    conflict = contradictory_flags(args)
    if conflict is not None:
        return conflict
    status = bool(args.get("status"))
    resume = bool(args.get("resume"))
    wip = args.get("wip")
    if status or resume:
        vw = validate_wip_path(wip, must_exist=True)
        if not vw.get("ok"):
            vw["hint"] = "pass --wip /path/to/skillremix-wip-<RUN_ID>"
            return vw
        args = {**args, "wip": vw["wip"]}
    pin = args.get("pin")
    if pin and not PIN_RE.match(str(pin).strip()):
        return wip_error(
            "pin_format",
            "pin must be owner/repo@skill",
            pin=pin,
        )
    if args.get("remix_plan_only") and not args.get("n"):
        return wip_error("remix_plan_only_needs_n", "--remix-plan-only requires --n N (N>=2)")
    if args.get("n") is not None and int(args["n"]) < 2:
        return wip_error("n_too_small", "--n requires N >= 2")
    return {"ok": True, "args": args}


def main() -> int:
    """CLI: pass parse_args JSON on stdin, or --wip PATH for WIP-only check."""
    if len(sys.argv) >= 3 and sys.argv[1] == "--wip":
        out = validate_wip_path(sys.argv[2], must_exist="--allow-missing" not in sys.argv)
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps(wip_error("stdin_empty", "expected parse_args JSON on stdin"), indent=2))
        return 2
    args = json.loads(raw)
    out = validate_parsed(args)
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
