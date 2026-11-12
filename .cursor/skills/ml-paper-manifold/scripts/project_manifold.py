#!/usr/bin/env python3
"""Standalone Lawvere-Amari Inverse Chart Encoder & e-Geodesic Synthesizer (/skillcompose).

Maps a task input x in X onto the compiled skill manifold M:
  1. Conormal Domain Guard P_M(x): halts with exit 2 (`ABSTAIN_OFF_MANIFOLD`) on alien/polysemic inputs.
  2. Fisher-Rao Tangent Projection: computes chart coordinates theta*(x) and e-geodesic landmark weights.
  3. Anti-Unified Lawvere Fiber Resolution: instantiates contradiction-free clauses T_M(theta*(x)).
  4. Conditional Markov Kernel K_{theta*(x)}(y | x): evaluates exact probabilities over the 648-state
     structured output lattice Y and emits the MAP structured output + sheaf gluing obligations.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

AXIS_LEXICONS = {
    "spec_modality": {
        "json_contract": {"json", "schema", "schemas", "openapi", "contract", "contracts", "typed", "types", "interface", "payload", "manifest", "validation"},
        "formal_grammar_adr": {"rfc", "adr", "ebnf", "grammar", "formal", "precondition", "preconditions", "specification", "invariant", "invariants", "dsl", "protocol", "spec"},
        "informal_prose": {"brainstorm", "ideate", "freeform", "creative", "chat"},
    },
    "execution_regime": {
        "streaming_incremental": {"stream", "streaming", "incremental", "chunk", "chunked", "jsonl", "iterator", "cursor", "pipeline", "event", "webhook", "realtime"},
        "transactional_staged": {"transaction", "transactional", "migration", "staged", "atomic", "two", "phase", "commit", "zero", "downtime", "database", "sql", "sqlite"},
        "single_shot": {"single", "oneshot", "template", "snippet", "quick", "draft"},
    },
    "verification_channel": {
        "static_ast_contract": {"ast", "lint", "typecheck", "static", "syntax", "parse", "parser", "check", "structure", "kleene", "citation", "provenance"},
        "exogenous_exec_oracle": {"pytest", "jest", "test", "testing", "harness", "benchmark", "run", "execute", "sandbox", "empirical", "reproducible", "eval", "evals", "query", "verify"},
        "adversarial_differential": {"adversarial", "redteam", "exploit", "fuzz", "differential", "property", "counterexample", "security", "vulnerability", "audit", "critic", "critique"},
        "prose_self_check": {"polish", "review", "clean", "readability"},
    },
    "failure_semantics": {
        "abstain_exit2": {"abstain", "refuse", "refusal", "guard", "exit", "reject", "strict", "gate", "preflight"},
        "idempotent_rollback": {"rollback", "recovery", "checkpoint", "resume", "idempotent", "undo", "backup", "restore", "continuity", "ledger", "state"},
        "silent_partial": {"best", "effort", "fallback"},
    },
    "gluing_topology": {
        "sheaf_global_section": {"pullback", "sheaf", "reconcile", "bijective", "global", "consistency", "coherence", "canon", "cross", "ledger", "invariant"},
        "pairwise_handoff": {"handoff", "bridge", "adapter", "pack", "pipe", "chain", "stage", "wire"},
        "unlinked_outputs": {"standalone", "isolated"},
    },
    "context_disclosure": {
        "progressive_parnas": {"references", "scripts", "subskills", "modular", "encapsulate", "progressive", "disclosure", "compact"},
        "monolithic_prompt": {"mega", "all", "prompt"},
    },
}


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= 2]


def encode_x(text: str) -> dict[str, float]:
    toks = Counter(tokenize(text))
    sc = sum(toks[w] for w in ("stream", "streaming", "large", "million", "jsonl", "chunk", "incremental", "realtime", "batch"))
    st = sum(toks[w] for w in ("migration", "rollback", "state", "checkpoint", "database", "sql", "sqlite", "transaction", "zero", "downtime", "canon", "continuity"))
    sr = sum(toks[w] for w in ("rfc", "formal", "grammar", "strict", "security", "audit", "exploit", "contract", "schema", "invariant", "adversarial"))
    mv = sum(toks[w] for w in ("api", "schema", "reconcile", "pullback", "sheaf", "cross", "pipeline", "multi", "sync", "bridge"))
    return {
        "scale": round(1.0 - math.exp(-0.55 * sc), 4),
        "stateful": round(1.0 - math.exp(-0.55 * st), 4),
        "strict": round(1.0 - math.exp(-0.45 * sr), 4),
        "multi_view": round(1.0 - math.exp(-0.55 * mv), 4),
    }


def psi_xy(x_feat: dict[str, float], y: tuple[str, ...]) -> list[float]:
    spec, ex, ver, fail, glue, disc = y
    f0 = 1.0 if spec == "json_contract" else 0.0
    f1 = 1.0 if spec == "formal_grammar_adr" else 0.0
    f2 = 1.0 if ex == "streaming_incremental" else 0.0
    f3 = 1.0 if ex == "transactional_staged" else 0.0
    f4 = 1.0 if ver == "static_ast_contract" else 0.0
    f5 = 1.0 if ver == "exogenous_exec_oracle" else 0.0
    f6 = 1.0 if ver == "adversarial_differential" else 0.0
    f7 = 1.0 if fail == "abstain_exit2" else 0.0
    f8 = 1.0 if fail == "idempotent_rollback" else 0.0
    f9 = 1.0 if glue == "pairwise_handoff" else 0.0
    f10 = 1.0 if glue == "sheaf_global_section" else 0.0
    f11 = 1.0 if disc == "progressive_parnas" else 0.0
    return [
        f0, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11,
        x_feat["scale"] * f2,
        x_feat["stateful"] * (0.5 * f3 + 0.5 * f8),
        x_feat["strict"] * (0.5 * f1 + 0.5 * f6),
        x_feat["multi_view"] * f10,
    ]


def probe_eta(text: str, x_feat: dict[str, float]) -> list[float]:
    toks = Counter(tokenize(text))
    def lp(ax: str, val: str, base: float) -> float:
        hits = sum(toks[w] for w in AXIS_LEXICONS[ax].get(val, set()) if w in toks)
        return base + 0.55 * math.log1p(hits) + (1.15 if hits >= 2 else 0.0)
    return [
        lp("spec_modality", "json_contract", 0.2),
        lp("spec_modality", "formal_grammar_adr", 0.2),
        lp("execution_regime", "streaming_incremental", 0.0),
        lp("execution_regime", "transactional_staged", 0.0),
        lp("verification_channel", "static_ast_contract", 0.2),
        lp("verification_channel", "exogenous_exec_oracle", 0.35),
        lp("verification_channel", "adversarial_differential", 0.25),
        lp("failure_semantics", "abstain_exit2", 0.3),
        lp("failure_semantics", "idempotent_rollback", 0.15),
        lp("gluing_topology", "pairwise_handoff", 0.2),
        lp("gluing_topology", "sheaf_global_section", 0.25),
        lp("context_disclosure", "progressive_parnas", 0.35),
        1.1 * x_feat["scale"],
        1.1 * x_feat["stateful"],
        1.1 * x_feat["strict"],
        1.1 * x_feat["multi_view"],
    ]


def main() -> int:
    default_atlas = Path(__file__).resolve().parent.parent / "references" / "manifold_atlas.json"
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--atlas", type=Path, default=default_atlas)
    ap.add_argument("--input", required=True, help="Task prompt string or path to task file")
    ap.add_argument("--require", action="append", default=[], help="Optional axis=value override")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
    inp = Path(args.input)
    text = inp.read_text(encoding="utf-8", errors="replace") if inp.is_file() else args.input
    toks = set(tokenize(text))
    guard = atlas.get("domain_guard") or {}
    q_seed = set(tokenize(str(atlas.get("query") or "")))
    traps = (set(guard.get("polysemy_traps") or []) | set(guard.get("alien_tokens") or [])) - q_seed
    off_dom = set(guard.get("off_domain_tokens") or []) - q_seed
    dom_toks = set(guard.get("domain_tokens") or [])

    trap_hits = sorted(toks & traps)
    off_hits = sorted(toks & off_dom)
    if trap_hits or (off_hits and not (toks & dom_toks)):
        rep = {
            "ok": False,
            "decision": "ABSTAIN_OFF_MANIFOLD",
            "domain": atlas.get("domain"),
            "reasons": [f"conormal_domain_guard_rejected: trap_hits={trap_hits}, off_domain_hits={off_hits}"],
        }
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(rep, indent=2))
        return 2

    x_feat = encode_x(text)
    geom = atlas["geometry"]
    eta_0 = geom["barycenter_eta"]
    g_half = geom["fisher_sqrt"]
    w_basis = geom["whitened_basis"]
    t_basis = geom["tangent_basis_eta"]
    p_eta = probe_eta(text, x_feat)
    raw_d = [p_eta[i] - eta_0[i] for i in range(len(eta_0))]
    w_d = [sum(g_half[r][c] * raw_d[c] for c in range(len(eta_0))) for r in range(len(eta_0))]
    theta = [sum(u[i] * w_d[i] for i in range(len(eta_0))) for u in w_basis]
    norm_t = math.sqrt(sum(c * c for c in theta))
    if norm_t > 3.0:
        theta = [c * 3.0 / norm_t for c in theta]
    eta_star = [eta_0[d] + sum(c * v[d] for c, v in zip(theta, t_basis)) for d in range(len(eta_0))]

    landmarks = atlas.get("landmarks") or []
    lm_weights = {}
    if landmarks:
        nd = []
        for lm in landmarks:
            lc = lm.get("chart_coordinates") or []
            sq = sum((a - b) ** 2 for a, b in zip(theta, lc))
            aff = lm.get("input_affinity") or {}
            asim = sum(x_feat[k] * float(aff.get(k, 0.0)) for k in x_feat)
            nd.append(-0.85 * sq + 1.25 * asim)
        mx = max(nd)
        exps = [math.exp(v - mx) for v in nd]
        zw = sum(exps)
        for lm, ew in zip(landmarks, exps):
            lm_weights[lm["slug"]] = round(ew / zw, 4)

    reqs = {}
    for item in args.require:
        if "=" in item:
            k, v = item.split("=", 1)
            reqs[k.strip()] = v.strip()

    logic = atlas["logic"]
    fiber = {ax: list(vals) for ax, vals in logic["conormal_core"].items()}
    chart_assign = {}
    tok_counts = Counter(tokenize(text))
    for ax, cv in (logic.get("chart_variables") or {}).items():
        dvals = list(cv["domain"])
        if ax in reqs and reqs[ax] in dvals:
            picked = [reqs[ax]]
        else:
            scored = [(sum(tok_counts[w] for w in AXIS_LEXICONS[ax].get(v, set()) if w in tok_counts), v) for v in dvals]
            bs = max(s for s, _ in scored)
            picked = [v for s, v in scored if s == bs] if bs > 0 else dvals
        fiber[ax] = picked
        chart_assign[ax] = picked

    axes_order = list(atlas["output_axes"].keys())
    space = list(itertools.product(*(atlas["output_axes"][a] for a in axes_order)))
    valid = []
    max_s = float("-inf")
    for idx, y in enumerate(space):
        if all(y[j] in fiber[axes_order[j]] for j in range(len(axes_order))):
            sc = sum(eta_star[d] * psi_xy(x_feat, y)[d] for d in range(len(eta_star)))
            valid.append((idx, sc))
            if sc > max_s:
                max_s = sc
    z = sum(math.exp(sc - max_s) for _, sc in valid)
    log_z = max_s + math.log(z)
    ranked = sorted(((math.exp(sc - log_z), idx) for idx, sc in valid), reverse=True)

    rep = {
        "ok": True,
        "decision": "SYNTHESIZE_ON_MANIFOLD",
        "domain": atlas.get("domain"),
        "fisher_chart_coordinates": [round(c, 5) for c in theta],
        "landmark_e_geodesic_weights": lm_weights,
        "resolved_lawvere_fiber": fiber,
        "resolved_chart_variables": chart_assign,
        "admissible_output_fiber_cardinality": len(valid),
        "map_structured_output": {axes_order[j]: space[ranked[0][1]][j] for j in range(len(axes_order))} if ranked else {},
        "sheaf_gluing_obligations": atlas["sheaf_nerve"]["overlaps"],
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
