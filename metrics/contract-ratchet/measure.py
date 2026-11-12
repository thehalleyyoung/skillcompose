#!/usr/bin/env python3
"""Contract ratchet regression (theory.md §4.2): the hybrid contract is checked on the term a package
actually runs, and a forge round that breaks it, or raises any component of the vector Lyapunov debt,
is refused. Each case mutates a clean package in a throwaway git repo and runs concrete_term.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
TERM = SCRIPTS / "concrete_term.py"
FORGE_LOG = SCRIPTS / "forge_log.py"

PROJECTOR = '''import argparse, sys
ap = argparse.ArgumentParser()
ap.add_argument("--query", required=True)
a = ap.parse_args()
if not a.query.strip():
    sys.exit(2)
print("{}")
'''
MUTATOR = '''import argparse
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--topic", default="")
a = ap.parse_args()
d = Path(a.dir)
d.mkdir(parents=True, exist_ok=True)
(d / "chapter.md").write_text(a.topic.replace("-", " "))
'''
GATE = '''import argparse, sys
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
a = ap.parse_args()
text = " ".join(p.read_text() for p in Path(a.dir).glob("*.md"))
sys.exit(0 if text.strip() else 1)
'''
OBSERVER = '''import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
a = ap.parse_args()
print("x".replace("x", "y"))
'''
PROTOCOL = [
    'python3 scripts/project_manifold.py --query "a dragon at the ford"',
    "python3 scripts/write_chapter.py --dir drafts --topic dragon-ford",
    "python3 scripts/style_report.py --dir drafts",
    "python3 scripts/verify_dominator_gate.py --dir drafts",
]
ATLAS = {"carrier": {"drafter": [{"dest": "scripts/write_chapter.py"}]},
         "argument_interface": {"take": ["--topic"], "able": []}}


def skill(lines: list[str]) -> str:
    body = "\n".join(f"{i + 1}. `{c}`" for i, c in enumerate(lines))
    return ("# fantasy-draft\n\nTakes --topic. Run in order:\n\n" + body + "\n\n"
            + "Write scenes through concrete sensory detail; verify before done.\n" * 20)


def git(repo: Path, *a: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout


def run(*a: str) -> tuple[int, dict]:
    r = subprocess.run(["python3", *a], capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout)
    except json.JSONDecodeError:
        return r.returncode, {"stderr": r.stderr[-400:]}


def clean(repo: Path) -> None:
    files = {"SKILL.md": skill(PROTOCOL), "scripts/project_manifold.py": PROJECTOR,
             "scripts/write_chapter.py": MUTATOR, "scripts/verify_dominator_gate.py": GATE,
             "scripts/style_report.py": OBSERVER, "references/manifold_atlas.json": json.dumps(ATLAS),
             "AWESOME_PROOF.md": "# proof\nfinished novel at out/novel.md\n"}
    for rel, text in files.items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    subprocess.run(["python3", str(TERM), "write", "--package", str(repo)], capture_output=True, check=True)


def case(tmp: Path, name: str, mutate) -> tuple[int, dict]:
    repo = tmp / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    clean(repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "clean")
    if mutate:
        mutate(repo)
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", name, "--allow-empty")
    return run(str(TERM), "ratchet", "--repo", str(repo), "--base", "HEAD~1" if mutate else "HEAD",
               "--head", "HEAD", "--zero", "--require-artifact", "--json")


def rewrite(lines: list[str], refresh: bool = True):
    def m(repo: Path) -> None:
        (repo / "SKILL.md").write_text(skill(lines), encoding="utf-8")
        if refresh:
            subprocess.run(["python3", str(TERM), "write", "--package", str(repo)], capture_output=True)
    return m


def has(out: dict, prefix: str) -> bool:
    return any(str(r).startswith(prefix) or f" {prefix}" in str(r) for r in out.get("reasons", []))


def main() -> int:
    p, w, s, g = PROTOCOL
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        rc_clean, cl = case(tmp, "clean", None)
        rc_early, early = case(tmp, "write_before_projector", rewrite([w, p, s, g]))
        rc_late, late = case(tmp, "mutator_after_gate", rewrite([p, s, g, w]))
        rc_quoted, quoted = case(tmp, "quoted_write_before_projector",
                                 rewrite([w.replace("scripts/write_chapter.py", '"$SCRIPTS/write_chapter.py"'), p, s, g]))
        rc_flag, flag = case(tmp, "bad_flag", rewrite([p, w.replace("--topic", "--subject"), s, g]))

        def drop_carrier(repo: Path) -> None:
            rewrite([p, s, g])(repo)
            (repo / "scripts" / "write_chapter.py").unlink()
        rc_carrier, carrier = case(tmp, "carrier_removed", drop_carrier)

        def drop_arg(repo: Path) -> None:
            (repo / "SKILL.md").write_text(skill([p, w.replace(" --topic dragon-ford", ""), s, g])
                                           .replace("Takes --topic. ", ""), encoding="utf-8")
            subprocess.run(["python3", str(TERM), "write", "--package", str(repo)], capture_output=True)
        rc_iface, iface = case(tmp, "interface_arg_removed", drop_arg)

        def gate_writes(repo: Path) -> None:
            (repo / "scripts" / "verify_dominator_gate.py").write_text(
                GATE.replace("sys.exit(0", "Path('cache').mkdir(exist_ok=True)\nsys.exit(0"), encoding="utf-8")
            subprocess.run(["python3", str(TERM), "write", "--package", str(repo)], capture_output=True)
        rc_ro, ro = case(tmp, "gate_writes", gate_writes)

        rc_lyap, lyap = case(tmp, "lyapunov_component_rises", lambda r: (r / "AWESOME_PROOF.md").unlink())

        def stale(repo: Path) -> None:
            (repo / "scripts" / "polish.py").write_text(OBSERVER, encoding="utf-8")
            (repo / "SKILL.md").write_text(skill([p, w, s, "python3 scripts/polish.py --dir drafts", g]),
                                           encoding="utf-8")
        rc_stale, st = case(tmp, "stale_artifact", stale)

        checks = {
            "clean_package_passes": rc_clean == 0 and cl.get("phi") == 0
            and cl.get("roles", {}).get("mutator") == ["scripts/write_chapter.py"],
            "str_replace_is_not_a_write": "scripts/style_report.py" in cl.get("roles", {}).get("observer", []),
            "write_before_projector_refused": rc_early == 2 and has(early, "ΔΦ_c")
            and any("projected:" in o for o in early.get("obligations", [])),
            "quoted_invocation_is_read": rc_quoted == 2
            and any("projected:" in o for o in quoted.get("obligations", [])),
            "mutator_after_gate_refused": rc_late == 2 and any("gated:" in o for o in late.get("obligations", [])),
            "undeclared_flag_refused": rc_flag == 2 and any("signature:" in o and "--subject" in o
                                                            for o in flag.get("obligations", [])),
            "removed_carrier_refused": rc_carrier == 2 and any("carrier:" in o for o in carrier.get("obligations", [])),
            "removed_interface_arg_refused": rc_iface == 2
            and any("interface:" in o and "--topic" in o for o in iface.get("obligations", [])),
            "writing_gate_refused": rc_ro == 2 and any("gate_readonly:" in o for o in ro.get("obligations", [])),
            "lyapunov_component_rise_refused": rc_lyap == 2 and lyap.get("phi") == 0
            and has(lyap, "ΔΦ > 0") and "d5_awesome_world_proof" in " ".join(lyap.get("reasons", [])),
            "stale_artifact_refused": rc_stale == 2 and any("artifact:" in str(r) for r in st.get("reasons", [])),
        }
        rows = []
        for i in range(1, 21):
            r = {"round": i, "total": 20, "theme": "P1-unify" if i <= 10 else "P2-enhance",
                 "kind": "unify" if i <= 10 else "enhance", "unify": i <= 10, "gap": "g", "addition": "a",
                 "surfaces": ["code", "docs", "procedure"], "radical": True, "chars_changed": 1500, "commit": f"c{i}",
                 "contract": {"decision": "PASS", "phi_before": int(i > 15), "phi": int(i >= 15), "reasons": []}}
            if i >= 11:
                r["outcome"] = {"before": "b.md", "after": "a.md", "verdict": "better"}
                r["focus"] = {"self_measurement": False}
            rows.append(r)
        rows[14]["contract"].update(decision="FAIL", reasons=["ΔΦ_c = 1 > 0: this change broke projected: …"])
        log = tmp / "log.jsonl"
        log.write_text("".join(json.dumps(r) + "\n" for r in rows))
        rc_v, v = run(str(FORGE_LOG), "validate", "--log", str(log), "--rounds", "20", "--json")
        log.write_text("".join(json.dumps({k: x for k, x in r.items() if k != "contract"}) + "\n" for r in rows))
        rc_bare, bare = run(str(FORGE_LOG), "validate", "--log", str(log), "--rounds", "20", "--json")
        checks["held_regression_fails_forge"] = rc_v == 2 and v.get("contract", {}).get("rose") == [15] \
            and v.get("contract", {}).get("nonzero_after_unify") == list(range(15, 21))
        checks["contract_free_forge_fails"] = rc_bare == 2 and len(bare.get("contract", {}).get("without", [])) == 20
    ok_all = all(checks.values())
    print(json.dumps({"ok": ok_all, "checks": checks}, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
