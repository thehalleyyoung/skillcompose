#!/usr/bin/env python3
"""Parse CLI args for /skillremix (legacy: /randomupgrade) into JSON."""
from __future__ import annotations

import argparse
import json
import shlex
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skillremix",
        add_help=True,
        description="Upgrade an eligible marketplace skill (adoption floor; popular OK), or remix N skills into sub+super skills.",
    )
    p.add_argument("query", nargs="*", help="Search words (optional)")
    p.add_argument("--pin", default=None, help="owner/repo@skill (single-upgrade mode)")
    p.add_argument("--name", default=None, help="Fork / superskill name")
    p.add_argument("--seed", default=None, help="PRNG seed for eligible pick")
    p.add_argument("--min-installs", type=int, default=80)
    p.add_argument(
        "--max-installs",
        type=int,
        default=None,
        help="Optional upper install cap (default: none — highly popular allowed)",
    )
    p.add_argument("--min-stars", type=int, default=15)
    p.add_argument(
        "--max-stars",
        type=int,
        default=None,
        help="Optional upper star cap (default: none — highly popular allowed)",
    )
    p.add_argument("--forge-rounds", type=int, default=50)
    p.add_argument(
        "--round-interval-sec",
        type=int,
        default=90,
        help="Seconds between forge-round prompts (each round is its own scheduled prompt)",
    )
    p.add_argument("--ask-themes", action="store_true", help="Pause after locking forge phases")
    p.add_argument("--ask-phases", action="store_true", help="Alias for --ask-themes")
    p.add_argument("--private", action="store_true")
    p.add_argument("--local-only", action="store_true")
    p.add_argument("--discover-only", action="store_true", help="Stop after candidates + pick")
    p.add_argument("--audit-only", action="store_true", help="Clone+audit only")
    p.add_argument("--resume", action="store_true", help="Resume forge from WIP")
    p.add_argument("--wip", default=None, help="Existing skillremix-wip-* or randomupgrade-wip-* path")
    p.add_argument("--status", action="store_true", help="Print forge status JSON for --wip")
    p.add_argument("--domain", default=None, help="Domain pack: writing|devops|data|research|automation")
    # Remix mode
    p.add_argument(
        "--n",
        type=int,
        default=None,
        metavar="N",
        help="Remix mode: pick N eligible marketplace skills (popular OK), buff the right ones, invent subskills + a superskill",
    )
    p.add_argument(
        "--remix-plan-only",
        action="store_true",
        help="With --n: stop after remix plan (buff map + subskills + superskill) is written",
    )
    p.add_argument(
        "--allow-unknown",
        action="store_true",
        help="Allow unknown licenses through license_gate (not recommended)",
    )
    return p


def main() -> int:
    from args_preflight import validate_parsed  # local sibling

    raw = " ".join(sys.argv[1:])
    if len(sys.argv) == 2 and ("--" in sys.argv[1] or " " in sys.argv[1]):
        try:
            argv = shlex.split(sys.argv[1])
        except ValueError:
            argv = sys.argv[1:]
    else:
        argv = sys.argv[1:]
    args = build_parser().parse_args(argv)
    if args.n is not None and args.n < 2:
        print("error: --n requires N >= 2 (use default single-upgrade mode for one skill)", file=sys.stderr)
        return 2
    if args.n is not None and args.pin:
        print("error: --n remix mode cannot combine with --pin (pin is single-skill)", file=sys.stderr)
        return 2
    mode = "remix" if args.n else "upgrade"
    out = {
        "query": " ".join(args.query).strip(),
        "pin": args.pin,
        "name": args.name,
        "seed": args.seed,
        "min_installs": args.min_installs,
        "max_installs": args.max_installs,
        "min_stars": args.min_stars,
        "max_stars": args.max_stars,
        "forge_rounds": args.forge_rounds,
        "round_interval_sec": args.round_interval_sec,
        "ask_themes": args.ask_themes or args.ask_phases,
        "private": args.private,
        "local_only": args.local_only,
        "discover_only": args.discover_only,
        "audit_only": args.audit_only,
        "resume": args.resume,
        "wip": args.wip,
        "status": args.status,
        "domain": args.domain,
        "n": args.n,
        "remix_plan_only": args.remix_plan_only,
        "allow_unknown": args.allow_unknown,
        "mode": mode,
        "raw": raw,
    }
    pre = validate_parsed(out)
    if not pre.get("ok"):
        print(json.dumps(pre, indent=2))
        return 2
    if pre.get("args", {}).get("wip"):
        out["wip"] = pre["args"]["wip"]
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
