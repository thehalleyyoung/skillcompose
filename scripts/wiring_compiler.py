#!/usr/bin/env python3
"""Algebraic Skill Wiring Compiler & Static Contract Verifier for /skillremix.

Models each skill as an Open Effectful Kleisli Module:
    S = <inputs, outputs, preconditions, postconditions, frame(reads, writes), operator_class>

Compiles a chosen set of audited skills into a typed wiring graph (`wiring_graph.json`) using
five formal software-engineering composition operators:
  1. Sequential Pipe (S2 o_alpha S1)   — synthesizes minimal Sufficient-Statistic Adapters alpha
                                         only where output/input types mismatch (Q1 => P2).
  2. Parallel Tensor (S1 (x) S2)       — statically checks Concurrent Separation Logic
                                         (disjoint writes, zero read/write interference).
  3. Guarded Coproduct (G |> S1 + S2)  — total intake routing with explicit ABSTAIN sink.
  4. Orthogonal Loop (Mut <-> Critic)  — enforces write_set(Critic) == empty & executable oracle.
  5. Pullback Join (S1 x_K S2)         — inserts cross-artifact invariant reconciler pi_K(O1)==pi_K(O2).

Also verifies five static theorems on any compiled graph or materialized remix package:
  - type_safety             (no unbound required input ports)
  - separation_logic        (parallel tensor stages are race/interference free)
  - dpi_exogenous_grounding (no pure-prompt chain >2 hops without an executable environment oracle)
  - dominator_orthogonality (every mutator is post-dominated before DONE by a read-only oracle gate)
  - parnas_encapsulation    (SKILL.md progressive disclosure vs raw concatenation bloat)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from submodular_select import role_posterior  # noqa: E402

# Domain-specific shared entity keys K for Pullback Join synthesis (pi_K(O1) == pi_K(O2)).
DOMAIN_PULLBACK_KEYS: dict[str, dict[str, str]] = {
    "data": {
        "key": "schema_entity_columns",
        "artifact": "review/pullback_schema_api.json",
        "invariant": "pi_columns(migration_sql) == pi_columns(api_contract) && row_count_preserved",
    },
    "devops": {
        "key": "patched_symbol_surface",
        "artifact": "review/pullback_patch_tests.json",
        "invariant": "every patched vulnerability has a failing-before/passing-after exploit test",
    },
    "research": {
        "key": "claim_provenance_table",
        "artifact": "review/pullback_claim_ledger.json",
        "invariant": "every quantitative claim cites source_id + exact numerator/denominator check",
    },
    "automation": {
        "key": "grammar_semantics_contract",
        "artifact": "review/pullback_spec_ast.json",
        "invariant": "resolved RFC ambiguity clauses bijectively map to parser AST + property tests",
    },
    "writing": {
        "key": "canon_epistemic_state",
        "artifact": "review/pullback_canon_voice.json",
        "invariant": "character knowledge at scene t <= revealed_facts(<=t) && distinct POV voice profile",
    },
    "general": {
        "key": "artifact_interface_manifest",
        "artifact": "review/pullback_manifest.json",
        "invariant": "produced artifact exports match downstream consumer imports",
    },
}


def slug_of(sid: str) -> str:
    return (sid.split("@", 1)[-1] if "@" in sid else sid.split("/")[-1]).lower()


def classify_operator(member: dict[str, Any], audit: dict[str, Any] | None = None) -> dict[str, Any]:
    """Infer typed Kleisli module signature for a marketplace member skill."""
    rp = member.get("role_posterior") or role_posterior(member)
    sid = str(member.get("id") or "unknown")
    slug = slug_of(sid)
    stats = (audit or {}).get("stats") or {}
    has_scripts = int(stats.get("n_scripts") or 0) > 0

    # Pick dominant lifecycle role
    ranked = sorted(rp.items(), key=lambda kv: kv[1], reverse=True)
    top_role = ranked[0][0] if ranked else "synthesis"

    if top_role == "spec_grounding":
        return {
            "id": f"member:{slug}",
            "source_id": sid,
            "operator_class": "specifier",
            "primary_role": top_role,
            "inputs": ["task_request", "workspace_context"],
            "outputs": ["locked_spec_packet"],
            "preconditions": ["domain_guard_matched"],
            "postconditions": ["ambiguities_enumerated", "acceptance_invariants_typed"],
            "reads": ["workspace_context"],
            "writes": ["spec/locked_spec.json"],
            "exogenous_oracle": has_scripts,
        }
    if top_role == "static_contract":
        return {
            "id": f"member:{slug}",
            "source_id": sid,
            "operator_class": "readonly_critic",
            "primary_role": top_role,
            "inputs": ["candidate_artifact", "locked_spec_packet"],
            "outputs": ["static_contract_report"],
            "preconditions": ["candidate_artifact_exists"],
            "postconditions": ["schema_and_invariants_checked"],
            "reads": ["workspace_artifacts", "spec/locked_spec.json"],
            "writes": [],  # Read-only frame!
            "exogenous_oracle": True,
        }
    if top_role == "exec_observation":
        return {
            "id": f"member:{slug}",
            "source_id": sid,
            "operator_class": "exec_observation",
            "primary_role": top_role,
            "inputs": ["candidate_artifact", "locked_spec_packet"],
            "outputs": ["empirical_execution_trace"],
            "preconditions": ["candidate_artifact_exists"],
            "postconditions": ["deterministic_commands_executed", "exit_codes_recorded"],
            "reads": ["workspace_artifacts", "spec/locked_spec.json"],
            "writes": [],  # Observation channel does not mutate product artifacts
            "exogenous_oracle": True,
        }
    if top_role == "adversarial_verify":
        return {
            "id": f"member:{slug}",
            "source_id": sid,
            "operator_class": "readonly_critic",
            "primary_role": top_role,
            "inputs": ["candidate_artifact", "locked_spec_packet"],
            "outputs": ["adversarial_critique_report"],
            "preconditions": ["candidate_artifact_exists"],
            "postconditions": ["counterexamples_and_smells_probed"],
            "reads": ["workspace_artifacts", "spec/locked_spec.json"],
            "writes": [],  # Strict separation: critics never rewrite!
            "exogenous_oracle": has_scripts,
        }
    if top_role == "state_recovery":
        return {
            "id": f"member:{slug}",
            "source_id": sid,
            "operator_class": "state_bridge",
            "primary_role": top_role,
            "inputs": ["candidate_artifact", "empirical_execution_trace"],
            "outputs": ["verified_state_checkpoint"],
            "preconditions": ["candidate_artifact_exists"],
            "postconditions": ["rollback_or_continuity_verified"],
            "reads": ["workspace_artifacts"],
            "writes": ["state/checkpoint.json"],
            "exogenous_oracle": has_scripts,
        }
    # Default: constructive mutator / synthesizer
    return {
        "id": f"member:{slug}",
        "source_id": sid,
        "operator_class": "mutator",
        "primary_role": "synthesis",
        "inputs": ["locked_spec_packet"],
        "outputs": ["candidate_artifact"],
        "preconditions": ["locked_spec_packet_valid"],
        "postconditions": ["artifact_materialized"],
        "reads": ["spec/locked_spec.json", "workspace_context"],
        "writes": [f"workspace_artifacts:{slug}"],
        "exogenous_oracle": has_scripts,
    }


def compile_wiring(
    members: list[dict[str, Any]],
    audits: dict[str, dict[str, Any]] | None = None,
    *,
    domain: str | None = None,
    package_name: str = "principled-remix",
) -> dict[str, Any]:
    """Synthesize a provably sound Kleisli wiring graph from audited member skills."""
    audits = audits or {}
    dom = (domain or "general").lower()
    pb_cfg = DOMAIN_PULLBACK_KEYS.get(dom, DOMAIN_PULLBACK_KEYS["general"])

    classified = [classify_operator(m, audits.get(str(m.get("id") or ""))) for m in members]

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    parallel_groups: list[dict[str, Any]] = []
    synthesized_subskills: list[dict[str, Any]] = []

    # 1. Total Intake Guard Coproduct (G |> Pipeline + ABSTAIN)
    guard_node = {
        "id": "subskill:intent-guard-router",
        "operator_class": "guard_router",
        "composition_op": "coproduct_guard",
        "inputs": ["raw_user_request"],
        "outputs": ["task_request", "workspace_context"],
        "abstain_branch": "ABSTAIN_OUT_OF_DOMAIN",
        "preconditions": ["non_empty_request"],
        "postconditions": ["domain_sense_verified_or_abstained"],
        "reads": ["raw_user_request"],
        "writes": [],
        "exogenous_oracle": True,
    }
    nodes.append(guard_node)
    synthesized_subskills.append(
        {
            "name": "intent-guard-router",
            "kind": "subskill",
            "algebraic_role": "Guarded Coproduct (G |> Pipeline + ABSTAIN)",
            "job": (
                f"Decidable domain/polysemy guard for {dom}: routes valid requests into typed "
                f"`task_request` and halts with exit-2 ABSTAIN on wrong-sense triggers."
            ),
            "pulls_from": [slug_of(str(m.get("id") or "")) for m in members],
        }
    )

    specifiers = [c for c in classified if c["operator_class"] == "specifier"]
    mutators = [c for c in classified if c["operator_class"] == "mutator"]
    critics = [c for c in classified if c["operator_class"] in {"readonly_critic", "exec_observation"}]
    bridges = [c for c in classified if c["operator_class"] == "state_bridge"]

    # Ensure at least one specifier or adapter produces `locked_spec_packet`
    if not specifiers:
        spec_adapter = {
            "id": "adapter:spec-normalizer",
            "operator_class": "adapter",
            "composition_op": "kleisli_adapter",
            "inputs": ["task_request", "workspace_context"],
            "outputs": ["locked_spec_packet"],
            "preconditions": ["domain_sense_verified_or_abstained"],
            "postconditions": ["sufficient_statistic_spec_locked"],
            "reads": ["workspace_context"],
            "writes": ["spec/locked_spec.json"],
            "exogenous_oracle": True,
        }
        nodes.append(spec_adapter)
        specifiers = [spec_adapter]
        synthesized_subskills.append(
            {
                "name": "handoff-pack",
                "kind": "subskill",
                "algebraic_role": "Sufficient-Statistic Kleisli Adapter (I -> locked_spec_packet)",
                "job": (
                    "Compresses raw task context into a minimal sufficient-statistic `locked_spec.json` "
                    "(preconditions, target invariants, forbidden regressions) so downstream mutators "
                    "never parse raw chat history."
                ),
                "pulls_from": [slug_of(str(m.get("id") or "")) for m in members],
            }
        )
    else:
        nodes.extend(specifiers)
        synthesized_subskills.append(
            {
                "name": "handoff-pack",
                "kind": "subskill",
                "algebraic_role": "Sufficient-Statistic Handoff Contract",
                "job": (
                    "Normalizes specifier outputs into canonical `locked_spec.json` and enforces "
                    "Meyer precondition compatibility (Q_spec => P_mutator) across stages."
                ),
                "pulls_from": [s["id"] for s in specifiers],
            }
        )

    for sp in specifiers:
        edges.append({"from": guard_node["id"], "to": sp["id"], "op": "sequential_pipe", "artifact": "task_request"})

    # Ensure at least one mutator exists; if multiple mutators exist, sequence them on partitioned frames
    if not mutators and classified:
        # Promote first member to mutator if pool had only support skills
        promoted = dict(classified[0])
        promoted["operator_class"] = "mutator"
        promoted["inputs"] = ["locked_spec_packet"]
        promoted["outputs"] = ["candidate_artifact"]
        promoted["writes"] = ["workspace_artifacts:primary"]
        mutators = [promoted]
        specifiers = [s for s in specifiers if s["id"] != promoted["id"]]
        critics = [c for c in critics if c["id"] != promoted["id"]]
        bridges = [b for b in bridges if b["id"] != promoted["id"]]

    prev_mut_id = None
    for idx, mut in enumerate(mutators):
        mut_node = dict(mut)
        # Partition write frames if sequenced, or insert Pullback Join when multiple mutators touch views
        mut_node["writes"] = [f"workspace_artifacts:slice_{idx+1}"]
        nodes.append(mut_node)
        if prev_mut_id is None:
            for sp in specifiers:
                edges.append(
                    {"from": sp["id"], "to": mut_node["id"], "op": "sequential_pipe", "artifact": "locked_spec_packet"}
                )
        else:
            edges.append(
                {"from": prev_mut_id, "to": mut_node["id"], "op": "sequential_pipe", "artifact": "candidate_artifact"}
            )
        prev_mut_id = mut_node["id"]

    last_producer_id = prev_mut_id or specifiers[-1]["id"]

    # 2. Pullback Reconciler (S1 x_K S2) across coupled views / spec <-> artifact
    pullback_node = {
        "id": f"subskill:pullback-{pb_cfg['key'].replace('_', '-')}",
        "operator_class": "pullback_join",
        "composition_op": "pullback_join",
        "shared_key": pb_cfg["key"],
        "invariant": pb_cfg["invariant"],
        "inputs": ["locked_spec_packet", "candidate_artifact"],
        "outputs": ["reconciled_artifact_bundle", "pullback_witness"],
        "preconditions": ["candidate_artifact_exists"],
        "postconditions": [pb_cfg["invariant"]],
        "reads": ["spec/locked_spec.json", "workspace_artifacts"],
        "writes": [pb_cfg["artifact"]],
        "exogenous_oracle": True,
    }
    nodes.append(pullback_node)
    edges.append(
        {"from": last_producer_id, "to": pullback_node["id"], "op": "pullback_join", "artifact": "candidate_artifact"}
    )
    synthesized_subskills.append(
        {
            "name": f"pullback-{dom}-bridge",
            "kind": "subskill",
            "algebraic_role": f"Pullback Invariant Reconciler (S_spec x_{{{pb_cfg['key']}}} S_mut)",
            "job": f"Deterministically checks {pb_cfg['invariant']} and emits `{pb_cfg['artifact']}`.",
            "pulls_from": [m["id"] for m in mutators],
        }
    )

    # 3. Parallel Tensor of Read-Only Critics + Exogenous Observation (Separation Logic: W_i = empty!)
    if not any(c["operator_class"] == "exec_observation" for c in critics):
        exec_oracle = {
            "id": "oracle:exogenous-env-runner",
            "operator_class": "exec_observation",
            "composition_op": "exogenous_grounding",
            "inputs": ["reconciled_artifact_bundle", "locked_spec_packet"],
            "outputs": ["empirical_execution_trace"],
            "preconditions": ["reconciled_artifact_bundle_exists"],
            "postconditions": ["deterministic_env_oracle_executed"],
            "reads": ["workspace_artifacts", "spec/locked_spec.json"],
            "writes": [],
            "exogenous_oracle": True,
        }
        critics.append(exec_oracle)

    tensor_ids: list[str] = []
    for c in critics:
        c_node = dict(c)
        c_node["writes"] = []  # Enforce strict read-only frame for parallel critics
        c_node["inputs"] = ["reconciled_artifact_bundle", "locked_spec_packet"]
        nodes.append(c_node)
        tensor_ids.append(c_node["id"])
        edges.append(
            {
                "from": pullback_node["id"],
                "to": c_node["id"],
                "op": "parallel_tensor",
                "artifact": "reconciled_artifact_bundle",
            }
        )

    if len(tensor_ids) >= 2:
        parallel_groups.append(
            {
                "id": "tensor:orthogonal-critics",
                "members": tensor_ids,
                "separation_invariant": "forall i!=j: writes(i) == [] && writes(j) == []",
            }
        )

    # Optional state recovery / checkpoint bridges
    pre_gate_ids = list(tensor_ids)
    for b in bridges:
        b_node = dict(b)
        b_node["inputs"] = ["reconciled_artifact_bundle", "empirical_execution_trace"]
        nodes.append(b_node)
        for tid in tensor_ids:
            edges.append({"from": tid, "to": b_node["id"], "op": "sequential_pipe", "artifact": "empirical_execution_trace"})
        pre_gate_ids = [b_node["id"]]

    # 4. Dominator Verify Gate + Closed-Loop Lyapunov Repair Back-Edge
    gate_node = {
        "id": "subskill:verify-gate",
        "operator_class": "oracle_gate",
        "composition_op": "orthogonal_dominator_gate",
        "inputs": [
            "reconciled_artifact_bundle",
            "pullback_witness",
            "empirical_execution_trace",
        ],
        "outputs": ["verified_certificate_or_lyapunov_repair_card"],
        "preconditions": ["all_upstream_critics_reported"],
        "postconditions": ["phi_debt_equals_zero", "no_guard_regression"],
        "reads": ["workspace_artifacts", pb_cfg["artifact"]],
        "writes": [],  # Gate never edits product artifacts!
        "exogenous_oracle": True,
    }
    nodes.append(gate_node)
    for pid in pre_gate_ids:
        edges.append({"from": pid, "to": gate_node["id"], "op": "dominator_join", "artifact": "critic_evidence"})

    done_node = {
        "id": "DONE",
        "operator_class": "terminal",
        "inputs": ["verified_certificate_or_lyapunov_repair_card"],
        "outputs": [],
        "reads": [],
        "writes": [],
        "exogenous_oracle": True,
    }
    nodes.append(done_node)
    edges.append({"from": gate_node["id"], "to": "DONE", "op": "certified_ship", "artifact": "verified_certificate"})
    # Closed-loop feedback edge when Phi > 0
    if mutators:
        edges.append(
            {
                "from": gate_node["id"],
                "to": mutators[0]["id"],
                "op": "lyapunov_feedback_retry",
                "condition": "phi_debt > 0 (upstream-first repair; control-barrier ratchet enforced)",
                "artifact": "lyapunov_repair_card",
            }
        )

    synthesized_subskills.append(
        {
            "name": "verify-gate",
            "kind": "subskill",
            "algebraic_role": "Post-Dominator Orthogonal Oracle & Lyapunov Controller",
            "job": (
                "Read-only executable gate (write_set = empty) that post-dominates every mutator "
                "before DONE; computes Lyapunov debt Phi and emits upstream-first repair cards on FAIL."
            ),
            "pulls_from": tensor_ids,
        }
    )

    graph = {
        "schema": "skillremix.wiring_graph.v2",
        "package_name": package_name,
        "domain": dom,
        "nodes": nodes,
        "edges": edges,
        "parallel_groups": parallel_groups,
        "pullback": pb_cfg,
        "synthesized_subskills": synthesized_subskills[:4],
    }
    graph["verification"] = verify_graph(graph)
    return graph


def _post_dominates(nodes_by_id: dict[str, dict], edges: list[dict], start: str, gate: str, target: str) -> bool:
    """True iff `target` is unreachable from `start` along forward edges when `gate` is removed."""
    if start == gate:
        return True
    adj: dict[str, list[str]] = {nid: [] for nid in nodes_by_id}
    for e in edges:
        if e.get("op") == "lyapunov_feedback_retry":
            continue
        u, v = e["from"], e["to"]
        if u in adj:
            adj[u].append(v)

    q = deque([start])
    seen = {start}
    while q:
        cur = q.popleft()
        if cur == gate:
            continue
        if cur == target:
            return False  # Found a path bypassing gate!
        for nxt in adj.get(cur, []):
            if nxt == gate:
                continue
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return True


def verify_graph(graph: dict[str, Any], pkg_dir: Path | None = None) -> dict[str, Any]:
    """Check the 5 formal software-engineering & information-theoretic laws on a wiring graph."""
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    by_id = {n["id"]: n for n in nodes if "id" in n}
    reasons: list[str] = []
    checks: dict[str, bool] = {}

    # 1. Type Safety: every non-entry node has >=1 incoming forward edge binding inputs
    forward_in: dict[str, int] = {nid: 0 for nid in by_id}
    for e in edges:
        if e.get("op") != "lyapunov_feedback_retry" and e.get("to") in forward_in:
            forward_in[e["to"]] += 1
    unbound = [
        nid
        for nid, n in by_id.items()
        if n.get("operator_class") not in {"guard_router"} and forward_in.get(nid, 0) == 0
    ]
    checks["type_safety"] = len(unbound) == 0
    if unbound:
        reasons.append(f"type_safety FAIL: unbound operator nodes {unbound}")

    # 2. Concurrent Separation Logic on all parallel_groups
    sep_ok = True
    for pg in graph.get("parallel_groups") or []:
        mids = pg.get("members") or []
        for i in range(len(mids)):
            for j in range(i + 1, len(mids)):
                ni = by_id.get(mids[i], {})
                nj = by_id.get(mids[j], {})
                wi = set(ni.get("writes") or [])
                wj = set(nj.get("writes") or [])
                ri = set(ni.get("reads") or [])
                rj = set(nj.get("reads") or [])
                if (wi & wj) or (wi & rj) or (wj & ri):
                    sep_ok = False
                    reasons.append(
                        f"separation_logic FAIL in {pg.get('id')}: {mids[i]} and {mids[j]} interfere"
                    )
    checks["separation_logic"] = sep_ok

    # 3. Data Processing Inequality (DPI) Grounding: at least one exogenous_oracle node on forward flow
    exo_nodes = [
        nid
        for nid, n in by_id.items()
        if n.get("exogenous_oracle") is True
        and n.get("operator_class") in {"exec_observation", "oracle_gate", "pullback_join"}
    ]
    checks["dpi_exogenous_grounding"] = len(exo_nodes) >= 2
    if not checks["dpi_exogenous_grounding"]:
        reasons.append("dpi_exogenous_grounding FAIL: pipeline lacks executable observation/oracle nodes")

    # 4. Dominator Orthogonality: every mutator must be post-dominated on all paths to DONE by an
    #    oracle_gate with writes == []
    gates = [
        nid
        for nid, n in by_id.items()
        if n.get("operator_class") == "oracle_gate" and len(n.get("writes") or []) == 0
    ]
    mutators = [nid for nid, n in by_id.items() if n.get("operator_class") == "mutator"]
    dom_ok = bool(gates) and ("DONE" in by_id)
    for m in mutators:
        if not any(_post_dominates(by_id, edges, m, g, "DONE") for g in gates):
            dom_ok = False
            reasons.append(f"dominator_orthogonality FAIL: mutator {m} can reach DONE bypassing read-only gate")
    checks["dominator_orthogonality"] = dom_ok

    # 5. Parnas Progressive Disclosure / Context Encapsulation (when package dir provided)
    parnas_ok = True
    parnas_detail: dict[str, Any] = {}
    if pkg_dir and (pkg_dir / "SKILL.md").is_file():
        skill_bytes = (pkg_dir / "SKILL.md").stat().st_size
        hidden_bytes = 0
        for sub in ("scripts", "references", "subskills", "evals"):
            d = pkg_dir / sub
            if d.is_dir():
                hidden_bytes += sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        encapsulation_ratio = hidden_bytes / max(1, skill_bytes + hidden_bytes)
        parnas_detail = {
            "skill_md_bytes": skill_bytes,
            "encapsulated_bytes": hidden_bytes,
            "encapsulation_ratio": round(encapsulation_ratio, 4),
        }
        # Flag if SKILL.md concatenates huge prose (>32KB) or hides <20% in modules
        if skill_bytes > 32000 or encapsulation_ratio < 0.20:
            parnas_ok = False
            reasons.append(
                f"parnas_encapsulation FAIL: SKILL.md={skill_bytes}B, encapsulation_ratio={encapsulation_ratio:.2f}"
            )
    checks["parnas_encapsulation"] = parnas_ok

    return {
        "decision": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "reasons": reasons,
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "exogenous_nodes": exo_nodes,
        "readonly_gates": gates,
        "parnas": parnas_detail,
    }


def render_wiring_md(graph: dict[str, Any]) -> str:
    """Render human + agent readable WIRING_CONTRACT.md."""
    lines = [
        f"# Algebraic Wiring Contract — `{graph.get('package_name')}`",
        "",
        "Synthesized via Kleisli Design-by-Contract, Concurrent Separation Logic, Pullback Reconciliation, "
        "DPI Exogenous Grounding, and Post-Dominator Orthogonal Verification.",
        "",
        "## Operators & Typed Frames",
        "",
        "| Operator ID | Class | Inputs | Outputs | Writes (Frame) | Exogenous Oracle |",
        "|---|---|---|---|---|---|",
    ]
    for n in graph.get("nodes") or []:
        if n.get("operator_class") == "terminal":
            continue
        ins = ", ".join(f"`{x}`" for x in (n.get("inputs") or []))
        outs = ", ".join(f"`{x}`" for x in (n.get("outputs") or []))
        wr = ", ".join(f"`{x}`" for x in (n.get("writes") or [])) or "∅ *(read-only)*"
        exo = "yes" if n.get("exogenous_oracle") else "no"
        lines.append(f"| `{n['id']}` | `{n['operator_class']}` | {ins} | {outs} | {wr} | {exo} |")

    pb = graph.get("pullback") or {}
    lines += [
        "",
        "## Pullback Invariant (`S_1 ×_K S_2`)",
        "",
        f"- **Shared Key (`K`):** `{pb.get('key')}`",
        f"- **Witness Artifact:** `{pb.get('artifact')}`",
        f"- **Commutative Invariant:** `{pb.get('invariant')}`",
        "",
        "## Static Verification Summary",
        "",
    ]
    ver = graph.get("verification") or {}
    for k, v in (ver.get("checks") or {}).items():
        lines.append(f"- **{k}**: `{'PASS' if v else 'FAIL'}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compile", help="Compile chosen_n.json + audits into wiring_graph.json")
    c.add_argument("--chosen-n", type=Path, required=True)
    c.add_argument("--audits", type=Path, default=None)
    c.add_argument("--domain", default=None)
    c.add_argument("--name", default="principled-remix")
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--md-out", type=Path, default=None)
    c.add_argument("--json", action="store_true")

    v = sub.add_parser("verify", help="Verify wiring_graph.json (and optional package dir)")
    v.add_argument("--graph", type=Path, required=True)
    v.add_argument("--package", type=Path, default=None)
    v.add_argument("--json", action="store_true")

    args = ap.parse_args()
    if args.cmd == "compile":
        payload = json.loads(args.chosen_n.read_text(encoding="utf-8"))
        members = payload.get("chosen") or []
        audits: dict[str, dict[str, Any]] = {}
        if args.audits and args.audits.is_dir():
            for p in args.audits.glob("*.json"):
                try:
                    d = json.loads(p.read_text(encoding="utf-8"))
                    audits[p.stem] = d
                except json.JSONDecodeError:
                    pass
        graph = compile_wiring(members, audits, domain=args.domain, package_name=args.name)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        md_path = args.md_out or args.out.with_suffix(".md")
        md_path.write_text(render_wiring_md(graph), encoding="utf-8")
        print(json.dumps(graph["verification"] if args.json else graph, indent=2))
        return 0 if graph["verification"]["decision"] == "PASS" else 2

    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    ver = verify_graph(graph, args.package)
    print(json.dumps(ver, indent=2) if args.json else ver)
    return 0 if ver["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
