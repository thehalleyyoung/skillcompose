#!/usr/bin/env python3
"""Parse CLI args for thehalleyyoung/skillcompose (/skillcompose) into JSON.

`--args` is the optional desired argument interface of the final skill:
arguments it should be able to take, and, with a take: prefix, arguments it
should take. It is not a meta-skill control flag and is not folded into the
discovery query. See references/theory.md §3.5.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys


def split_composed_args(raw: str | None) -> list[str]:
    """Split `--args` into interface tokens. Commas win; otherwise shlex."""
    if raw is None:
        return []
    text = str(raw).strip()
    if not text:
        return []
    if "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    try:
        return shlex.split(text)
    except ValueError:
        return [text]


def classify_desired_interface(tokens: list[str]) -> dict[str, list[str]]:
    """Map `--args` tokens onto D = (D_take, D_able).

    An unmarked name is an argument the final skill is able to take.
    A `take:` prefix also puts it in the set of arguments the final skill takes.
    Taking implies being able to take, so D_take is a subset of D_able.
    """
    take: list[str] = []
    able: list[str] = []
    for token in tokens:
        raw = token.strip()
        required = False
        if raw.lower().startswith("take:"):
            raw = raw[5:].strip()
            required = True
        if not raw:
            continue
        if raw not in able:
            able.append(raw)
        if required and raw not in take:
            take.append(raw)
    return {"take": take, "able": able}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skillcompose",
        add_help=True,
        description=(
            "thehalleyyoung/skillcompose: upgrade an eligible marketplace skill, "
            "or remix N skills into a Lawvere–Amari manifold package."
        ),
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
    p.add_argument(
        "--wip",
        default=None,
        help="Existing skillcompose-wip-* directory (skillremix-wip-* / randomupgrade-wip-* still resume)",
    )
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
    p.add_argument(
        "--args",
        default=None,
        dest="composed_args",
        help=(
            "Optional desired interface of the final skill: arguments it should "
            "be able to take, e.g. '--author-persona, --premise'. Prefix take: "
            "for an argument it should take, e.g. 'take:--premise'. Not folded "
            "into the discovery query."
        ),
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
        "composed_args": split_composed_args(args.composed_args),
        "composed_args_raw": args.composed_args,
        "desired_interface": classify_desired_interface(split_composed_args(args.composed_args)),
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
