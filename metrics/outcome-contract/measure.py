#!/usr/bin/env python3
"""Outcome contract regression: forge rounds must show the skill's output before and after, and a forge
that spends its rounds measuring itself fails validation. Runs in a throwaway git repo."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
OUTCOME = SCRIPTS / "outcome_round.py"
FORGE_LOG = SCRIPTS / "forge_log.py"
sys.path.insert(0, str(SCRIPTS))
from measure_chars import measure  # noqa: E402

BEFORE = ("The dragon was big and scary. Mira was scared of the dragon because it was big. "
          "She thought about how scary it was. The dragon roared loudly and it was very loud. ") * 4
AFTER = ("Heat came first, a dry tide that curled the reeds before anything moved. Then the hill "
         "breathed, and Mira understood the hill was a back. She did not run; running was what the "
         "ash-children had done, and their shoes still lay in a neat row by the ford. ") * 3


def git(repo: Path, *a: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout


def commit(repo: Path, files: dict[str, str], msg: str) -> str:
    for rel, text in files.items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", msg)
    return git(repo, "rev-parse", "HEAD").strip()


def run(*a: str) -> tuple[int, dict]:
    r = subprocess.run(["python3", *a], capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout)
    except json.JSONDecodeError:
        return r.returncode, {"stderr": r.stderr[-400:]}


def evidence(repo: Path, rnd: int, before: str, after: str, verdict: dict) -> None:
    d = repo / "forge" / "outcomes" / f"r{rnd:02d}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "task.md").write_text("Write the opening scene of a fantasy novel where a girl meets a dragon.\n")
    (d / "before.md").write_text(before)
    (d / "after.md").write_text(after)
    (d / "verdict.json").write_text(json.dumps(verdict))


GOOD = {"flaw": "tells the fear instead of showing it, and repeats 'scary' and 'big'",
        "before_excerpt": "She thought about how scary it was.",
        "after_excerpt": "their shoes still lay in a neat row by the ford",
        "verdict": "better", "why": "the after scene makes the reader feel the threat through concrete detail"}


def row(i: int, sha: str, self_measure: bool, better: bool = True) -> dict:
    r = {"round": i, "total": 20, "theme": f"P{'1-unify' if i <= 10 else '2-enhance'}",
         "kind": "unify" if i <= 10 else "enhance", "unify": i <= 10, "gap": "g", "addition": "a",
         "surfaces": ["code", "docs", "procedure"], "radical": True, "chars_changed": 1500, "commit": f"{sha}{i}",
         "contract": {"decision": "PASS", "phi_before": 0, "phi": 0, "reasons": []}}
    if i >= 11:
        r["outcome"] = {"before": "b.md", "after": "a.md", "verdict": "better" if better else "same"}
        r["focus"] = {"self_measurement": self_measure}
    return r


def validate(tmp: Path, rows: list[dict]) -> tuple[int, dict]:
    log = tmp / "log.jsonl"
    log.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return run(str(FORGE_LOG), "validate", "--log", str(log), "--rounds", "20", "--json")


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        repo = tmp / "fork"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "user.name", "t")
        commit(repo, {"SKILL.md": "# skill\n"}, "base")

        commit(repo, {"SKILL.md": "# skill\n" + "Show fear through the body and the scene, not by naming it.\n" * 30}, "r12 no evidence")
        rc_none, none = run(str(OUTCOME), "check", "--fork", str(repo), "--round", "12", "--json")

        evidence(repo, 12, BEFORE, BEFORE, GOOD)
        rc_same, same = run(str(OUTCOME), "check", "--fork", str(repo), "--round", "12", "--json")

        evidence(repo, 12, BEFORE, AFTER, {**GOOD, "after_excerpt": "a sentence the skill never wrote at all"})
        rc_fake, fake = run(str(OUTCOME), "check", "--fork", str(repo), "--round", "12", "--json")

        evidence(repo, 12, BEFORE, AFTER, GOOD)
        commit(repo, {}, "r12 evidence") if git(repo, "status", "--porcelain") else None
        commit(repo, {"references/craft.md": "Concrete detail over named emotion.\n" * 60}, "r12 skill change")
        rc_ok, ok = run(str(OUTCOME), "check", "--fork", str(repo), "--round", "12", "--json")
        outcomes_excluded = not any(f.startswith("forge/outcomes/") for f in measure(repo, "HEAD~1", None)["files"])

        commit(repo, {"evals/metrics/voice_truth.py": "# checker accuracy study\n" * 80,
                      "METRICS.md": "M99 checker accuracy\n" * 40, "SKILL.md": "# skill\nx\n"}, "r13 self-measure")
        evidence(repo, 13, BEFORE, AFTER, GOOD)
        rc_self, selfm = run(str(OUTCOME), "check", "--fork", str(repo), "--round", "13", "--json")

        rc_app, _ = run(str(FORGE_LOG), "append", "--log", str(tmp / "a.jsonl"), "--round", "12", "--total", "50",
                        "--theme", "P2-enhance", "--gap", "g", "--addition", "a", "--commit", "c",
                        "--compared-to", "[]", "--surfaces", '["code","docs","ux"]', "--chars-changed", "2000",
                        "--kind", "enhance", "--json")

        base = [row(i, "c", False) for i in range(1, 21)]
        rc_clean, clean = validate(tmp, base)
        drift = [row(i, "c", i in (11, 12, 13)) if i >= 11 else row(i, "c", False) for i in range(1, 21)]
        rc_drift, drifted = validate(tmp, drift)
        flat = [row(i, "c", False, better=i in (11, 12)) for i in range(1, 21)]
        rc_flat, flatted = validate(tmp, flat)
        bare = [{k: v for k, v in row(i, "c", False).items() if k not in ("outcome", "focus")} for i in range(1, 21)]
        rc_bare, bared = validate(tmp, bare)

        checks = {
            "no_evidence_refused": rc_none == 2 and any("task.md" in r for r in none.get("reasons", [])),
            "unchanged_output_refused": rc_same == 2 and any("alike" in r for r in same.get("reasons", [])),
            "invented_excerpt_refused": rc_fake == 2 and any("not in after" in r for r in fake.get("reasons", [])),
            "real_improvement_passes": rc_ok == 0 and ok.get("outcome", {}).get("verdict") == "better"
            and ok.get("focus", {}).get("self_measurement") is False,
            "outputs_not_product_chars": outcomes_excluded,
            "self_measurement_flagged": rc_self == 0 and selfm["focus"]["self_measurement"] is True
            and selfm["focus"]["instrumentation_share"] > 0.5,
            "append_without_outcome_refused": rc_app != 0,
            "clean_forge_passes": rc_clean == 0,
            "drift_forge_fails": rc_drift == 2 and any("self-measurement drift" in r for r in drifted.get("reasons", [])),
            "flat_output_fails": rc_flat == 2 and any("got better in only 2 of 10" in r for r in flatted.get("reasons", [])),
            "evidence_free_forge_fails": rc_bare == 2
            and any("without before/after output evidence" in r for r in bared.get("reasons", [])),
        }
    ok_all = all(checks.values())
    print(json.dumps({"ok": ok_all, "checks": checks}, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
