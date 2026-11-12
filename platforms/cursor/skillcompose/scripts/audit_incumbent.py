#!/usr/bin/env python3
"""Audit an incumbent skill directory and lock the 50-round forge phase plan."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def audit(skill_dir: Path) -> dict:
    skill_md = skill_dir / "SKILL.md"
    body = read(skill_md)
    scripts = list(skill_dir.glob("scripts/**/*")) if (skill_dir / "scripts").exists() else []
    scripts = [p for p in scripts if p.is_file()]
    refs = list((skill_dir / "references").rglob("*")) if (skill_dir / "references").exists() else []
    refs = [p for p in refs if p.is_file()]
    evals = []
    for pat in ("evals/evals.json", "evals.json", "eval/evals.json"):
        p = skill_dir / pat
        if p.exists():
            evals.append(p)
    install = (skill_dir / "install.sh").exists() or (skill_dir.parent / "install.sh").exists()
    readme = read(skill_dir / "README.md") or read(skill_dir.parent / "README.md")

    gaps = []

    def gap(gid: str, title: str, detail: str, severity: str = "high"):
        gaps.append({"id": gid, "title": title, "detail": detail, "severity": severity})

    if not skill_md.exists():
        gap("missing-skill-md", "Missing SKILL.md", "Not a portable agent skill", "critical")
        return {"gaps": gaps, "stats": {}}

    if not scripts:
        gap(
            "no-scripts",
            "No deterministic scripts/",
            "Incumbent is prompt-only; add scripts for verify/score/smoke so agents don't self-grade.",
        )
    if not evals:
        gap(
            "no-evals",
            "No evals/ harness",
            "Add ≥3 with/without cases so upgrades are measurable.",
        )
    if not re.search(r"(?i)verif|independent|do not grade your own|false.?done", body):
        gap(
            "no-verify-step",
            "No independent verification step",
            "Procedure never requires a fresh check before claiming done.",
        )
    if not re.search(r"(?i)when not to use|do not use|non-trigger", body):
        gap(
            "no-nontriggers",
            "Missing when-not-to-use / non-triggers",
            "Skill will over-trigger; add explicit non-triggers.",
            "medium",
        )
    if "install.sh" not in readme and not install:
        gap(
            "weak-install",
            "No multi-host install path",
            "Add install.sh that copies to ~/.gemini/config/skills, ~/.claude/skills, ~/.cursor/skills, and ~/.codex/skills.",
        )
    if not re.search(r"```(?:text|bash|shell)?\n\s*/[\w-]+", readme + body):
        gap(
            "no-slash-example",
            "No fenced slash-invocation example",
            "README/SKILL lack `/skill-name <args>` example — hurts first-run success.",
            "medium",
        )
    if not refs and len(body.splitlines()) > 200:
        gap(
            "no-progressive-disclosure",
            "Monolithic SKILL without references/",
            "Split deep material into references/ for progressive disclosure.",
            "medium",
        )
    if not re.search(r"(?i)metric|success_rate|eval|measure", body + readme):
        gap(
            "no-metrics",
            "No usefulness metrics story",
            "Define at least one measurable metric and how scripts compute it.",
        )
    if not re.search(r"(?i)fail|error|recover|resume|checkpoint", body):
        gap(
            "no-failure-recovery",
            "No failure/resume protocol",
            "Add checkpoint + resume so long chores don't restart from zero.",
            "medium",
        )
    if re.search(r"(?i)TODO|coming soon|placeholder", body):
        gap(
            "placeholders",
            "Placeholder / TODO residue",
            "Replace TODOs with runnable procedure or delete dead sections.",
            "medium",
        )

    # Suggest competitive / UX depth only when not already addressed in docs
    if len(gaps) < 3:
        blob = body + "\n" + readme
        if not re.search(
            r"(?i)neighbor|comparison\.md|wholeness\.md|marketplace alternative",
            blob,
        ):
            gap(
                "shallow-vs-neighbors",
                "Shallow vs marketplace neighbors",
                "Benchmark against 2 neighbors; add a capability the incumbent verifiably lacks.",
            )
        if not re.search(
            r"(?i)operator ux|--smoke|status --wip|resume_forge|exit \*\*2\*\*|slash-args",
            blob,
        ):
            gap(
                "operator-ux",
                "Operator UX gaps",
                "Add --smoke defaults, richer slash-args, clearer error messages.",
                "medium",
            )

    stats = {
        "skill_md_lines": len(body.splitlines()),
        "n_scripts": len(scripts),
        "n_references": len(refs),
        "n_evals_files": len(evals),
        "has_install": install,
        "has_readme_slash": bool(re.search(r"```(?:text|bash|shell)?\n\s*/[\w-]+", readme)),
    }
    return {"gaps": gaps, "stats": stats, "skill_dir": str(skill_dir)}


def propose_phases(gaps: list[dict]) -> list[dict]:
    """Lock the fixed 50-round phase plan (replaces T1–T5)."""
    from forge_phases import phases_doc

    return phases_doc(gaps)["phases"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skill-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, help="Write full audit JSON")
    ap.add_argument(
        "--themes-out",
        type=Path,
        help="Write forge_phases.json (legacy flag name --themes-out)",
    )
    ap.add_argument("--phases-out", type=Path, help="Write forge_phases.json")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = audit(args.skill_dir)
    phases = propose_phases(result["gaps"])
    result["proposed_phases"] = phases
    result["proposed_themes"] = phases  # backward-compat for older callers/smoke

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    phases_path = args.phases_out or args.themes_out
    if phases_path:
        from forge_phases import phases_doc

        doc = phases_doc(result["gaps"])
        phases_path.parent.mkdir(parents=True, exist_ok=True)
        phases_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2) if args.json else result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())