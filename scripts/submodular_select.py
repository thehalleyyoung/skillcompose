#!/usr/bin/env python3
"""Information-theoretic & Kolmogorov/NCD submodular skill selector for /skillcompose.

Replaces naive popularity-top-N ("best of GitHub") and surface name-Jaccard with:
  1. 6-stage Kleisli Operational Capability Posterior p(u | s), grounded in actual file/script
     structure when local upstream skill directories are available:
       - spec_grounding      (preconditions, RFC/schema contracts, ambiguity resolution)
       - synthesis           (constructive generation, drafting, implementation, migration)
       - static_contract     (types, AST/lint invariants, pullback projection checks)
       - exec_observation    (executable tests/harnesses/SQL/CLI oracles — breaks DPI!)
       - adversarial_verify  (orthogonal read-only critique, exploit/slop/false-done gate)
       - state_recovery      (rollback, idempotence, continuity ledger, checkpointing)
  2. Monotone Submodular Noisy-OR Coverage M(S) = sum_u w_u * (1 - prod_{s in S} (1 - p(u | s)))
     with an instance-specific Nemhauser-Wolsey online submodularity upper bound certificate:
       M(OPT_N) <= min_t [ M(S_t) + sum_{top-N e in V \\ S_t} (M(S_t u {e}) - M(S_t)) ]
  3. Universal Pairwise Redundancy blending Jensen-Shannon Divergence (1 - sqrt(JSD)) AND
     Cilibrasi-Vitanyi Normalized Compression Distance (1 - d_NCD via DEFLATE/LZ77) when skill
     bodies are materialized on disk — catching cloned/reworded checklists with zero keyword tuning.
  4. Directed Producer -> Consumer Kleisli Synergy Bonus across pipeline edges.
  5. Off-Domain / Polysemy Divergence Penalty D_off(s || T).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import zlib
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remix_coherence_gate import DESC_ALIEN, DOMAIN_TOKENS, OFF_DOMAIN  # noqa: E402

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "your", "using",
    "use", "skill", "skills", "agent", "agents", "claude", "cursor", "codex",
    "code", "tool", "tools", "based", "workflow", "workflows", "helper", "helpers",
}

ROLE_WEIGHTS: dict[str, float] = {
    "spec_grounding": 1.15,
    "synthesis": 1.10,
    "static_contract": 1.05,
    "exec_observation": 1.25,     # Breaks Data Processing Inequality (exogenous channel)
    "adversarial_verify": 1.25,   # Breaks Common-Mode Self-Grading (orthogonal post-dominator)
    "state_recovery": 0.95,
}

ROLE_LEXICONS: dict[str, set[str]] = {
    "spec_grounding": {
        "spec", "specification", "requirements", "prd", "rfc", "outline", "plan",
        "planning", "clarify", "elicitation", "precondition", "contract", "design",
        "architecture", "adr", "brief", "premise", "schema", "grammar", "intake", "ebnf",
    },
    "synthesis": {
        "write", "writing", "draft", "drafting", "generate", "generator", "implement",
        "implementation", "build", "create", "author", "compose", "refactor", "patch",
        "transform", "etl", "migrate", "prose", "chapter", "code", "synthesize", "builder",
    },
    "static_contract": {
        "type", "types", "typed", "schema", "validation", "validate", "lint", "ast",
        "invariant", "consistency", "coherence", "interface", "openapi", "sql", "pullback",
        "constraint", "citation", "bibliography", "provenance", "check", "structure", "kleene",
    },
    "exec_observation": {
        "test", "testing", "pytest", "jest", "harness", "benchmark", "eval", "evals",
        "measure", "metric", "metrics", "run", "execute", "reproducible", "sandbox", "executable",
        "differential", "property", "fuzz", "query", "experiment", "empirical", "verify", "reconcile",
    },
    "adversarial_verify": {
        "audit", "security", "vulnerability", "review", "critic", "critique", "adversarial",
        "deslop", "humanize", "tells", "false", "gate", "redteam", "exploit", "bug",
        "defect", "judge", "scanner", "smell", "detect", "refusal", "guard", "bleed",
    },
    "state_recovery": {
        "continuity", "memory", "state", "checkpoint", "resume", "rollback", "recovery",
        "idempotent", "migration", "git", "history", "canon", "bridge", "handoff",
        "transaction", "backup", "observability", "incident", "ledger", "immutability",
    },
}

SYNERGY_EDGES: list[tuple[str, str, float]] = [
    ("spec_grounding", "synthesis", 0.22),
    ("synthesis", "static_contract", 0.20),
    ("static_contract", "exec_observation", 0.25),
    ("synthesis", "exec_observation", 0.24),
    ("exec_observation", "adversarial_verify", 0.26),
    ("adversarial_verify", "state_recovery", 0.18),
    ("spec_grounding", "adversarial_verify", 0.20),
]

POLYSEMY_TRAPS: dict[str, set[str]] = {
    "writing": {"plaid", "stripe", "kubernetes", "terraform", "storybook", "springboot", "solidity"},
    "research": {"plaid", "stripe", "shopify", "storybook", "springboot", "laravel", "unity"},
    "devops": {"romance", "fanfiction", "novel", "screenplay", "tarot", "plaid", "stripe"},
    "data": {"romance", "fanfiction", "storybook", "unity3d", "chartjs", "tailwind"},
    "automation": {"romance", "fanfiction", "tarot", "zigbee", "homeassistant"},
    "general": {"plaid", "stripe", "shopify"},
}


def tokenize(text: str) -> list[str]:
    raw = re.split(r"[^a-z0-9]+", (text or "").lower())
    return [t for t in raw if len(t) >= 3 and t not in STOPWORDS]


def load_local_skill_payload(row: dict[str, Any]) -> tuple[str, int]:
    """Return (concatenated SKILL.md + scripts text, executable_script_count) if materialized locally."""
    ldir = row.get("local_dir")
    if not ldir:
        return "", 0
    p = Path(str(ldir))
    if not p.is_dir():
        return "", 0
    chunks: list[str] = []
    sm = p / "SKILL.md"
    if sm.is_file():
        chunks.append(sm.read_text(encoding="utf-8", errors="replace")[:16000])
    n_scripts = 0
    sd = p / "scripts"
    if sd.is_dir():
        for sf in sorted(sd.rglob("*")):
            if sf.is_file() and sf.suffix in {".py", ".sh", ".mjs", ".js"}:
                n_scripts += 1
                chunks.append(sf.read_text(encoding="utf-8", errors="replace")[:8000])
    return "\n".join(chunks), n_scripts


def candidate_text(row: dict[str, Any]) -> str:
    sid = str(row.get("id") or "")
    slug = sid.split("@", 1)[-1].replace("-", " ").replace("_", " ")
    local_body, _ = load_local_skill_payload(row)
    # Strip frontmatter from local_body for semantic scoring
    if local_body.startswith("---"):
        parts = local_body.split("---", 2)
        if len(parts) == 3:
            local_body = parts[2]
    parts = [
        slug,
        slug,
        str(row.get("github_description") or ""),
        str(row.get("query") or ""),
        " ".join(row.get("queries") or []) if isinstance(row.get("queries"), list) else "",
        str(row.get("discovery_role") or "").replace("_", " "),
        local_body[:4000],
    ]
    return " ".join(parts)


def role_posterior(row: dict[str, Any], query: str = "") -> dict[str, float]:
    """Infer query-conditioned capability coverage p(u | s, Q) in [0, 0.94] for each Kleisli role."""
    meta_parts = [
        str(row.get("id") or "").split("@", 1)[-1].replace("-", " ").replace("_", " "),
        str(row.get("github_description") or ""),
        str(row.get("query") or ""),
        str(row.get("discovery_role") or "").replace("_", " "),
    ]
    toks = tokenize(" ".join(meta_parts))
    counts = Counter(toks)
    raw_scores: dict[str, float] = {}
    for role, lex in ROLE_LEXICONS.items():
        hits = sum(counts[w] for w in lex if w in counts)
        raw_scores[role] = 1.0 - math.exp(-0.42 * hits)

    # Empirical structural signal: real executable scripts directly ground exec_observation!
    local_body, n_scripts = load_local_skill_payload(row)
    if n_scripts > 0:
        raw_scores["exec_observation"] = max(raw_scores["exec_observation"], min(0.88, 0.55 + 0.15 * n_scripts))

    disc_role = str(row.get("discovery_role") or "").lower()
    if disc_role == "practice_support":
        raw_scores["exec_observation"] = max(raw_scores["exec_observation"], 0.35)
        raw_scores["adversarial_verify"] = max(raw_scores["adversarial_verify"], 0.35)
    elif disc_role == "domain_core" and max(raw_scores.values(), default=0.0) < 0.15:
        raw_scores["synthesis"] = 0.45

    # Query-Conditioned Relevance Multiplier I(s; Q): reward skills specialized to the concrete task query
    q_toks = set(tokenize(query))
    if q_toks:
        all_skill_toks = set(toks) | set(tokenize(local_body[:3000]))
        q_overlap = len(all_skill_toks & q_toks) / float(len(q_toks))
        # Scale factor in [0.72, 1.18]: generic unfocused skills are damped; query-specialized skills boosted
        rel_scale = 0.72 + 0.46 * min(1.0, q_overlap * 2.2)
        for role in raw_scores:
            # Keep pure verification/recovery support viable while sharpening synthesis/spec selection
            if role in {"synthesis", "spec_grounding", "static_contract"}:
                raw_scores[role] *= rel_scale
            else:
                raw_scores[role] *= (0.88 + 0.12 * rel_scale)

    return {k: round(min(0.94, v), 4) for k, v in raw_scores.items()}


ANTI_PATTERN_EXEMPLARS = [
    re.compile(r"\b[Ii]t wasn['’]t\b[^.?!]{1,80}\.\s*[Ii]t was\b"),
    re.compile(r"\beval\s*\(\s*user", re.I),
]


def contract_conflict_penalty(row: dict[str, Any]) -> float:
    """Penalize non-critic skills whose own SKILL.md positively teaches anti-patterns/slop."""
    rp = role_posterior(row)
    if rp.get("adversarial_verify", 0.0) >= 0.45:
        return 0.0  # Critics legitimately quote patterns they scan against
    local_body, _ = load_local_skill_payload(row)
    if not local_body:
        return 0.0
    hits = sum(1 for pat in ANTI_PATTERN_EXEMPLARS if pat.search(local_body))
    return round(0.85 * hits, 4)


def token_dist(row: dict[str, Any]) -> dict[str, float]:
    toks = tokenize(candidate_text(row))
    feats = list(toks)
    feats.extend(f"{toks[i]}_{toks[i+1]}" for i in range(len(toks) - 1))
    if not feats:
        sid = str(row.get("id") or "unknown")
        return {sid: 1.0}
    c = Counter(feats)
    total = float(sum(c.values()))
    return {k: v / total for k, v in c.items()}


def js_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """Normalized Jensen-Shannon Divergence in [0, 1] (bits)."""
    vocab = set(p) | set(q)
    if not vocab:
        return 0.0
    kl_pm = 0.0
    kl_qm = 0.0
    for w in vocab:
        pw = p.get(w, 0.0)
        qw = q.get(w, 0.0)
        mw = 0.5 * (pw + qw)
        if pw > 0 and mw > 0:
            kl_pm += pw * math.log2(pw / mw)
        if qw > 0 and mw > 0:
            kl_qm += qw * math.log2(qw / mw)
    return max(0.0, min(1.0, 0.5 * (kl_pm + kl_qm)))


def _czlib(b: bytes) -> int:
    return len(zlib.compress(b, level=9)) if b else 0


def normalized_compression_distance(row_a: dict[str, Any], row_b: dict[str, Any]) -> float:
    """Cilibrasi-Vitanyi Normalized Compression Distance d_NCD(x, y) in [0, 1]."""
    body_a, _ = load_local_skill_payload(row_a)
    body_b, _ = load_local_skill_payload(row_b)
    txt_a = (body_a or candidate_text(row_a)).encode("utf-8")
    txt_b = (body_b or candidate_text(row_b)).encode("utf-8")
    if not txt_a or not txt_b:
        return 1.0
    ca = _czlib(txt_a)
    cb = _czlib(txt_b)
    cab = _czlib(txt_a + b"\n---\n" + txt_b)
    denom = max(ca, cb)
    if denom == 0:
        return 1.0
    return max(0.0, min(1.0, (cab - min(ca, cb)) / float(denom)))


def monotone_coverage(chosen: list[dict[str, Any]], query: str = "") -> tuple[float, dict[str, float]]:
    """Pure monotone submodular noisy-OR coverage M(S | Q) (satisfies exact diminishing returns)."""
    posteriors = [role_posterior(r, query=query) for r in chosen]
    role_cov: dict[str, float] = {}
    cov_sum = 0.0
    for role, w in ROLE_WEIGHTS.items():
        not_cov = 1.0
        for p in posteriors:
            not_cov *= 1.0 - p.get(role, 0.0)
        cu = 1.0 - not_cov
        role_cov[role] = round(cu, 4)
        cov_sum += w * cu
    return cov_sum, role_cov


def off_domain_divergence(row: dict[str, Any], domain: str | None, query: str) -> float:
    dom = (domain or "general").lower()
    sid = str(row.get("id") or "")
    slug_toks = set(tokenize(sid.replace("@", " ").replace("/", " ")))
    desc_toks = set(tokenize(str(row.get("github_description") or "")))
    all_toks = slug_toks | desc_toks | set(tokenize(str(row.get("query") or "")))
    q_toks = set(tokenize(query))
    d_toks = DOMAIN_TOKENS.get(dom, set())
    target = q_toks | d_toks

    penalty = 0.0
    alien = DESC_ALIEN.get(dom, set())
    if alien and (desc_toks & alien):
        penalty += 1.6

    off_hits = (OFF_DOMAIN & all_toks) - q_toks
    if off_hits and dom in {"writing", "research", "data", "automation"}:
        penalty += 1.4

    traps = (POLYSEMY_TRAPS.get(dom, set()) | POLYSEMY_TRAPS["general"]) - q_toks
    if traps & slug_toks:
        penalty += 1.8

    roles = role_posterior(row)
    support_mass = max(
        roles["exec_observation"],
        roles["adversarial_verify"],
        roles["state_recovery"],
        roles["static_contract"],
    )
    if target and not (all_toks & target) and support_mass < 0.35:
        penalty += 0.75

    installs = row.get("installs") or row.get("stars") or 0
    try:
        pop_prior = min(0.18, 0.025 * math.log10(max(1.0, float(installs))))
    except (TypeError, ValueError):
        pop_prior = 0.0

    return round(max(0.0, penalty - pop_prior), 4)


def evaluate_set(
    chosen: list[dict[str, Any]],
    *,
    domain: str | None = None,
    query: str = "",
    lambda_syn: float = 0.35,
    lambda_red: float = 0.85,
    lambda_oot: float = 1.0,
) -> dict[str, Any]:
    if not chosen:
        return {
            "objective": 0.0,
            "submodular_coverage": 0.0,
            "normalized_coverage": 0.0,
            "chain_synergy": 0.0,
            "mean_redundancy": 0.0,
            "mean_jsd": 1.0,
            "mean_ncd": 1.0,
            "off_domain_penalty": 0.0,
            "role_coverage": {r: 0.0 for r in ROLE_WEIGHTS},
            "role_entropy_bits": 0.0,
            "has_exogenous_grounding": False,
            "has_orthogonal_verify": False,
        }

    posteriors = [role_posterior(r, query=query) for r in chosen]
    dists = [token_dist(r) for r in chosen]
    cov_sum, role_cov = monotone_coverage(chosen, query=query)
    max_cov_sum = sum(ROLE_WEIGHTS.values())

    syn_sum = 0.0
    for r_src, r_dst, weight in SYNERGY_EDGES:
        best_pair = 0.0
        for i, pi in enumerate(posteriors):
            for j, pj in enumerate(posteriors):
                if i == j:
                    continue
                best_pair = max(best_pair, min(pi[r_src], pj[r_dst]))
        syn_sum += weight * best_pair

    jsd_vals: list[float] = []
    ncd_vals: list[float] = []
    owner_collisions = 0
    for i in range(len(chosen)):
        oi = str(chosen[i].get("id") or "").split("/", 1)[0].lower()
        for j in range(i + 1, len(chosen)):
            oj = str(chosen[j].get("id") or "").split("/", 1)[0].lower()
            jsd_vals.append(js_divergence(dists[i], dists[j]))
            ncd_vals.append(normalized_compression_distance(chosen[i], chosen[j]))
            if oi and oi == oj:
                owner_collisions += 1

    mean_jsd = sum(jsd_vals) / len(jsd_vals) if jsd_vals else 1.0
    mean_ncd = sum(ncd_vals) / len(ncd_vals) if ncd_vals else 1.0
    jsd_sim = sum(1.0 - math.sqrt(v) for v in jsd_vals) / len(jsd_vals) if jsd_vals else 0.0
    ncd_sim = sum(1.0 - v for v in ncd_vals) / len(ncd_vals) if ncd_vals else 0.0
    # Universal + distributional blend: 65% JSD semantic similarity + 35% Kolmogorov/NCD similarity
    blended_sim = 0.65 * jsd_sim + 0.35 * ncd_sim
    owner_pen = 0.12 * owner_collisions / max(1, len(chosen) - 1)
    redundancy = blended_sim + owner_pen

    oot_sum = sum(off_domain_divergence(r, domain, query) + contract_conflict_penalty(r) for r in chosen)

    tot_r = sum(role_cov.values())
    entropy = 0.0
    if tot_r > 0:
        for v in role_cov.values():
            if v > 0:
                pv = v / tot_r
                entropy -= pv * math.log2(pv)

    objective = cov_sum + lambda_syn * syn_sum - lambda_red * redundancy - lambda_oot * oot_sum
    return {
        "objective": round(objective, 4),
        "submodular_coverage": round(cov_sum, 4),
        "normalized_coverage": round(cov_sum / max_cov_sum, 4),
        "chain_synergy": round(syn_sum, 4),
        "mean_redundancy": round(redundancy, 4),
        "mean_jsd": round(mean_jsd, 4),
        "mean_ncd": round(mean_ncd, 4),
        "off_domain_penalty": round(oot_sum, 4),
        "role_coverage": role_cov,
        "role_entropy_bits": round(entropy, 4),
        "has_exogenous_grounding": role_cov["exec_observation"] >= 0.35,
        "has_orthogonal_verify": role_cov["adversarial_verify"] >= 0.35,
    }


def compute_nemhauser_wolsey_bound(
    pool: list[dict[str, Any]],
    prefixes: list[list[dict[str, Any]]],
    k: int,
    query: str = "",
) -> dict[str, float]:
    """Compute tight online submodular upper bound on monotone coverage M(OPT_k | Q)."""
    if not pool or k <= 0:
        return {"achieved_coverage": 0.0, "opt_upper_bound": 0.0, "optimality_ratio_lower_bound": 1.0}
    tightest_ub = float("inf")
    for s_t in prefixes:
        m_st, _ = monotone_coverage(s_t, query=query)
        s_ids = {r.get("id") for r in s_t}
        marginals = []
        for cand in pool:
            if cand.get("id") in s_ids:
                continue
            m_next, _ = monotone_coverage(s_t + [cand], query=query)
            marginals.append(max(0.0, m_next - m_st))
        marginals.sort(reverse=True)
        ub_t = m_st + sum(marginals[:k])
        tightest_ub = min(tightest_ub, ub_t)
    achieved, _ = monotone_coverage(prefixes[-1], query=query)
    ratio = achieved / tightest_ub if tightest_ub > 1e-9 else 1.0
    return {
        "achieved_coverage": round(achieved, 4),
        "opt_upper_bound": round(tightest_ub, 4),
        "optimality_ratio_lower_bound": round(min(1.0, ratio), 4),
        "nemhauser_wolsey_worst_case_floor": round(1.0 - math.exp(-1.0), 4),
    }


def select_submodular(
    eligible: list[dict[str, Any]],
    n: int,
    *,
    domain: str | None = None,
    query: str = "",
    seed: str = "skillcompose",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, float]]:
    def tie_key(r: dict[str, Any]) -> str:
        return hashlib.sha256(f"{seed}:{r.get('id')}".encode()).hexdigest()

    pool = sorted(eligible, key=tie_key)
    chosen: list[dict[str, Any]] = []
    prefixes: list[list[dict[str, Any]]] = [[]]
    trace: list[dict[str, Any]] = []
    current_eval = evaluate_set([], domain=domain, query=query)
    k_target = min(n, len(pool))

    for step in range(1, k_target + 1):
        best_row: dict[str, Any] | None = None
        best_gain = -1e9
        best_eval: dict[str, Any] | None = None
        chosen_ids = {c.get("id") for c in chosen}

        for cand in pool:
            if cand.get("id") in chosen_ids:
                continue
            cand_eval = evaluate_set(chosen + [cand], domain=domain, query=query)
            gain = cand_eval["objective"] - current_eval["objective"]
            if gain > best_gain:
                best_gain = gain
                best_row = cand
                best_eval = cand_eval

        if best_row is None or best_eval is None:
            break

        enriched = dict(best_row)
        enriched["role_posterior"] = role_posterior(best_row, query=query)
        enriched["marginal_information_gain"] = round(best_gain, 4)
        enriched["off_domain_divergence"] = off_domain_divergence(best_row, domain, query)
        enriched["contract_conflict_penalty"] = contract_conflict_penalty(best_row)
        chosen.append(enriched)
        prefixes.append(list(chosen))
        current_eval = best_eval
        trace.append(
            {
                "step": step,
                "picked_id": best_row.get("id"),
                "marginal_gain": round(best_gain, 4),
                "cumulative_objective": current_eval["objective"],
                "normalized_coverage": current_eval["normalized_coverage"],
                "role_entropy_bits": current_eval["role_entropy_bits"],
            }
        )

    nw_cert = compute_nemhauser_wolsey_bound(pool, prefixes, k_target, query=query)
    return chosen, trace, nw_cert


def popularity_top_n(eligible: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    def pop_key(r: dict[str, Any]) -> tuple[float, str]:
        inst = r.get("installs") or r.get("github_stars") or r.get("stars") or 0
        try:
            v = float(inst)
        except (TypeError, ValueError):
            v = 0.0
        return (-v, str(r.get("id") or ""))

    return sorted(eligible, key=pop_key)[: min(n, len(eligible))]


def build_selection_report(
    eligible: list[dict[str, Any]],
    n: int,
    *,
    domain: str | None = None,
    query: str = "",
    seed: str = "skillcompose",
) -> dict[str, Any]:
    chosen, trace, nw_cert = select_submodular(eligible, n, domain=domain, query=query, seed=seed)
    principled_eval = evaluate_set(chosen, domain=domain, query=query)

    pop_set = popularity_top_n(eligible, n)
    pop_eval = evaluate_set(pop_set, domain=domain, query=query)

    return {
        "strategy": "submodular_kleisli_jsd_ncd",
        "domain": domain or "general",
        "query": query,
        "requested_n": n,
        "eligible_count": len(eligible),
        "chosen": chosen,
        "greedy_trace": trace,
        "nemhauser_wolsey_certificate": nw_cert,
        "principled_metrics": principled_eval,
        "counterfactual_popularity_top_n": {
            "chosen_ids": [r.get("id") for r in pop_set],
            "metrics": pop_eval,
        },
        "lift_over_popularity_top_n": {
            "objective_delta": round(principled_eval["objective"] - pop_eval["objective"], 4),
            "coverage_delta": round(
                principled_eval["normalized_coverage"] - pop_eval["normalized_coverage"], 4
            ),
            "synergy_delta": round(principled_eval["chain_synergy"] - pop_eval["chain_synergy"], 4),
            "redundancy_reduction": round(
                pop_eval["mean_redundancy"] - principled_eval["mean_redundancy"], 4
            ),
            "entropy_bits_delta": round(
                principled_eval["role_entropy_bits"] - pop_eval["role_entropy_bits"], 4
            ),
        },
    }


def compare_vs_github_top(
    eligible: list[dict[str, Any]],
    n: int,
    *,
    domain: str | None = None,
    query: str = "",
    seed: str = "skillcompose",
) -> dict[str, Any]:
    """Structured comparison between submodular JSD+NCD selection and GitHub Popularity-Top-N."""
    rep = build_selection_report(eligible, n, domain=domain, query=query, seed=seed)
    return {
        "chosen": rep["chosen"],
        "principled_ids": [r.get("id") for r in rep["chosen"]],
        "github_top_ids": rep["counterfactual_popularity_top_n"]["chosen_ids"],
        "principled": rep["principled_metrics"],
        "github_top": rep["counterfactual_popularity_top_n"]["metrics"],
        "nemhauser_wolsey_certificate": rep["nemhauser_wolsey_certificate"],
        "lift": rep["lift_over_popularity_top_n"],
        "trace": rep["greedy_trace"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, required=True, help="JSONL or JSON candidate list")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--domain", default=None)
    ap.add_argument("--query", default="")
    ap.add_argument("--seed", default="skillcompose")
    ap.add_argument("--write-chosen", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.candidates.is_file():
        print(json.dumps({"error": "candidates_missing", "path": str(args.candidates)}), file=sys.stderr)
        return 2

    raw = args.candidates.read_text(encoding="utf-8").strip()
    rows: list[dict[str, Any]] = []
    if raw.startswith("["):
        rows = json.loads(raw)
    else:
        for line in raw.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    eligible = [r for r in rows if r.get("eligible") is True]
    if not eligible:
        print(json.dumps({"error": "no_eligible_candidates", "total": len(rows)}), file=sys.stderr)
        return 2

    report = build_selection_report(
        eligible,
        max(1, args.n),
        domain=args.domain,
        query=args.query,
        seed=args.seed,
    )
    if args.write_chosen:
        args.write_chosen.parent.mkdir(parents=True, exist_ok=True)
        args.write_chosen.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for r in report["chosen"]:
            print(r.get("id"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
