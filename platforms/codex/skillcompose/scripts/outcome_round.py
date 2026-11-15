#!/usr/bin/env python3
"""Outcome contract for forge rounds: a round must improve what the skill produces, not just the skill's
measurement of itself.

A forge that only checks its own package drifts. Each round finds a gap in the package's checkers,
evals or metrics, closes it, and adds an eval proving it closed, and the user's output never changes.
This gate anchors every round from OUTCOME_FROM_ROUND on in the domain output:

  forge/outcomes/rNN/task.md          the request a real user of the domain would make
  forge/outcomes/rNN/task_coords.json task-chart coordinates + desired property phi
                                      (task_space.py; see references/forge_formal_methods.md)
  forge/outcomes/rNN/before.<ext>     what the skill produced for that task at the start of the round
  forge/outcomes/rNN/after.<ext>      what it produces for the same task after the round's change
  forge/outcomes/rNN/verdict.json     {"flaw": the worst problem in before, as a reader of the domain sees it,
                                       "before_excerpt": verbatim text from before showing the flaw,
                                       "after_excerpt": verbatim text from after where it is fixed
                                         (required when verdict is "better"),
                                       "verdict": "better" | "same" | "worse",
                                       "why": what a reader would notice,
                                       "phi": desired output property name (must match task_coords.phi)}

"same" and "worse" are allowed and logged as misses; inventing "better" is not, so the excerpts must be
copied from the files. The outputs are evidence, so measure_chars.py leaves them out of a round's product
characters.

Focus: each round's changed characters are split into skill (what the skill does: SKILL.md, members,
references, scripts it runs, templates), instrumentation (evals/, tests/, metrics/, METRICS.md,
WHOLENESS.md, COMPARISON.md, gold labels, benchmarks, forge logs), and output (artifacts the skill wrote,
listed in forge/output_dirs.json, e.g. ["novel"]). A round is self-measurement when more than
SELF_MEASURE_SHARE of its skill+instrumentation characters are instrumentation. forge_log.py validate
allows at most MAX_SELF_MEASURE_FRACTION of outcome rounds to be self-measurement.

  outcome_round.py init  --fork F --round R --task "..."    scaffold forge/outcomes/rNN/
  outcome_round.py check --fork F --round R [--commit HEAD]  exit 0 PASS / 2 FAIL, JSON for forge_log
  outcome_round.py audit --fork F --log forge/usefulness_forge.jsonl   focus of every logged round
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_chars import measure  # noqa: E402

OUTCOME_FROM_ROUND = 11
SELF_MEASURE_SHARE = 0.5
MAX_SELF_MEASURE_FRACTION = 0.2
MIN_BETTER_FRACTION = 0.5
MIN_OUTPUT_CHARS = 300
MAX_SIMILARITY = 0.97
MIN_EXCERPT_CHARS = 15

INSTRUMENT_DIRS = ("evals/", "eval/", "tests/", "test/", "metrics/", "benchmarks/", "benchmark/", "forge/")
INSTRUMENT_FILES = re.compile(
    r"(^|/)(METRICS|WHOLENESS|COMPARISON|USEFULNESS_FORGE|UPGRADE_PLAN)\.md$"
    r"|(^|/)results[^/]*\.json$|(^|/)gold_[^/]*\.json$|_truth\.py$|(^|/)run_e2e\.py$|(^|/)test_[^/]*\.py$"
)


def rdir(fork: Path, rnd: int) -> Path:
    return fork / "forge" / "outcomes" / f"r{rnd:02d}"


EXTRA_OUTPUTS: list[str] = []


def output_dirs(fork: Path) -> list[str]:
    extra = [d.strip("/") + "/" for d in EXTRA_OUTPUTS if d.strip("/")]
    p = fork / "forge" / "output_dirs.json"
    try:
        dirs = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return extra
    listed = [d.strip("/") + "/" for d in dirs if isinstance(d, str) and d.strip("/")] if isinstance(dirs, list) else []
    return extra + listed


def category(path: str, outputs: list[str]) -> str:
    p = path.replace("\\", "/")
    if p.startswith("forge/outcomes/") or any(p.startswith(d) for d in outputs):
        return "output"
    if p.startswith(INSTRUMENT_DIRS) or INSTRUMENT_FILES.search(p):
        return "instrumentation"
    return "skill"


def focus(fork: Path, commit: str) -> dict:
    m = measure(fork, commit, None)
    outs = output_dirs(fork)
    split = {"skill": 0, "instrumentation": 0, "output": 0}
    for path, n in m.get("per_file", {}).items():
        split[category(path, outs)] += n
    base = split["skill"] + split["instrumentation"]
    share = round(split["instrumentation"] / base, 4) if base else 0.0
    return {"commit": commit, "chars": split, "instrumentation_share": share,
            "self_measurement": share > SELF_MEASURE_SHARE}


def _one(d: Path, stem: str) -> Path | None:
    hits = sorted(p for p in d.glob(f"{stem}.*") if p.is_file())
    return hits[0] if len(hits) == 1 else None


def evidence(fork: Path, rnd: int) -> tuple[dict, list[str]]:
    d = rdir(fork, rnd)
    errs: list[str] = []
    out: dict = {"dir": str(d.relative_to(fork))}
    task = d / "task.md"
    if not task.is_file() or len(task.read_text(encoding="utf-8").strip()) < 40:
        errs.append(f"{out['dir']}/task.md missing or under 40 chars: say what a real user asked the skill for")
    # Task-space coordinates (formal forge: expand X while improving phi)
    coords = d / "task_coords.json"
    phi_coords = ""
    if not coords.is_file():
        errs.append(
            f"{out['dir']}/task_coords.json missing: register chart coords + phi "
            "(python3 scripts/task_space.py register …)"
        )
    else:
        try:
            cd = json.loads(coords.read_text(encoding="utf-8"))
            phi_coords = str(cd.get("phi") or "").strip()
            if not isinstance(cd.get("coords"), dict) or not cd.get("coords"):
                errs.append("task_coords.coords must be a non-empty object")
            if len(phi_coords) < 3:
                errs.append("task_coords.phi must name the desired output property")
            out["task_coords"] = str(coords.relative_to(fork))
            out["phi"] = phi_coords
        except (OSError, ValueError) as e:
            errs.append(f"task_coords.json unreadable: {e}")
    texts = {}
    for stem in ("before", "after"):
        f = _one(d, stem)
        if f is None:
            errs.append(f"{out['dir']}/{stem}.<ext>: need exactly one file with the skill's output")
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        if len(t.strip()) < MIN_OUTPUT_CHARS:
            errs.append(f"{f.name} has {len(t.strip())} chars; a real output is at least {MIN_OUTPUT_CHARS}")
        texts[stem] = t
        out[stem] = str(f.relative_to(fork))
    if len(texts) == 2:
        sim = difflib.SequenceMatcher(None, texts["before"][:20000], texts["after"][:20000], autojunk=False).ratio()
        out["similarity"] = round(sim, 4)
        if sim > MAX_SIMILARITY:
            errs.append(f"before and after are {sim:.0%} alike: rerun the task with the changed skill, "
                        "the output did not change")
    try:
        v = json.loads((d / "verdict.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        errs.append(f"{out['dir']}/verdict.json unreadable: {e}")
        return out, errs
    if not isinstance(v, dict):
        return out, errs + ["verdict.json must be an object"]
    verdict = v.get("verdict")
    if verdict not in ("better", "same", "worse"):
        errs.append('verdict must be "better", "same" or "worse"')
    for k, n in (("flaw", 20), ("why", 40)):
        if not isinstance(v.get(k), str) or len(v[k].strip()) < n:
            errs.append(f"verdict.{k} must be at least {n} chars")
    want = [("before_excerpt", "before")] + ([("after_excerpt", "after")] if verdict == "better" else [])
    for k, stem in want:
        ex = v.get(k)
        if not isinstance(ex, str) or len(ex.strip()) < MIN_EXCERPT_CHARS:
            errs.append(f"verdict.{k}: quote at least {MIN_EXCERPT_CHARS} chars of {stem} that show it")
        elif stem in texts and " ".join(ex.split()) not in " ".join(texts[stem].split()):
            errs.append(f"verdict.{k} is not in {stem}: copy it verbatim from the output")
    # phi in verdict must match task_coords when both present
    vphi = v.get("phi") if isinstance(v.get("phi"), str) else ""
    if phi_coords and vphi and vphi.strip() != phi_coords:
        errs.append(f"verdict.phi {vphi!r} must match task_coords.phi {phi_coords!r}")
    if phi_coords and not vphi:
        errs.append("verdict.phi required: name the desired output property improved this round")
    out.update({k: v.get(k) for k in ("verdict", "flaw", "why", "phi") if isinstance(v.get(k), str)})
    return out, errs


def check(fork: Path, rnd: int, commit: str = "HEAD") -> dict:
    if rnd < OUTCOME_FROM_ROUND:
        return {"decision": "PASS", "round": rnd, "required": False,
                "note": f"outcome evidence starts at round {OUTCOME_FROM_ROUND}"}
    ev, errs = evidence(fork, rnd)
    fo = focus(fork, commit)
    return {"decision": "FAIL" if errs else "PASS", "round": rnd, "required": True, "outcome": ev,
            "focus": fo, "reasons": errs}


def init(fork: Path, rnd: int, task: str) -> dict:
    d = rdir(fork, rnd)
    d.mkdir(parents=True, exist_ok=True)
    (d / "task.md").write_text(task.strip() + "\n", encoding="utf-8")
    if not (d / "verdict.json").exists():
        (d / "verdict.json").write_text(json.dumps(
            {"flaw": "", "before_excerpt": "", "after_excerpt": "", "verdict": "", "why": "", "phi": ""},
            indent=2) + "\n",
            encoding="utf-8")
    next_steps = [
        "ensure forge/task_space/atlas.json exists (task_space.py init-atlas)",
        "register novel chart coords + phi: "
        f"python3 scripts/task_space.py register --fork <fork> --round {rnd} "
        "--coords '{...}' --phi <property> --task-summary '...'",
        f"run the skill on task.md as a user would; save its output as {d}/before.<ext>",
        "read it as a demanding reader of the domain; put the single worst flaw, with a verbatim quote, "
        "and matching phi in verdict.json",
        "change the skill so that flaw stops happening (procedure, member guidance, references, the scripts it runs)",
        f"rerun the same task with the changed skill; save {d}/after.<ext>; fill the verdict honestly",
    ]
    return {"dir": str(d), "next": next_steps}


def audit(fork: Path, log: Path) -> dict:
    rows = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rnd, c = int(r.get("round", 0)), r.get("commit")
        if not c:
            continue
        try:
            fo = focus(fork, c)
        except SystemExit as e:
            rows.append({"round": rnd, "error": str(e)})
            continue
        rows.append({"round": rnd, "kind": r.get("kind"), "gap": str(r.get("gap", ""))[:90],
                     "instrumentation_share": fo["instrumentation_share"], "chars": fo["chars"],
                     "self_measurement": fo["self_measurement"],
                     "outcome": bool(r.get("outcome")) or rdir(fork, rnd).is_dir()})
    scoped = [r for r in rows if r.get("round", 0) >= OUTCOME_FROM_ROUND and "error" not in r]
    selfm = [r["round"] for r in scoped if r["self_measurement"]]
    tot = {k: sum(r["chars"][k] for r in scoped) for k in ("skill", "instrumentation", "output")}
    return {"rounds": rows, "scoped_rounds": len(scoped), "self_measurement_rounds": selfm,
            "self_measurement_fraction": round(len(selfm) / len(scoped), 4) if scoped else 0.0,
            "without_outcome": [r["round"] for r in scoped if not r["outcome"]], "chars": tot,
            "decision": "PASS" if scoped and len(selfm) <= MAX_SELF_MEASURE_FRACTION * len(scoped)
            and not [r for r in scoped if not r["outcome"]] else "FAIL"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--fork", type=Path, required=True)
    i.add_argument("--round", type=int, required=True)
    i.add_argument("--task", required=True)
    c = sub.add_parser("check")
    c.add_argument("--fork", type=Path, required=True)
    c.add_argument("--round", type=int, required=True)
    c.add_argument("--commit", default="HEAD")
    a = sub.add_parser("audit")
    a.add_argument("--fork", type=Path, required=True)
    a.add_argument("--log", type=Path, required=True)
    for p in (i, c, a):
        p.add_argument("--json", action="store_true")
    for p in (c, a):
        p.add_argument("--output-dir", action="append", default=[],
                       help="artifact folder the skill wrote (adds to forge/output_dirs.json)")
    args = ap.parse_args()
    EXTRA_OUTPUTS.extend(getattr(args, "output_dir", []))
    if args.cmd == "init":
        out = init(args.fork, args.round, args.task)
    elif args.cmd == "check":
        out = check(args.fork, args.round, args.commit)
    else:
        out = audit(args.fork, args.log)
    print(json.dumps(out, indent=2))
    return 0 if out.get("decision", "PASS") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
