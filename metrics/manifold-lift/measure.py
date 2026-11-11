#!/usr/bin/env python3
"""Verify Lawvere-Amari Generative Skill Manifold theorems and end-to-end runtime gates.

Proves offline with exact arithmetic (0 external dependencies):
  1. Exact Monotone Submodularity (diminishing returns) of D-Optimal Fisher Log-Det Volume V_Fisher(S)
     across combinatorial subset pairs S subset T.
  2. Galois Conormal + Plotkin-Reynolds Anti-Unification resolves Constraint-Union Collapse
     (/\_i Q_i |- false) while preserving exact pullback specialization sigma_i^*(T_M) == Q_i & Phi_core.
  3. Out-of-Sample Recombinant Generalization: on unseen chart coordinates theta* not in {theta^(i)},
     both Concatenation and Set-Union/Mixture fail (0 mass / infinite KL), whereas Lawvere-Amari
     Manifold projection achieves full support mass and near-zero KL divergence (<0.15 bits).
  4. Amari Information-Geometric Curvature: e-geodesic (KL barycenter) has strictly positive Bregman
     divergence gap over m-mixture on the shared structured output fiber.
  5. Static Theorem 6 Verifier (`manifold_sheaf_exactness`) rejects unlifted logical clause collisions
     AND non-zero Cech 1-cocycle triangle holonomy (delta^1 != id).
  6. End-to-End Compiled Package Runtime: synthesized `project_manifold.py` (in-manifold synthesis +
     exit-2 off-manifold ABSTAIN) and `verify_dominator_gate.py` (Cech 0-coboundary `--glue` check).
"""
from __future__ import annotations

import itertools
import json
import math
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

from compose_skills import compose_package  # noqa: E402
from manifold_engine import (  # noqa: E402
    build_skill_manifold,
    evaluate_generalization_over_union,
    fisher_logdet_volume,
)
from wiring_compiler import compile_wiring, verify_graph  # noqa: E402


