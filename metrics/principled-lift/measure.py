#!/usr/bin/env python3
"""Measure principled v2 lift over naive Popularity-Top-N ('best of GitHub') and adversarial traps.

Tests:
  1. Submodular coverage + JSD anti-redundancy beats Popularity-Top-N on a realistic pool crowded
     with redundant entry-stage skills + polysemic traps (`plaid`, `storybook`).
  2. Wiring compiler statically proves `type_safety`, `separation_logic`, `dpi_exogenous_grounding`,
     and `dominator_orthogonality` on compiled graphs.
  3. Wiring compiler statically REJECTS a graph where a mutator bypasses the read-only gate to DONE.
  4. Wiring compiler statically REJECTS a parallel tensor with write-write separation-logic conflict.
  5. Information-gain MDL anti-padding catches repetitive boilerplate while passing real code+schema commits.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_ROOT = ROOT.parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from submodular_select import compare_vs_github_top  # noqa: E402
from wiring_compiler import compile_wiring, verify_graph  # noqa: E402
from information_gain import commit_mdl_novelty  # noqa: E402


def score() -> dict:
    cases = []

    # 1. Submodular vs Popularity-Top-N on realistic crowded marketplace pool
    pool = [
        {
            "id": "mega1/prompts@idea-brainstormer",
            "installs": 180000,
            "stars": 8500,
            "github_description": "Brainstorm creative software ideas and generate feature lists",
            "query": "software ideation",
            "discovery_role": "domain_core",
        },
        {
            "id": "mega2/prompts@product-brainstorming",
            "installs": 150000,
            "stars": 7200,
            "github_description": "Generate product ideas and brainstorm startup features",
            "query": "software ideation",
            "discovery_role": "domain_core",
        },
        {
            "id": "mega3/prompts@ce-brainstorm",
            "installs": 120000,
            "stars": 6100,
            "github_description": "Interactive brainstorming prompt for software feature ideation",
            "query": "software ideation",
            "discovery_role": "domain_core",
        },
        {
            "id": "fintech/payments@plaid",
            "installs": 95000,
            "stars": 5400,
            "github_description": "Integrate Plaid banking and ACH payment link APIs",
            "query": "plan",
            "discovery_role": "domain_core",
        },
        {
            "id": "ui/kit@storybook-stories",
            "installs": 90000,
            "stars": 4900,
            "github_description": "Write React Native Storybook UI component stories",
            "query": "user story",
            "discovery_role": "domain_core",
        },
        {
            "id": "arch/specs@rfc-spec-contracts",
            "installs": 2400,
            "stars": 210,
            "github_description": "Elicit formal RFC specification preconditions, invariants, and architecture ADR contracts",
            "query": "spec contract",
            "discovery_role": "domain_core",
        },
        {
            "id": "quality/evals@property-test-harness",
            "installs": 1800,
            "stars": 190,
            "github_description": "Execute reproducible pytest property tests and benchmark evaluation harnesses",
            "query": "eval harness",
            "discovery_role": "practice_support",
        },
        {
            "id": "sec/review@adversarial-false-done-gate",
            "installs": 1100,
            "stars": 140,
            "github_description": "Adversarial critique and independent false-done verification gate for code and specs",
            "query": "false done verification",
            "discovery_role": "practice_support",
        },
        {
            "id": "ops/state@checkpoint-rollback-ledger",
            "installs": 650,
            "stars": 85,
            "github_description": "Idempotent migration rollback, state continuity bridge, and git checkpoint recovery",
            "query": "checkpoint resume",
            "discovery_role": "practice_support",
        },
    ]

    comp = compare_vs_github_top(pool, 4, domain="automation", query="software spec implementation")
    p_ids = set(comp["principled_ids"])
    lift = comp["lift"]
    no_traps = "fintech/payments@plaid" not in p_ids and "ui/kit@storybook-stories" not in p_ids
    beats_github = (
        lift["objective_delta"] > 1.0
        and lift["coverage_delta"] > 0.20
        and lift["redundancy_reduction"] > 0.10
        and no_traps
    )
    cases.append(
        {
            "name": "submodular_beats_github_top_n",
            "ok": beats_github,
            "principled_ids": comp["principled_ids"],
            "github_top_ids": comp["github_top_ids"],
            "lift": lift,
        }
    )

    # 2. Algebraic wiring compile & static verification PASS
    graph = compile_wiring(comp["chosen"], {}, domain="automation", package_name="spec-factory-remix")
    v_ok = graph["verification"]["decision"] == "PASS"
    cases.append(
        {
            "name": "wiring_compiler_sound",
            "ok": v_ok,
            "checks": graph["verification"]["checks"],
        }
    )

    # 3. Static verifier catches mutator bypassing read-only gate to DONE
    bad_dom = json.loads(json.dumps(graph))
    mut_id = next(n["id"] for n in bad_dom["nodes"] if n["operator_class"] == "mutator")
    bad_dom["edges"].append({"from": mut_id, "to": "DONE", "op": "unverified_shortcut"})
    v_bad_dom = verify_graph(bad_dom)
    cases.append(
        {
            "name": "reject_gate_bypass_shortcut",
            "ok": v_bad_dom["decision"] == "FAIL" and not v_bad_dom["checks"]["dominator_orthogonality"],
        }
    )

    # 4. Static verifier catches separation-logic write race in parallel tensor
    bad_sep = json.loads(json.dumps(graph))
    t_members = bad_sep["parallel_groups"][0]["members"]
    for n in bad_sep["nodes"]:
        if n["id"] in t_members[:2]:
            n["writes"] = ["shared/mutable_file.py"]
    v_bad_sep = verify_graph(bad_sep)
    cases.append(
        {
            "name": "reject_parallel_write_race",
            "ok": v_bad_sep["decision"] == "FAIL" and not v_bad_sep["checks"]["separation_logic"],
        }
    )

    # 5. MDL / Lempel-Ziv anti-padding catches repetitive spam vs genuine commit
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.io"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
        (repo / "SKILL.md").write_text("# Base skill\nInitial contract.\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)

        # Commit A: 1500 chars of repetitive Goodhart padding
        (repo / "PADDING.md").write_text("This round improves quality significantly.\n" * 45, encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "pad"], check=True, capture_output=True)
        mdl_pad = commit_mdl_novelty(repo, "HEAD")

        # Commit B: Genuine schema + executable Python check
        (repo / "verify_schema.py").write_text(
            "import json, sys\n"
            "REQUIRED = {'preconditions', 'postconditions', 'invariants', 'rollback_sql'}\n"
            "def validate_packet(path: str) -> dict:\n"
            "    doc = json.load(open(path, encoding='utf-8'))\n"
            "    missing = sorted(REQUIRED - set(doc.keys()))\n"
            "    if missing:\n"
            "        return {'decision': 'FAIL', 'missing': missing, 'code': 2}\n"
            "    return {'decision': 'PASS', 'n_invariants': len(doc['invariants'])}\n"
            "if __name__ == '__main__':\n"
            "    res = validate_packet(sys.argv[1])\n"
            "    sys.exit(0 if res['decision'] == 'PASS' else 2)\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "real"], check=True, capture_output=True)
        mdl_real = commit_mdl_novelty(repo, "HEAD")

        cases.append(
            {
                "name": "mdl_catches_padding_passes_code",
                "ok": (not mdl_pad["anti_padding_pass"]) and mdl_real["anti_padding_pass"],
                "pad_density": mdl_pad["info_density"],
                "real_density": mdl_real["info_density"],
            }
        )

        # 6. Mechanical compose_skills + auto-generated verify_dominator_gate enforces W(gate) == empty
        from compose_skills import compose_package

        cand_jsonl = Path(td) / "cands.jsonl"
        up_root = Path(td) / "upstreams"
        for p_item in pool:
            p_copy = dict(p_item)
            p_copy["eligible"] = True
            slug = p_copy["id"].split("@", 1)[1]
            sdir = up_root / slug
            sdir.mkdir(parents=True, exist_ok=True)
            (sdir / "SKILL.md").write_text(
                f"---\nname: {slug}\ndescription: {p_copy['github_description']}\n---\n# {slug}\n"
                + ("Detailed specification reference.\n" * 12),
                encoding="utf-8",
            )
            p_copy["local_dir"] = str(sdir)
            with cand_jsonl.open("a", encoding="utf-8") as cf:
                cf.write(json.dumps(p_copy) + "\n")

        out_pkg = Path(td) / "composed_pkg"
        comp_res = compose_package(
            cand_jsonl,
            n=4,
            domain="automation",
            query="software spec implementation",
            out_dir=out_pkg,
            skill_name="composed-pack",
        )
        gate_py = out_pkg / "scripts" / "verify_dominator_gate.py"
        target_art = Path(td) / "deliverable.txt"
        target_art.write_text("immutable_payload_v1\n", encoding="utf-8")
        contract_file = Path(td) / "contract.json"
        contract_file.write_text('{"invariants": ["v1"]}\n', encoding="utf-8")

        clean_run = subprocess.run(
            [
                sys.executable,
                str(gate_py),
                "--contract",
                str(contract_file),
                "--protect",
                str(target_art),
                "--cmd",
                "python3 -c 'import sys; sys.exit(0)'",
            ],
            capture_output=True,
            text=True,
        )
        mutating_critic_run = subprocess.run(
            [
                sys.executable,
                str(gate_py),
                "--contract",
                str(contract_file),
                "--protect",
                str(target_art),
                "--cmd",
                f"python3 -c \"open({str(target_art)!r}, 'a').write('tamper')\"",
            ],
            capture_output=True,
            text=True,
        )
        cases.append(
            {
                "name": "compose_and_dominator_gate_enforces_separation_logic",
                "ok": (
                    comp_res["ok"]
                    and clean_run.returncode == 0
                    and mutating_critic_run.returncode == 2
                    and "separation_logic_violation_critic_mutated_targets" in mutating_critic_run.stdout
                ),
                "nemhauser_wolsey_ratio": comp_res["nemhauser_wolsey_certificate"]["optimality_ratio_lower_bound"],
                "parnas_ratio": comp_res["verification"]["parnas"]["encapsulation_ratio"],
            }
        )

    passed = sum(1 for c in cases if c["ok"])
    total = len(cases)
    return {
        "skill_root": str(SKILL_ROOT),
        "cases": cases,
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total, 4) if total else 0.0,
    }


def main() -> None:
    values = score()
    sample = {
        "metric_id": "principled-lift",
        "title": "Principled submodular + Kleisli wiring + MDL gates",
        "at": datetime.now(tz=timezone.utc).isoformat(),
        "ts": time.time(),
        "values": values,
    }
    with (ROOT / "history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    (ROOT / "latest.json").write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    ok = values["pass_rate"] >= 1.0
    print(json.dumps({"ok": ok, "latest": str(ROOT / "latest.json"), "values": values}, indent=2))
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
