#!/usr/bin/env python3
"""Pre-publish ship checklist for an upgraded / remixed package.

Hard-fails until forge mass (50×≥1000 chars, unique commits, P1–P4 kinds) and
phase artifacts (METRICS.md, AWESOME_PROOF.md). Remix also needs unify_wholeness PASS.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forge_log import validate as forge_validate  # noqa: E402
from forge_phases import FORGE_ROUNDS, MIN_CHARS_PER_ROUND  # noqa: E402
from unify_wholeness import evaluate as unify_evaluate  # noqa: E402


class NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def is_remix(fork: Path) -> bool:
    if (fork / "REMIX_PLAN.md").exists() or (fork / "WHOLENESS.md").exists():
        return True
    if (fork / "forge" / "remix_plan.json").exists():
        return True
    if (fork / "subskills").is_dir() and (fork / "skills").is_dir():
        return True
    return False


def check_metrics_doc(fork: Path) -> list[str]:
    reasons = []
    path = fork / "METRICS.md"
    if not path.is_file():
        # also accept evals card
        alt = list((fork / "evals").glob("*.md")) if (fork / "evals").is_dir() else []
        if not alt and not (fork / "evals" / "evals.json").exists():
            return ["missing METRICS.md (P3) — need reproducible best-in-some-way metrics"]
        text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in alt[:3])
        if (fork / "evals" / "evals.json").exists():
            text += (fork / "evals" / "evals.json").read_text(encoding="utf-8", errors="replace")
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    if not re.search(r"reproduc|command|script|pytest|smoke|make |python ", low):
        reasons.append("METRICS.md must include a reproducible command/script")
    if not re.search(r"baseline|incumbent|control|neighbor|compet", low):
        reasons.append("METRICS.md must name a baseline/incumbent/neighbor comparison")
    if not re.search(r"best|outperform|delta|lift|win|superior", low):
        reasons.append("METRICS.md must state a best-in-some-way claim (or narrowed honest claim)")
    if not re.search(r"result|score|rate|%\b|pass", low):
        reasons.append("METRICS.md must record numeric/reproducible results")
    if re.search(r"(?i)did not outperform|failed to beat|underperform", text):
        if not re.search(r"(?i)fix|narrow|revised claim|after fix", text):
            reasons.append(
                "METRICS.md reports underperformance without a fix/narrowed-claim reflection loop"
            )
    return reasons


def check_awesome_doc(fork: Path) -> list[str]:
    reasons = []
    path = fork / "AWESOME_PROOF.md"
    if not path.is_file():
        return [
            "missing AWESOME_PROOF.md (P4) — need a real artifact (e.g. novel) or "
            "≥99%-confident third-party bug find with public URL"
        ]
    text = path.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    has_artifact = bool(
        re.search(r"(?i)(novel|manuscript|artifact|built|wrote|generated).{0,80}\.(md|txt|pdf)", text)
    ) or bool(re.search(r"(?i)path:\s*\S+", text))
    has_bug = bool(
        re.search(
            r"https?://(github|bitbucket|gitlab)\.[^\s)]+",
            text,
            re.I,
        )
    ) and bool(re.search(r"(?i)bug|issue|vulnerability|defect", text))
    if not (has_artifact or has_bug):
        reasons.append(
            "AWESOME_PROOF.md must cite a real artifact path OR a public GitHub/Bitbucket/GitLab bug URL"
        )
    if has_bug:
        if not re.search(r"99\s*%|0\.99|high confidence|≥\s*99", low):
            reasons.append("third-party bug proof must state ≥99% confidence it is a real bug")
        if not re.search(r"(?i)could not|couldn't|without (this|our|the) (tool|skill)|necessary", text):
            reasons.append(
                "bug proof must argue the finding could not have been made without this tool/skill"
            )
    if len(text) < 500:
        reasons.append("AWESOME_PROOF.md too thin (<500 chars)")
    return reasons


def check(fork: Path, rounds: int = FORGE_ROUNDS, min_chars: int = MIN_CHARS_PER_ROUND) -> dict:
    reasons = []
    warnings = []

    def need(cond: bool, msg: str):
        if not cond:
            reasons.append(msg)

    skill = fork / "SKILL.md"
    need(skill.exists(), "missing SKILL.md")
    need((fork / "UPSTREAM.md").exists(), "missing UPSTREAM.md")
    need(
        (fork / "COMPARISON.md").exists() or (fork / "REMIX_PLAN.md").exists(),
        "missing COMPARISON.md or REMIX_PLAN.md",
    )
    need(
        (fork / "UPGRADE_PLAN.md").exists()
        or (fork / "forge" / "forge_phases.json").exists()
        or (fork / "forge" / "upgrade_themes.json").exists()
        or (fork / "forge" / "remix_plan.json").exists()
        or (fork / "REMIX_PLAN.md").exists(),
        "missing UPGRADE_PLAN / forge_phases / remix plan",
    )
    need((fork / "install.sh").exists(), "missing install.sh")
    readme = (fork / "README.md").read_text(encoding="utf-8") if (fork / "README.md").exists() else ""
    need(bool(re.search(r"(?m)^## Install", readme)), "README missing ## Install")
    need(bool(re.search(r"(?m)^## Use \(after install\)", readme)), "README missing ## Use (after install)")
    need(bool(re.search(r"```(?:text|bash|shell)?\n\s*/[\w-]+", readme)), "README missing fenced /skill args example")

    log = fork / "forge" / "usefulness_forge.jsonl"
    forge_out = None
    if not log.exists():
        reasons.append("missing forge/usefulness_forge.jsonl — copy from WIP; ship cannot pass without it")
    else:
        forge_out = forge_validate(
            NS(
                log=str(log),
                rounds=rounds,
                min_chars=min_chars,
                strict_phases=True,
                require_unify_fraction=None,
            )
        )
        if forge_out["decision"] != "PASS":
            reasons.extend([f"forge_log: {r}" for r in forge_out.get("reasons") or ["FAIL"]])

    forge_md = fork / "USEFULNESS_FORGE.md"
    need(forge_md.exists() and forge_md.stat().st_size > 50, "USEFULNESS_FORGE.md missing or empty")

    reasons.extend(check_metrics_doc(fork))
    reasons.extend(check_awesome_doc(fork))

    # dry_run_gates --fast is not enough for publish (stamp from scripts/dry_run_gates.sh)
    stamp = fork / "review" / "last_dry_run.json"
    if stamp.is_file():
        try:
            import json as _json
            st = _json.loads(stamp.read_text(encoding="utf-8"))
            if st.get("mode") == "fast":
                reasons.append(
                    "review/last_dry_run.json mode=fast — re-run bash scripts/dry_run_gates.sh "
                    "(without --fast) before publish"
                )
        except Exception as e:
            warnings.append(f"could not read dry_run stamp: {e}")


    try:
        proc = subprocess.run(
            ["git", "-C", str(fork), "log", "--oneline"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        forge_commits = [l for l in (proc.stdout or "").splitlines() if "forge(" in l]
        if len(forge_commits) < rounds:
            reasons.append(
                f"only {len(forge_commits)} forge(*) commits visible; need ≥{rounds} "
                "(each round must be its own commit — nominal batching fails ship)"
            )
    except Exception as e:
        reasons.append(f"git log failed: {e}")

    unify_out = None
    if is_remix(fork):
        unify_out = unify_evaluate(
            fork,
            log if log.exists() else None,
            rounds,
            min_chars,
            unify_fraction=10 / max(rounds, 1),  # P1 = 10 rounds
            require_forge=True,
        )
        if unify_out["decision"] != "PASS":
            reasons.append("unify_wholeness FAIL — package is not strictly more than the sum of its parts")
            reasons.extend([f"wholeness: {r}" for r in unify_out.get("reasons") or []])
            failed = unify_out.get("failed_predicates") or []
            if failed:
                reasons.append(f"failed_predicates: {failed}")

    return {
        "decision": "PASS" if not reasons else "FAIL",
        "reasons": reasons,
        "warnings": warnings,
        "fork": str(fork),
        "remix": is_remix(fork),
        "forge_validate": forge_out,
        "unify_wholeness": unify_out,
        "thresholds": {
            "rounds": rounds,
            "min_chars_per_round": min_chars,
            "phases": "P1-unify 1-10 | P2-enhance 11-20 | P3-metrics 21-44 | P4-awesome 45-50",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fork", type=Path, required=True)
    ap.add_argument("--rounds", type=int, default=FORGE_ROUNDS)
    ap.add_argument("--min-chars", type=int, default=MIN_CHARS_PER_ROUND)
    ap.add_argument("--unify-fraction", type=float, default=None, help=argparse.SUPPRESS)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    out = check(args.fork, args.rounds, args.min_chars)
    print(json.dumps(out, indent=2) if args.json else out)
    return 0 if out["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