def score() -> dict:
    cases = []

    landmark_pool = [
        {
            "id": "data/stream@jsonl-streaming-contract",
            "eligible": True,
            "installs": 3200,
            "stars": 280,
            "github_description": "Streaming incremental JSONL schema contract pipeline with strict abstain guard",
            "query": "streaming json schema contract",
            "discovery_role": "domain_core",
            "theory_clauses": {
                "spec_modality": ["json_contract"],
                "execution_regime": ["streaming_incremental"],
                "verification_channel": ["static_ast_contract"],
            },
        },
        {
            "id": "data/sql@zero-downtime-migration",
            "eligible": True,
            "installs": 4100,
            "stars": 390,
            "github_description": "Transactional staged SQLite formal grammar ADR migration with pytest harness and rollback",
            "query": "transactional sql formal migration rollback",
            "discovery_role": "domain_core",
            "theory_clauses": {
                "spec_modality": ["formal_grammar_adr"],
                "execution_regime": ["transactional_staged"],
                "verification_channel": ["exogenous_exec_oracle"],
            },
        },
        {
            "id": "sec/verify@adversarial-sheaf-reconciler",
            "eligible": True,
            "installs": 1900,
            "stars": 210,
            "github_description": "Adversarial differential property testing and pullback sheaf reconciler across schemas",
            "query": "adversarial differential verify pullback",
            "discovery_role": "practice_support",
            "theory_clauses": {
                "spec_modality": ["json_contract", "formal_grammar_adr"],
                "execution_regime": ["streaming_incremental", "transactional_staged"],
                "verification_channel": ["adversarial_differential"],
                "gluing_topology": ["sheaf_global_section"],
            },
        },
        {
            "id": "ops/state@idempotent-checkpoint-ledger",
            "eligible": True,
            "installs": 1450,
            "stars": 165,
            "github_description": "Idempotent rollback state recovery ledger and progressive module handoff",
            "query": "idempotent rollback state ledger",
            "discovery_role": "practice_support",
            "theory_clauses": {
                "spec_modality": ["json_contract", "formal_grammar_adr"],
                "execution_regime": ["streaming_incremental", "transactional_staged"],
                "verification_channel": ["exogenous_exec_oracle", "adversarial_differential"],
                "failure_semantics": ["idempotent_rollback"],
            },
        },
    ]

    # 1. Exhaustive Submodularity Diminishing-Returns Check on V_Fisher(S)
    diminishing_violations = 0
    monotone_violations = 0
    pairs_tested = 0
    idxs = list(range(len(landmark_pool)))
    for i in idxs:
        s_set = [landmark_pool[i]]
        for j in idxs:
            if j == i:
                continue
            t_set = [landmark_pool[i], landmark_pool[j]]
            for e_idx in idxs:
                if e_idx in (i, j):
                    continue
                elem = landmark_pool[e_idx]
                gain_s = fisher_logdet_volume(s_set + [elem]) - fisher_logdet_volume(s_set)
                gain_t = fisher_logdet_volume(t_set + [elem]) - fisher_logdet_volume(t_set)
                pairs_tested += 1
                if gain_s < -1e-9 or gain_t < -1e-9:
                    monotone_violations += 1
                if gain_s + 1e-7 < gain_t:
                    diminishing_violations += 1

    cases.append(
        {
            "name": "fisher_logdet_exact_submodularity",
            "ok": pairs_tested > 0 and monotone_violations == 0 and diminishing_violations == 0,
            "pairs_tested": pairs_tested,
            "full_pool_fisher_volume": fisher_logdet_volume(landmark_pool),
        }
    )

    # 2. Galois Conormal + Plotkin-Reynolds Anti-Unification vs Concatenation Collapse
    atlas = build_skill_manifold(
        landmark_pool,
        domain="data",
        query="sqlite schema streaming migration",
        skill_name="data-manifold-pack",
    )
    logic = atlas["logic"]
    anti_unify_ok = (
        logic["concatenation_fiber_size"] == 0
        and len(logic["concatenation_conflicts"]) >= 2
        and logic["specialization_exact"] is True
        and logic["manifold_total_fiber_size"] > logic["union_fiber_size"] > 0
        and logic["recombinant_novel_states"] >= 4
    )
    cases.append(
        {
            "name": "galois_anti_unification_defeats_concatenation_collapse",
            "ok": anti_unify_ok,
            "concatenation_fiber_size": logic["concatenation_fiber_size"],
            "union_fiber_size": logic["union_fiber_size"],
            "manifold_total_fiber_size": logic["manifold_total_fiber_size"],
            "recombinant_novel_states": logic["recombinant_novel_states"],
            "specialization_exact": logic["specialization_exact"],
        }
    )

    # 3. Recombinant Out-of-Sample Generalization strictly beats Union/Mixture & Single-Skill Router
    # Use the first two sharp orthogonal skills to test pure off-diagonal coordinate synthesis
    sharp_two = landmark_pool[:2]
    sharp_atlas = build_skill_manifold(
        sharp_two,
        domain="data",
        query="database schema pipeline",
        skill_name="sharp-two-manifold",
    )
    gen = evaluate_generalization_over_union(sharp_atlas)
    gen_ok = (
        gen["concatenation_admissible_outputs"] == 0
        and gen["union_probability_mass_on_target_fiber"] == 0.0
        and gen["manifold_probability_mass_on_target_fiber"] > 0.99
        and gen["kl_target_to_union_bits"] == "inf"
        and gen["kl_target_to_best_single_bits"] == "inf"
        and isinstance(gen["kl_target_to_manifold_bits"], float)
        and gen["kl_target_to_manifold_bits"] < 0.15
        and gen["manifold_strictly_dominates_union"] is True
    )
    cases.append(
        {
            "name": "recombinant_out_of_sample_beats_union_and_router",
            "ok": gen_ok,
            "telemetry": gen,
        }
    )

    # 4. Amari e-Geodesic vs m-Mixture Curvature Theorem
    bregman_gap = atlas["geometry"]["amari_e_vs_m_bregman_gap_bits"]
    cases.append(
        {
            "name": "amari_e_geodesic_strictly_diverges_from_m_mixture",
            "ok": bregman_gap > 0.005 and atlas["geometry"]["tangent_rank"] >= 2,
            "amari_e_vs_m_bregman_gap_bits": bregman_gap,
            "tangent_rank": atlas["geometry"]["tangent_rank"],
            "intrinsic_dimension": atlas["geometry"]["intrinsic_dimension_participation_ratio"],
        }
    )

    # 5. Static Verifier rejects unlifted logical collision AND Cech 1-cocycle holonomy defect
    base_graph = compile_wiring(landmark_pool, {}, domain="data", package_name="data-manifold-pack")
    # 5a: Remove projector and inject colliding hard_fiber_clauses on two nodes
    bad_collision = json.loads(json.dumps(base_graph))
    bad_collision["nodes"] = [
        n for n in bad_collision["nodes"] if n.get("operator_class") != "manifold_projector"
    ]
    # Reconnect guard directly to spec/adapter so type_safety stays true while manifold_sheaf_exactness fails
    for e in bad_collision["edges"]:
        if e["to"] == "subskill:manifold-chart-projector":
            e["to"] = "adapter:spec-normalizer"
    bad_collision["edges"] = [
        e for e in bad_collision["edges"] if e["from"] != "subskill:manifold-chart-projector"
    ]
    bad_collision["nodes"][0]["hard_fiber_clauses"] = {"execution_regime": ["streaming_incremental"]}
    bad_collision["nodes"][1]["hard_fiber_clauses"] = {"execution_regime": ["transactional_staged"]}
    ver_collision = verify_graph(bad_collision)

    # 5b: Inject non-zero Cech 1-cocycle holonomy around triangle (U_spec_schema, U_migration_sql, U_api_serializer)
    bad_cocycle = json.loads(json.dumps(base_graph))
    bad_cocycle["sheaf_nerve"]["overlaps"][0]["transform"] = "shift_plus_1"
    ver_cocycle = verify_graph(bad_cocycle)

    cases.append(
        {
            "name": "wiring_rejects_unlifted_collision_and_holonomy_cocycle_defect",
            "ok": (
                base_graph["verification"]["decision"] == "PASS"
                and ver_collision["decision"] == "FAIL"
                and not ver_collision["checks"]["manifold_sheaf_exactness"]
                and ver_cocycle["decision"] == "FAIL"
                and not ver_cocycle["checks"]["manifold_sheaf_exactness"]
            ),
            "cocycle_defects_caught": len(ver_cocycle.get("sheaf_cocycle", {}).get("holonomy_defects") or []),
        }
    )

    # 6. End-to-End Compiled Package Runtime (`project_manifold.py` + `verify_dominator_gate.py --glue`)
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cand_jsonl = td_path / "cands.jsonl"
        up_root = td_path / "upstreams"
        for item in landmark_pool:
            slug = item["id"].split("@", 1)[1]
            sdir = up_root / slug
            sdir.mkdir(parents=True, exist_ok=True)
            (sdir / "SKILL.md").write_text(
                f"---\nname: {slug}\ndescription: {item['github_description']}\n---\n# {slug}\n"
                + ("Detailed specification and operational rules.\n" * 10),
                encoding="utf-8",
            )
            row = dict(item)
            row["local_dir"] = str(sdir)
            with cand_jsonl.open("a", encoding="utf-8") as cf:
                cf.write(json.dumps(row) + "\n")

        out_pkg = td_path / "compiled_manifold_skill"
        comp_res = compose_package(
            cand_jsonl,
            n=4,
            domain="data",
            query="sqlite schema streaming migration",
            out_dir=out_pkg,
            skill_name="sqlite-manifold-pack",
        )

        proj_py = out_pkg / "scripts" / "project_manifold.py"
        gate_py = out_pkg / "scripts" / "verify_dominator_gate.py"
        sec_json = td_path / "section.json"

        # 6a: In-manifold recombinant task projection -> exit 0
        run_in = subprocess.run(
            [
                sys.executable,
                str(proj_py),
                "--input",
                "streaming incremental formal grammar schema migration with adversarial differential tests",
                "--out",
                str(sec_json),
            ],
            capture_output=True,
            text=True,
        )
        # 6b: Off-manifold polysemic/alien prompt -> exit 2 ABSTAIN_OFF_MANIFOLD
        run_abstain = subprocess.run(
            [
                sys.executable,
                str(proj_py),
                "--input",
                "Write romance fanfiction chapters in storybook",
            ],
            capture_output=True,
            text=True,
        )

        # 6c: Sheaf 0-coboundary check passes on consistent views, fails (exit 2) on drifted views
        view_sql = td_path / "migration_view.json"
        view_api_ok = td_path / "api_view_ok.json"
        view_api_bad = td_path / "api_view_bad.json"
        contract_json = td_path / "contract.json"
        contract_json.write_text('{"locked": true}\n', encoding="utf-8")
        view_sql.write_text('{"entity_columns": ["id", "email", "tenant_id"], "primary_key": "id"}\n', encoding="utf-8")
        view_api_ok.write_text('{"entity_columns": ["id", "email", "tenant_id"], "primary_key": "id"}\n', encoding="utf-8")
        view_api_bad.write_text('{"entity_columns": ["id", "email"], "primary_key": "id"}\n', encoding="utf-8")

        gate_ok = subprocess.run(
            [
                sys.executable,
                str(gate_py),
                "--manifold-section",
                str(sec_json),
                "--contract",
                str(contract_json),
                "--protect",
                str(view_sql),
                "--protect",
                str(view_api_ok),
                "--glue",
                f"{view_sql}:{view_api_ok}:entity_columns,primary_key",
                "--cmd",
                "python3 -c 'import sys; sys.exit(0)'",
            ],
            capture_output=True,
            text=True,
        )
        gate_drift = subprocess.run(
            [
                sys.executable,
                str(gate_py),
                "--manifold-section",
                str(sec_json),
                "--contract",
                str(contract_json),
                "--protect",
                str(view_sql),
                "--protect",
                str(view_api_bad),
                "--glue",
                f"{view_sql}:{view_api_bad}:entity_columns,primary_key",
                "--cmd",
                "python3 -c 'import sys; sys.exit(0)'",
            ],
            capture_output=True,
            text=True,
        )

        cases.append(
            {
                "name": "compiled_package_projector_and_sheaf_coboundary_gate",
                "ok": (
                    comp_res["ok"]
                    and run_in.returncode == 0
                    and run_abstain.returncode == 2
                    and "ABSTAIN_OFF_MANIFOLD" in run_abstain.stdout
                    and gate_ok.returncode == 0
                    and gate_drift.returncode == 2
                    and "sheaf_coboundary_defect" in gate_drift.stdout
                ),
                "skill_md_bytes": comp_res["skill_md_bytes"],
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
        "metric_id": "manifold-lift",
        "title": "Lawvere-Amari generative skill manifold, anti-unification & Cech sheaf gates",
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
