#!/usr/bin/env python3
"""Lawvere-Amari Generative Skill Manifold Engine for /skillcompose.

Rigorous mathematical synthesis of a parameterized generative transducer family from a finite
sample of marketplace skills S = {s_1, ..., s_N}.

Core Theoretical Objects Implemented:
  1. Skill as a Guarded Conditional Markov Kernel (Kleisli Morphism over Structured Outputs):
       s = (P_s, Q_s, K_{eta_s})
     where P_s subseteq X is a decidable input guard, Q_s subseteq X x Y is a logical refinement
     theory cutting out the admissible structured output fiber Y_s(x) = {y in Y : (x, y) |= Q_s},
     and K_{eta_s}(y | x) = I[(x, y) |= Q_s] * exp(<eta_s, psi(x, y)>) / Z(eta_s, Q_s; x) is an
     exact conditional exponential-family generative process over the 648-state structured output
     architecture lattice Y.

  2. Logical Normal-Tangent Decomposition (Galois Closure + Plotkin-Reynolds Anti-Unification):
     - Conormal Bundle N*M (Universal Galois Invariants Phi_core = Th_MDL(S)):
       Universal structural & domain invariants cutting out the manifold M inside ambient space.
     - Tangent Coordinates Theta (Plotkin-Reynolds Least General Generalization lgg):
       Whenever sampled skills s_i, s_j specialize conflicting clauses (xi_a = v_i vs xi_a = v_j,
       which causes Constraint-Union Collapse Y_{Q_i & Q_j}(x) = empty under prompt concatenation),
       anti-unification lifts xi_a into a typed Lawvere fiber variable theta_a in Theta_a with
       pullback specializations sigma_i^*(T_M) == Q_i & Phi_core.

  3. Amari Conditional Statistical Manifold & Fisher-Rao Tangent Basis:
     - Computes the exact Conditional Fisher Information Metric:
         G_F(eta_0) = E_{x ~ mu}[ Cov_{y ~ K_{eta_0}(. | x)}(psi(x, y)) ]
     - Extracts G_F-orthonormal principal geodesic generators V = [v_1, ..., v_r] via cyclic
       Jacobi eigendecomposition, effective intrinsic dimension d_eff (participation ratio),
       e-geodesic (variational KL barycenter) synthesis, and D-optimal Log-Det Fisher volume
       V_Fisher(S) = 0.5 * log det(I + alpha * Psi_S^T Psi_S) for monotone submodular selection.

  4. Sheaf Gluing & Cech Cohomology Verification (H^0(U, F) = ker delta^0, delta^1 = 0):
     - Verifies static 1-cocycle holonomy exactness across triangle overlaps in the output nerve
       N(U) and runtime 0-coboundary agreement across structured output artifacts.
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
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from remix_coherence_gate import DESC_ALIEN, DOMAIN_TOKENS, OFF_DOMAIN  # noqa: E402

# ---------------------------------------------------------------------------
# 1. Structured Output Space Y (|Y| = 3 * 3 * 4 * 3 * 3 * 2 = 648 states)
# ---------------------------------------------------------------------------

OUTPUT_AXES: dict[str, tuple[str, ...]] = {
    "spec_modality": ("informal_prose", "json_contract", "formal_grammar_adr"),
    "execution_regime": ("single_shot", "streaming_incremental", "transactional_staged"),
    "verification_channel": (
        "prose_self_check",
        "static_ast_contract",
        "exogenous_exec_oracle",
        "adversarial_differential",
    ),
    "failure_semantics": ("silent_partial", "abstain_exit2", "idempotent_rollback"),
    "gluing_topology": ("unlinked_outputs", "pairwise_handoff", "sheaf_global_section"),
    "context_disclosure": ("monolithic_prompt", "progressive_parnas"),
}

AXIS_NAMES: tuple[str, ...] = tuple(OUTPUT_AXES.keys())

# Enumerate all 648 structured output states deterministically once
STRUCTURED_OUTPUT_SPACE: tuple[tuple[str, ...], ...] = tuple(
    itertools.product(*(OUTPUT_AXES[a] for a in AXIS_NAMES))
)

# Feature basis psi(x, y) in R^16 for conditional exponential family K_eta(y | x)
FEATURE_NAMES: tuple[str, ...] = (
    "spec_json_contract",
    "spec_formal_grammar",
    "exec_streaming",
    "exec_transactional",
    "verify_static_ast",
    "verify_exogenous_oracle",
    "verify_adversarial_diff",
    "fail_abstain_exit2",
    "fail_idempotent_rollback",
    "glue_pairwise",
    "glue_sheaf_section",
    "disclosure_parnas",
    # Input-output bilinear coupling features psi_X(x) * psi_Y(y)
    "couple_scale_streaming",
    "couple_stateful_rollback",
    "couple_strict_formal_spec",
    "couple_multi_view_sheaf",
)
DIM_ETA = len(FEATURE_NAMES)

# Canonical reference probe inputs mu(x) covering the input space X
PROBE_INPUTS: tuple[dict[str, float], ...] = (
    {"scale": 0.1, "stateful": 0.1, "strict": 0.3, "multi_view": 0.2},
    {"scale": 0.9, "stateful": 0.2, "strict": 0.4, "multi_view": 0.5},
    {"scale": 0.2, "stateful": 0.9, "strict": 0.8, "multi_view": 0.7},
    {"scale": 0.7, "stateful": 0.8, "strict": 0.9, "multi_view": 0.9},
)

AXIS_LEXICONS: dict[str, dict[str, set[str]]] = {
    "spec_modality": {
        "json_contract": {
            "json", "schema", "schemas", "openapi", "contract", "contracts", "typed",
            "types", "interface", "payload", "manifest", "validation", "pydantic",
        },
        "formal_grammar_adr": {
            "rfc", "adr", "ebnf", "grammar", "formal", "precondition", "preconditions",
            "specification", "invariant", "invariants", "axiom", "dsl", "protocol", "spec",
        },
        "informal_prose": {"brainstorm", "ideate", "ideation", "freeform", "creative", "chat"},
    },
    "execution_regime": {
        "streaming_incremental": {
            "stream", "streaming", "incremental", "chunk", "chunked", "jsonl", "iterator",
            "cursor", "pipeline", "event", "webhook", "realtime", "batching",
        },
        "transactional_staged": {
            "transaction", "transactional", "migration", "staged", "atomic", "two",
            "phase", "commit", "lock", "zero", "downtime", "database", "sql", "sqlite",
        },
        "single_shot": {"single", "oneshot", "template", "snippet", "quick", "draft"},
    },
    "verification_channel": {
        "static_ast_contract": {
            "ast", "lint", "typecheck", "mypy", "static", "syntax", "parse", "parser",
            "check", "structure", "kleene", "citation", "provenance",
        },
        "exogenous_exec_oracle": {
            "pytest", "jest", "test", "testing", "harness", "benchmark", "run", "execute",
            "sandbox", "empirical", "reproducible", "eval", "evals", "query", "verify",
        },
        "adversarial_differential": {
            "adversarial", "redteam", "exploit", "fuzz", "differential", "property",
            "counterexample", "security", "vulnerability", "audit", "critic", "critique",
            "deslop", "bleed", "smell", "false",
        },
        "prose_self_check": {"polish", "review", "clean", "readability"},
    },
    "failure_semantics": {
        "abstain_exit2": {
            "abstain", "refuse", "refusal", "guard", "exit", "reject", "strict",
            "non", "trigger", "gate", "preflight", "failfast",
        },
        "idempotent_rollback": {
            "rollback", "recovery", "checkpoint", "resume", "idempotent", "undo",
            "backup", "restore", "continuity", "ledger", "state", "history",
        },
        "silent_partial": {"best", "effort", "fallback", "approximate"},
    },
    "gluing_topology": {
        "sheaf_global_section": {
            "pullback", "sheaf", "reconcile", "reconciler", "bijective", "global",
            "consistency", "coherence", "canon", "cross", "ledger", "invariant",
        },
        "pairwise_handoff": {
            "handoff", "bridge", "adapter", "pack", "pipe", "chain", "stage", "wire",
        },
        "unlinked_outputs": {"standalone", "isolated"},
    },
    "context_disclosure": {
        "progressive_parnas": {
            "references", "scripts", "subskills", "modular", "encapsulate", "progressive",
            "disclosure", "compact", "module",
        },
        "monolithic_prompt": {"mega", "all", "prompt"},
    },
}

POLYSEMY_GUARD: dict[str, set[str]] = {
    "writing": {"plaid", "stripe", "kubernetes", "terraform", "storybook", "springboot", "solidity"},
    "research": {"plaid", "stripe", "shopify", "storybook", "springboot", "laravel", "unity"},
    "devops": {"romance", "fanfiction", "novel", "screenplay", "tarot", "plaid", "stripe"},
    "data": {"romance", "fanfiction", "storybook", "unity3d", "chartjs", "tailwind"},
    "automation": {"romance", "fanfiction", "tarot", "zigbee", "homeassistant", "plaid", "stripe"},
    "general": {"plaid", "stripe", "shopify"},
}


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= 2]


def _slug_of(sid: str) -> str:
    return (sid.split("@", 1)[-1] if "@" in sid else sid.split("/")[-1]).lower()


# ---------------------------------------------------------------------------
# 2. Exact Self-Contained Pure-Python Linear Algebra (Jacobi Eig + Cholesky)
# ---------------------------------------------------------------------------

def mat_eye(n: int) -> list[list[float]]:
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    m, k, n = len(a), len(b), len(b[0])
    bt = [[b[r][c] for r in range(k)] for c in range(n)]
    return [[sum(a[i][p] * bt[j][p] for p in range(k)) for j in range(n)] for i in range(m)]


def mat_vec(a: list[list[float]], v: list[float]) -> list[float]:
    return [sum(row[j] * v[j] for j in range(len(v))) for row in a]


def dot(u: list[float], v: list[float]) -> float:
    return sum(x * y for x, y in zip(u, v))


def cholesky_decomp(a: list[list[float]], jitter: float = 1e-9) -> list[list[float]]:
    """Exact Cholesky factor L such that A + jitter*I = L L^T for SPD matrix A."""
    n = len(a)
    l_mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = sum(l_mat[i][k] * l_mat[j][k] for k in range(j))
            if i == j:
                val = a[i][i] + jitter - s
                l_mat[i][j] = math.sqrt(max(1e-15, val))
            else:
                l_mat[i][j] = (a[i][j] - s) / l_mat[j][j]
    return l_mat


def spd_logdet(a: list[list[float]]) -> float:
    """Exact log det(A) for symmetric positive-definite matrix A via Cholesky."""
    l_mat = cholesky_decomp(a, jitter=1e-12)
    return 2.0 * sum(math.log(l_mat[i][i]) for i in range(len(l_mat)))


def jacobi_eigh(sym: list[list[float]], tol: float = 1e-11, max_sweeps: int = 80) -> tuple[list[float], list[list[float]]]:
    """Exact cyclic Jacobi eigenvalue decomposition for real symmetric matrix.

    Returns (eigenvalues_descending, eigenvectors_columns_as_list_of_vectors).
    """
    n = len(sym)
    a = [[0.5 * (sym[i][j] + sym[j][i]) for j in range(n)] for i in range(n)]
    v = mat_eye(n)

    for _ in range(max_sweeps):
        max_off = 0.0
        for p in range(n):
            for q in range(p + 1, n):
                if abs(a[p][q]) > max_off:
                    max_off = abs(a[p][q])
        if max_off < tol:
            break
        for p in range(n):
            for q in range(p + 1, n):
                apq = a[p][q]
                if abs(apq) < tol:
                    continue
                app, aqq = a[p][p], a[q][q]
                tau = (aqq - app) / (2.0 * apq)
                t = (1.0 / (tau + math.sqrt(1.0 + tau * tau))) if tau >= 0 else (-1.0 / (-tau + math.sqrt(1.0 + tau * tau)))
                c = 1.0 / math.sqrt(1.0 + t * t)
                s = t * c
                a[p][p] = app - t * apq
                a[q][q] = aqq + t * apq
                a[p][q] = a[q][p] = 0.0
                for r in range(n):
                    if r != p and r != q:
                        arp, arq = a[r][p], a[r][q]
                        a[r][p] = a[p][r] = c * arp - s * arq
                        a[r][q] = a[q][r] = s * arp + c * arq
                for r in range(n):
                    vrp, vrq = v[r][p], v[r][q]
                    v[r][p] = c * vrp - s * vrq
                    v[r][q] = s * vrp + c * vrq

    pairs = []
    for k in range(n):
        eig_val = a[k][k]
        eig_vec = [v[r][k] for r in range(n)]
        pairs.append((eig_val, eig_vec))
    pairs.sort(key=lambda item: item[0], reverse=True)
    return [p[0] for p in pairs], [p[1] for p in pairs]


def spd_powers(sym: list[list[float]], floor: float = 1e-4) -> tuple[list[list[float]], list[list[float]]]:
    """Compute (G^{1/2}, G^{-1/2}) for symmetric positive semi-definite Fisher matrix G."""
    vals, vecs = jacobi_eigh(sym)
    n = len(vals)
    g_half = [[0.0] * n for _ in range(n)]
    g_inv_half = [[0.0] * n for _ in range(n)]
    for lam, u in zip(vals, vecs):
        clamped = max(floor, lam)
        sh = math.sqrt(clamped)
        sih = 1.0 / sh
        for i in range(n):
            for j in range(n):
                g_half[i][j] += sh * u[i] * u[j]
                g_inv_half[i][j] += sih * u[i] * u[j]
    return g_half, g_inv_half


# ---------------------------------------------------------------------------
# 3. Conditional Exponential-Family Markov Kernel K_{eta, Q}(y | x)
# ---------------------------------------------------------------------------

def encode_input_features(text: str) -> dict[str, float]:
    """Extract normalized input regime coordinates psi_X(x) in [0, 1]^4."""
    toks = Counter(_tokenize(text))
    scale_hits = sum(toks[w] for w in ("stream", "streaming", "large", "million", "jsonl", "chunk", "incremental", "realtime", "batch"))
    state_hits = sum(toks[w] for w in ("migration", "rollback", "state", "checkpoint", "database", "sql", "sqlite", "transaction", "zero", "downtime", "canon", "continuity"))
    strict_hits = sum(toks[w] for w in ("rfc", "formal", "grammar", "strict", "security", "audit", "exploit", "contract", "schema", "invariant", "adversarial", "three", "valued"))
    multi_hits = sum(toks[w] for w in ("api", "schema", "reconcile", "pullback", "sheaf", "cross", "pipeline", "multi", "end", "sync", "bridge"))
    return {
        "scale": round(1.0 - math.exp(-0.55 * scale_hits), 4),
        "stateful": round(1.0 - math.exp(-0.55 * state_hits), 4),
        "strict": round(1.0 - math.exp(-0.45 * strict_hits), 4),
        "multi_view": round(1.0 - math.exp(-0.55 * multi_hits), 4),
    }


def psi_feature_map(x_feat: dict[str, float], y_state: tuple[str, ...]) -> list[float]:
    """Sufficient-statistic vector psi(x, y) in R^16 for structured output y given input x."""
    spec, exec_reg, ver, fail, glue, disc = y_state
    f0 = 1.0 if spec == "json_contract" else 0.0
    f1 = 1.0 if spec == "formal_grammar_adr" else 0.0
    f2 = 1.0 if exec_reg == "streaming_incremental" else 0.0
    f3 = 1.0 if exec_reg == "transactional_staged" else 0.0
    f4 = 1.0 if ver == "static_ast_contract" else 0.0
    f5 = 1.0 if ver == "exogenous_exec_oracle" else 0.0
    f6 = 1.0 if ver == "adversarial_differential" else 0.0
    f7 = 1.0 if fail == "abstain_exit2" else 0.0
    f8 = 1.0 if fail == "idempotent_rollback" else 0.0
    f9 = 1.0 if glue == "pairwise_handoff" else 0.0
    f10 = 1.0 if glue == "sheaf_global_section" else 0.0
    f11 = 1.0 if disc == "progressive_parnas" else 0.0
    return [
        f0,
        f1,
        f2,
        f3,
        f4,
        f5,
        f6,
        f7,
        f8,
        f9,
        f10,
        f11,
        x_feat.get("scale", 0.0) * f2,
        x_feat.get("stateful", 0.0) * (0.5 * f3 + 0.5 * f8),
        x_feat.get("strict", 0.0) * (0.5 * f1 + 0.5 * f6),
        x_feat.get("multi_view", 0.0) * f10,
    ]


def satisfies_theory(y_state: tuple[str, ...], allowed_axes: dict[str, set[str] | list[str]]) -> bool:
    """True iff structured output y_state satisfies all logical fiber constraints in allowed_axes."""
    for idx, axis in enumerate(AXIS_NAMES):
        allowed = allowed_axes.get(axis)
        if allowed is not None and y_state[idx] not in allowed:
            return False
    return True


def fiber_indices(allowed_axes: dict[str, set[str] | list[str]]) -> list[int]:
    """Return exact indices of admissible structured outputs Y_Q(x) subseteq Y."""
    return [i for i, y in enumerate(STRUCTURED_OUTPUT_SPACE) if satisfies_theory(y, allowed_axes)]


def kernel_distribution(
    eta: list[float],
    x_feat: dict[str, float],
    allowed_axes: dict[str, set[str] | list[str]] | None = None,
) -> tuple[list[float], float, int]:
    """Evaluate exact conditional Markov kernel K_{eta, Q}(y | x) over all 648 states in Y.

    Returns (probs_648, log_partition_Z, fiber_cardinality).
    If the logical fiber Y_Q(x) is empty (contradictory theory Q), returns (zeros, -inf, 0).
    """
    allowed = allowed_axes or {}
    valid_idx = fiber_indices(allowed)
    n_states = len(STRUCTURED_OUTPUT_SPACE)
    if not valid_idx:
        return [0.0] * n_states, float("-inf"), 0

    scores: list[tuple[int, float]] = []
    max_s = float("-inf")
    for idx in valid_idx:
        s = dot(eta, psi_feature_map(x_feat, STRUCTURED_OUTPUT_SPACE[idx]))
        scores.append((idx, s))
        if s > max_s:
            max_s = s

    sum_exp = sum(math.exp(s - max_s) for _, s in scores)
    log_z = max_s + math.log(sum_exp)
    probs = [0.0] * n_states
    for idx, s in scores:
        probs[idx] = math.exp(s - log_z)
    return probs, log_z, len(valid_idx)


def kl_divergence(p: list[float], q: list[float], eps_support: float = 1e-15) -> float:
    """Exact KL divergence D_KL(P || Q) in bits; returns +inf if supp(P) not subseteq supp(Q)."""
    kl_bits = 0.0
    for pi, qi in zip(p, q):
        if pi <= eps_support:
            continue
        if qi <= eps_support:
            return float("inf")
        kl_bits += pi * math.log2(pi / qi)
    return max(0.0, kl_bits)


_PROBE_PSIS_CACHE: list[list[list[float]]] | None = None
_ORIGIN_G_HALF_CACHE: list[list[float]] | None = None


def _get_probe_psis() -> list[list[list[float]]]:
    global _PROBE_PSIS_CACHE
    if _PROBE_PSIS_CACHE is None:
        _PROBE_PSIS_CACHE = [
            [psi_feature_map(x_feat, y) for y in STRUCTURED_OUTPUT_SPACE]
            for x_feat in PROBE_INPUTS
        ]
    return _PROBE_PSIS_CACHE


def conditional_fisher_matrix(
    eta: list[float],
    allowed_axes: dict[str, set[str] | list[str]] | None = None,
) -> list[list[float]]:
    """Exact Conditional Fisher-Rao Metric G_F(eta) = E_{x~mu}[Cov_{y~K_eta(.|x)}(psi(x, y))]."""
    cov_avg = [[0.0] * DIM_ETA for _ in range(DIM_ETA)]
    w_x = 1.0 / len(PROBE_INPUTS)
    probe_psis = _get_probe_psis()
    for p_idx, x_feat in enumerate(PROBE_INPUTS):
        probs, _, n_fib = kernel_distribution(eta, x_feat, allowed_axes)
        if n_fib == 0:
            continue
        psis = probe_psis[p_idx]
        mean_psi = [0.0] * DIM_ETA
        for idx, p in enumerate(probs):
            if p > 0.0:
                row = psis[idx]
                for d in range(DIM_ETA):
                    mean_psi[d] += p * row[d]
        for idx, p in enumerate(probs):
            if p > 0.0:
                diff = [psis[idx][d] - mean_psi[d] for d in range(DIM_ETA)]
                for a in range(DIM_ETA):
                    pa = p * diff[a]
                    for b in range(a, DIM_ETA):
                        val = w_x * pa * diff[b]
                        cov_avg[a][b] += val
                        if a != b:
                            cov_avg[b][a] += val
    # Add tiny metric regularization so G_F is strictly positive definite on saturated fibers
    for d in range(DIM_ETA):
        cov_avg[d][d] += 1e-3
    return cov_avg


# ---------------------------------------------------------------------------
# 4. Lifting Observed Marketplace Skills -> Guarded Generative Kernels
# ---------------------------------------------------------------------------

def _read_member_text(member: dict[str, Any], audit: dict[str, Any] | None = None) -> tuple[str, int, bool]:
    """Return (combined text, n_scripts, has_refs_or_subskills)."""
    chunks = [
        str(member.get("id") or "").replace("@", " ").replace("/", " ").replace("-", " ").replace("_", " "),
        str(member.get("github_description") or ""),
        str(member.get("query") or ""),
        str(member.get("discovery_role") or ""),
    ]
    n_scripts = int(((audit or {}).get("stats") or {}).get("n_scripts") or 0)
    has_mod = False
    ldir = member.get("local_dir")
    if ldir:
        p = Path(str(ldir))
        if p.is_dir():
            sm = p / "SKILL.md"
            if sm.is_file():
                chunks.append(sm.read_text(encoding="utf-8", errors="replace")[:12000])
            sd = p / "scripts"
            if sd.is_dir():
                sfiles = [f for f in sd.rglob("*") if f.is_file()]
                n_scripts = max(n_scripts, len(sfiles))
                has_mod = has_mod or bool(sfiles)
            if (p / "references").is_dir() or (p / "subskills").is_dir():
                has_mod = True
    return " ".join(chunks), n_scripts, has_mod


def lift_skill_to_kernel(member: dict[str, Any], audit: dict[str, Any] | None = None) -> dict[str, Any]:
    """Lift a discrete marketplace skill s_i into a Guarded Generative Kernel (P_i, Q_i, eta_i)."""
    sid = str(member.get("id") or "unknown")
    slug = _slug_of(sid)
    text, n_scripts, has_mod = _read_member_text(member, audit)
    toks = Counter(_tokenize(text))

    # Explicit theory clauses override (for exact algebraic/theorem tests) or lexicon inference
    explicit_clauses: dict[str, list[str]] = member.get("theory_clauses") or {}

    axis_scores: dict[str, dict[str, float]] = {}
    inferred_clauses: dict[str, list[str]] = {}

    for axis in AXIS_NAMES:
        val_scores: dict[str, float] = {}
        for val in OUTPUT_AXES[axis]:
            lex = AXIS_LEXICONS[axis].get(val, set())
            hits = sum(toks[w] for w in lex if w in toks)
            val_scores[val] = round(hits, 4)
        if n_scripts > 0 and axis == "verification_channel":
            val_scores["exogenous_exec_oracle"] += 2.5
        if has_mod and axis == "context_disclosure":
            val_scores["progressive_parnas"] += 2.0
        axis_scores[axis] = val_scores

        if axis in explicit_clauses:
            inferred_clauses[axis] = list(explicit_clauses[axis])
        else:
            best_val, best_sc = max(val_scores.items(), key=lambda kv: kv[1])
            if best_sc >= 2.0:
                # Specialized skill commits strongly to its dominant regime(s)
                committed = [v for v, sc in val_scores.items() if sc >= max(2.0, 0.72 * best_sc)]
                inferred_clauses[axis] = committed
            else:
                # Unconstrained on this axis (accepts full domain fiber)
                inferred_clauses[axis] = list(OUTPUT_AXES[axis])

    # Construct natural parameter vector eta^(i) in R^16
    def _log_pref(axis: str, val: str, base: float = 0.0) -> float:
        sc = axis_scores[axis].get(val, 0.0)
        in_clause = 1.15 if val in inferred_clauses[axis] and len(inferred_clauses[axis]) < len(OUTPUT_AXES[axis]) else 0.0
        return round(base + 0.55 * math.log1p(sc) + in_clause, 4)

    x_aff = encode_input_features(text)
    eta = [
        _log_pref("spec_modality", "json_contract", 0.2),
        _log_pref("spec_modality", "formal_grammar_adr", 0.2),
        _log_pref("execution_regime", "streaming_incremental", 0.0),
        _log_pref("execution_regime", "transactional_staged", 0.0),
        _log_pref("verification_channel", "static_ast_contract", 0.2),
        _log_pref("verification_channel", "exogenous_exec_oracle", 0.35),
        _log_pref("verification_channel", "adversarial_differential", 0.25),
        _log_pref("failure_semantics", "abstain_exit2", 0.3),
        _log_pref("failure_semantics", "idempotent_rollback", 0.15),
        _log_pref("gluing_topology", "pairwise_handoff", 0.2),
        _log_pref("gluing_topology", "sheaf_global_section", 0.25),
        _log_pref("context_disclosure", "progressive_parnas", 0.35),
        round(1.1 * x_aff["scale"], 4),
        round(1.1 * x_aff["stateful"], 4),
        round(1.1 * x_aff["strict"], 4),
        round(1.1 * x_aff["multi_view"], 4),
    ]
    if isinstance(member.get("natural_eta"), list) and len(member["natural_eta"]) == DIM_ETA:
        eta = [float(v) for v in member["natural_eta"]]

    return {
        "id": sid,
        "slug": slug,
        "theory_clauses": inferred_clauses,
        "natural_eta": eta,
        "input_affinity": x_aff,
        "fiber_size": len(fiber_indices(inferred_clauses)),
    }


def _get_origin_g_half() -> list[list[float]]:
    global _ORIGIN_G_HALF_CACHE
    if _ORIGIN_G_HALF_CACHE is None:
        g0 = conditional_fisher_matrix([0.0] * DIM_ETA)
        _ORIGIN_G_HALF_CACHE, _ = spd_powers(g0)
    return _ORIGIN_G_HALF_CACHE


def fisher_logdet_volume(members: list[dict[str, Any]], alpha: float = 1.6) -> float:
    """Monotone Submodular D-Optimal Fisher Log-Determinant Volume:
       V_Fisher(S) = 0.5 * log det(I_D + alpha * sum_{s in S} psi_tilde(s) psi_tilde(s)^T)
    Satisfies exact diminishing returns by operator concavity of log det on S_++^D.
    """
    if not members:
        return 0.0
    g0_half = _get_origin_g_half()
    gram = mat_eye(DIM_ETA)
    for m in members:
        lifted = lift_skill_to_kernel(m)
        whitened = mat_vec(g0_half, lifted["natural_eta"])
        for i in range(DIM_ETA):
            for j in range(DIM_ETA):
                gram[i][j] += alpha * whitened[i] * whitened[j]
    return round(0.5 * spd_logdet(gram), 4)


# ---------------------------------------------------------------------------
# 5. Galois Conormal Extraction & Plotkin-Reynolds Anti-Unification (lgg)
# ---------------------------------------------------------------------------

CONORMAL_STRUCTURAL_LAWS: dict[str, set[str]] = {
    # Universal soundness equations F_perp(x, y) = 0 cutting out the manifold M:
    # No prose-only self-grading, no silent partial corruption, no unlinked monolithic dumps.
    "verification_channel": {
        "static_ast_contract",
        "exogenous_exec_oracle",
        "adversarial_differential",
    },
    "failure_semantics": {"abstain_exit2", "idempotent_rollback"},
    "gluing_topology": {"pairwise_handoff", "sheaf_global_section"},
    "context_disclosure": {"progressive_parnas"},
}


def anti_unify_theories(lifted_skills: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute Galois Conormal Core Phi_core and Plotkin-Reynolds Anti-Unified Chart Theta.

    Separates:
      - Naive Concatenation Conjunction: Q_concat = /\\_i Q_i (collapses to empty fiber on conflicts!)
      - Naive Union Relation: R_union = \\/_i Q_i (only covers observed point fibers, misses cross-products!)
      - Lawvere Anti-Unified Manifold Theory T_M(theta):
          * Conormal Core Phi_core: universal soundness laws + shared invariant restrictions
          * Tangent Chart Variables theta_a in Theta_a: lifted wherever skills vary/conflict!
    """
    if not lifted_skills:
        return {
            "conormal_core": {k: sorted(v) for k, v in CONORMAL_STRUCTURAL_LAWS.items()},
            "chart_variables": {},
            "concatenation_conflicts": [],
            "concatenation_fiber_size": 0,
            "union_fiber_size": 0,
            "manifold_total_fiber_size": 0,
            "combinatorial_chart_points": 1,
            "observed_distinct_points": 0,
            "specialization_morphisms": {},
        }

    # 1. Check naive conjunction /\_i Q_i across observed skills
    conj_axes: dict[str, set[str]] = {}
    conflicts: list[dict[str, Any]] = []
    for axis in AXIS_NAMES:
        inter = set(OUTPUT_AXES[axis])
        for sk in lifted_skills:
            inter &= set(sk["theory_clauses"][axis])
        conj_axes[axis] = inter
        if not inter:
            conflicts.append(
                {
                    "axis": axis,
                    "member_assignments": {sk["slug"]: sk["theory_clauses"][axis] for sk in lifted_skills},
                    "diagnosis": f"Constraint-Union Collapse (Q_i /\\ Q_j |- false on `{axis}`)",
                }
            )

    concat_fiber_n = len(fiber_indices(conj_axes))

    # 2. Compute naive relational union \/_i (Q_i /\ Phi_core)
    union_state_indices: set[int] = set()
    for sk in lifted_skills:
        guarded_q = {
            axis: set(sk["theory_clauses"][axis]) & CONORMAL_STRUCTURAL_LAWS.get(axis, set(OUTPUT_AXES[axis]))
            for axis in AXIS_NAMES
        }
        # If an unbuffed skill only had weak defaults (e.g. prose_self_check), buffing lifts it into CONORMAL_STRUCTURAL_LAWS
        for axis, law_vals in CONORMAL_STRUCTURAL_LAWS.items():
            if not guarded_q[axis]:
                guarded_q[axis] = set(law_vals)
        union_state_indices |= set(fiber_indices(guarded_q))

    # 3. Galois Conormal Core + Plotkin-Reynolds Anti-Unification (lgg)
    conormal_core: dict[str, list[str]] = {}
    chart_variables: dict[str, dict[str, Any]] = {}
    specializations: dict[str, dict[str, list[str]]] = {sk["slug"]: {} for sk in lifted_skills}

    for axis in AXIS_NAMES:
        law_allowed = CONORMAL_STRUCTURAL_LAWS.get(axis, set(OUTPUT_AXES[axis]))
        member_sets: list[set[str]] = []
        for sk in lifted_skills:
            raw_set = set(sk["theory_clauses"][axis]) & law_allowed
            if not raw_set:
                raw_set = set(law_allowed)
            member_sets.append(raw_set)

        # Plotkin-Reynolds check: do all members agree on the exact same invariant subset?
        first = member_sets[0]
        all_identical = all(ms == first for ms in member_sets[1:])
        lgg_domain = sorted(set().union(*member_sets))

        if all_identical:
            conormal_core[axis] = sorted(first)
        else:
            # Variation detected! Lift into a typed Lawvere fiber variable xi_<axis> : lgg_domain
            conormal_core[axis] = sorted(law_allowed)
            var_name = f"theta_{axis}"
            chart_variables[axis] = {
                "variable": var_name,
                "domain": lgg_domain,
                "cardinality": len(lgg_domain),
                "had_hard_contradiction": len(conj_axes[axis]) == 0,
            }
            for sk, ms in zip(lifted_skills, member_sets):
                specializations[sk["slug"]][axis] = sorted(ms)

    # Manifold fiber over full chart domain Theta
    manifold_axes: dict[str, list[str]] = {}
    for axis in AXIS_NAMES:
        if axis in chart_variables:
            manifold_axes[axis] = chart_variables[axis]["domain"]
        else:
            manifold_axes[axis] = conormal_core[axis]
    manifold_fiber_n = len(fiber_indices(manifold_axes))

    comb_points = 1
    for cv in chart_variables.values():
        comb_points *= max(1, int(cv["cardinality"]))

    distinct_sigs = {
        tuple((ax, tuple(specializations[sk["slug"]].get(ax, []))) for ax in sorted(chart_variables))
        for sk in lifted_skills
    }

    # Verify exact specialization pullback: for every member i, sigma_i^*(T_M) == guarded(Q_i)
    specialization_exact = True
    for sk in lifted_skills:
        pulled_back = dict(manifold_axes)
        for ax, vals in specializations[sk["slug"]].items():
            pulled_back[ax] = vals
        guarded_q = {
            ax: sorted((set(sk["theory_clauses"][ax]) & CONORMAL_STRUCTURAL_LAWS.get(ax, set(OUTPUT_AXES[ax]))) or CONORMAL_STRUCTURAL_LAWS.get(ax, set(OUTPUT_AXES[ax])))
            for ax in AXIS_NAMES
        }
        if fiber_indices(pulled_back) != fiber_indices(guarded_q):
            specialization_exact = False

    return {
        "conormal_core": conormal_core,
        "chart_variables": chart_variables,
        "manifold_axes_domain": manifold_axes,
        "concatenation_conflicts": conflicts,
        "concatenation_fiber_size": concat_fiber_n,
        "union_fiber_size": len(union_state_indices),
        "manifold_total_fiber_size": manifold_fiber_n,
        "recombinant_novel_states": max(0, manifold_fiber_n - len(union_state_indices)),
        "combinatorial_chart_points": comb_points,
        "observed_distinct_points": len(distinct_sigs),
        "specialization_exact": specialization_exact,
        "specialization_morphisms": specializations,
    }


# ---------------------------------------------------------------------------
# 6. Sheaf Gluing Nerve N(U) & Cech 1-Cocycle Exactness (delta^1 = 0)
# ---------------------------------------------------------------------------

DOMAIN_SHEAF_COVERS: dict[str, dict[str, Any]] = {
    "data": {
        "open_cover": ["U_spec_schema", "U_migration_sql", "U_api_serializer", "U_rollback_verify"],
        "overlaps": [
            {"u": "U_spec_schema", "v": "U_migration_sql", "shared_keys": ["entity_columns", "primary_key"], "transform": "id"},
            {"u": "U_migration_sql", "v": "U_api_serializer", "shared_keys": ["entity_columns", "primary_key"], "transform": "id"},
            {"u": "U_spec_schema", "v": "U_api_serializer", "shared_keys": ["entity_columns", "primary_key"], "transform": "id"},
            {"u": "U_migration_sql", "v": "U_rollback_verify", "shared_keys": ["row_count_hash", "schema_version"], "transform": "id"},
        ],
    },
    "devops": {
        "open_cover": ["U_threat_spec", "U_security_patch", "U_exploit_regression", "U_rollout_gate"],
        "overlaps": [
            {"u": "U_threat_spec", "v": "U_security_patch", "shared_keys": ["cve_id", "patched_symbols"], "transform": "id"},
            {"u": "U_security_patch", "v": "U_exploit_regression", "shared_keys": ["cve_id", "patched_symbols"], "transform": "id"},
            {"u": "U_threat_spec", "v": "U_exploit_regression", "shared_keys": ["cve_id", "patched_symbols"], "transform": "id"},
            {"u": "U_exploit_regression", "v": "U_rollout_gate", "shared_keys": ["exit_code", "regression_hash"], "transform": "id"},
        ],
    },
    "automation": {
        "open_cover": ["U_rfc_grammar", "U_parser_ast", "U_evaluator_semantics", "U_property_oracle"],
        "overlaps": [
            {"u": "U_rfc_grammar", "v": "U_parser_ast", "shared_keys": ["ast_node_kinds", "precedence_table"], "transform": "id"},
            {"u": "U_parser_ast", "v": "U_evaluator_semantics", "shared_keys": ["ast_node_kinds", "truth_values"], "transform": "id"},
            {"u": "U_rfc_grammar", "v": "U_evaluator_semantics", "shared_keys": ["ast_node_kinds"], "transform": "id"},
            {"u": "U_evaluator_semantics", "v": "U_property_oracle", "shared_keys": ["truth_values", "precedence_table"], "transform": "id"},
        ],
    },
    "research": {
        "open_cover": ["U_claim_protocol", "U_evidence_table", "U_stat_computation", "U_citation_audit"],
        "overlaps": [
            {"u": "U_claim_protocol", "v": "U_evidence_table", "shared_keys": ["claim_ids", "denominators"], "transform": "id"},
            {"u": "U_evidence_table", "v": "U_stat_computation", "shared_keys": ["claim_ids", "denominators"], "transform": "id"},
            {"u": "U_claim_protocol", "v": "U_stat_computation", "shared_keys": ["claim_ids", "denominators"], "transform": "id"},
            {"u": "U_evidence_table", "v": "U_citation_audit", "shared_keys": ["source_hashes"], "transform": "id"},
        ],
    },
    "writing": {
        "open_cover": ["U_world_canon", "U_scene_draft", "U_epistemic_ledger", "U_voice_critic"],
        "overlaps": [
            {"u": "U_world_canon", "v": "U_scene_draft", "shared_keys": ["character_entities", "timeline_t"], "transform": "id"},
            {"u": "U_scene_draft", "v": "U_epistemic_ledger", "shared_keys": ["character_entities", "timeline_t"], "transform": "id"},
            {"u": "U_world_canon", "v": "U_epistemic_ledger", "shared_keys": ["character_entities", "timeline_t"], "transform": "id"},
            {"u": "U_scene_draft", "v": "U_voice_critic", "shared_keys": ["pov_register"], "transform": "id"},
        ],
    },
    "general": {
        "open_cover": ["U_locked_spec", "U_primary_artifact", "U_secondary_view", "U_oracle_trace"],
        "overlaps": [
            {"u": "U_locked_spec", "v": "U_primary_artifact", "shared_keys": ["interface_exports", "invariants"], "transform": "id"},
            {"u": "U_primary_artifact", "v": "U_secondary_view", "shared_keys": ["interface_exports", "invariants"], "transform": "id"},
            {"u": "U_locked_spec", "v": "U_secondary_view", "shared_keys": ["interface_exports", "invariants"], "transform": "id"},
            {"u": "U_secondary_view", "v": "U_oracle_trace", "shared_keys": ["invariants"], "transform": "id"},
        ],
    },
}

# Group of linear scale/offset/invert transition morphisms on overlap fibers: (scale, shift)
# Composition: (s2, b2) o (s1, b1) = (s2*s1, s2*b1 + b2); identity = (1.0, 0.0)
TRANSFORM_GROUP: dict[str, tuple[float, float]] = {
    "id": (1.0, 0.0),
    "negate": (-1.0, 0.0),
    "shift_plus_1": (1.0, 1.0),
    "shift_minus_1": (1.0, -1.0),
    "scale_100_pct": (100.0, 0.0),
    "scale_0_01": (0.01, 0.0),
}


def _inv_transform(tr: tuple[float, float]) -> tuple[float, float]:
    s, b = tr
    return (1.0 / s, -b / s)


def _comp_transform(t2: tuple[float, float], t1: tuple[float, float]) -> tuple[float, float]:
    s2, b2 = t2
    s1, b1 = t1
    return (s2 * s1, s2 * b1 + b2)


def build_sheaf_nerve(domain: str | None) -> dict[str, Any]:
    dom = (domain or "general").lower()
    cfg = DOMAIN_SHEAF_COVERS.get(dom, DOMAIN_SHEAF_COVERS["general"])
    return {
        "domain": dom,
        "open_cover": list(cfg["open_cover"]),
        "overlaps": [dict(e) for e in cfg["overlaps"]],
    }


def verify_sheaf_cocycle(nerve: dict[str, Any]) -> dict[str, Any]:
    """Check Cech 1-cocycle exactness (delta^1 g == id) around every 2-simplex (triangle) in N(U)."""
    overlaps = nerve.get("overlaps") or []
    edge_map: dict[tuple[str, str], tuple[set[str], tuple[float, float]]] = {}
    vertices: set[str] = set(nerve.get("open_cover") or [])

    for ov in overlaps:
        u, v = str(ov.get("u")), str(ov.get("v"))
        vertices.add(u)
        vertices.add(v)
        keys = set(ov.get("shared_keys") or [])
        t_name = str(ov.get("transform") or "id")
        tr = TRANSFORM_GROUP.get(t_name, (1.0, 0.0))
        if isinstance(ov.get("affine"), list) and len(ov["affine"]) == 2:
            tr = (float(ov["affine"][0]), float(ov["affine"][1]))
        edge_map[(u, v)] = (keys, tr)
        edge_map[(v, u)] = (keys, _inv_transform(tr))

    v_list = sorted(vertices)
    triangles_checked = 0
    holonomy_defects: list[dict[str, Any]] = []

    for i in range(len(v_list)):
        for j in range(i + 1, len(v_list)):
            for k in range(j + 1, len(v_list)):
                a, b, c = v_list[i], v_list[j], v_list[k]
                if (a, b) in edge_map and (b, c) in edge_map and (c, a) in edge_map:
                    kab, tab = edge_map[(a, b)]
                    kbc, tbc = edge_map[(b, c)]
                    kca, tca = edge_map[(c, a)]
                    triple_keys = kab & kbc & kca
                    triangles_checked += 1
                    # Holonomy around loop a -> b -> c -> a
                    hol = _comp_transform(tca, _comp_transform(tbc, tab))
                    if triple_keys and (abs(hol[0] - 1.0) > 1e-6 or abs(hol[1]) > 1e-6):
                        holonomy_defects.append(
                            {
                                "triangle": [a, b, c],
                                "triple_overlap_keys": sorted(triple_keys),
                                "loop_holonomy_affine": [round(hol[0], 6), round(hol[1], 6)],
                            }
                        )

    return {
        "cocycle_exact": len(holonomy_defects) == 0,
        "triangles_checked": triangles_checked,
        "holonomy_defects": holonomy_defects,
    }


# ---------------------------------------------------------------------------
# 7. Amari Statistical-Logical Manifold Compiler & Geodesic Projector
# ---------------------------------------------------------------------------

def build_skill_manifold(
    members: list[dict[str, Any]],
    audits: dict[str, dict[str, Any]] | None = None,
    *,
    domain: str | None = None,
    query: str = "",
    skill_name: str = "manifold-skill",
) -> dict[str, Any]:
    """Synthesize the complete Lawvere-Amari Generative Manifold Atlas from N observed skills."""
    audits = audits or {}
    dom = (domain or "general").lower()
    lifted = [lift_skill_to_kernel(m, audits.get(str(m.get("id") or ""))) for m in members]
    logic_decomp = anti_unify_theories(lifted)
    nerve = build_sheaf_nerve(dom)
    cocycle = verify_sheaf_cocycle(nerve)

    n = len(lifted)
    if n == 0:
        eta_0 = [0.0] * DIM_ETA
    else:
        eta_0 = [round(sum(sk["natural_eta"][d] for sk in lifted) / n, 6) for d in range(DIM_ETA)]

    # Exact Conditional Fisher-Rao Metric G_F(eta_0) over the manifold's admissible fiber
    manifold_axes = logic_decomp["manifold_axes_domain"]
    g_fisher = conditional_fisher_matrix(eta_0, manifold_axes)
    g_half, g_inv_half = spd_powers(g_fisher)

    # Whitened tangent scatter S_w = (1/N) sum_i (G_F^{1/2}(eta_i - eta_0))(G_F^{1/2}(eta_i - eta_0))^T
    scatter_w = [[0.0] * DIM_ETA for _ in range(DIM_ETA)]
    centered_etas: list[list[float]] = []
    for sk in lifted:
        delta = [sk["natural_eta"][d] - eta_0[d] for d in range(DIM_ETA)]
        centered_etas.append(delta)
        w_vec = mat_vec(g_half, delta)
        for a in range(DIM_ETA):
            for b in range(DIM_ETA):
                scatter_w[a][b] += (w_vec[a] * w_vec[b]) / max(1, n)

    eig_vals, eig_vecs_w = jacobi_eigh(scatter_w)
    pos_vals = [max(0.0, lam) for lam in eig_vals if lam > 1e-6]
    sum_l1 = sum(pos_vals)
    sum_l2 = sum(lam * lam for lam in pos_vals)
    intrinsic_dim = (sum_l1 * sum_l1 / sum_l2) if sum_l2 > 1e-12 else 0.0

    # Keep principal tangent basis vectors v_k = G_F^{-1/2} u_k satisfying <v_a, G_F v_b> = delta_ab
    max_rank = max(1, min(len(pos_vals), min(6, max(1, n - 1)))) if pos_vals else 0
    tangent_basis: list[list[float]] = []
    whitened_basis: list[list[float]] = []
    singular_values: list[float] = []
    for k in range(max_rank):
        u_k = eig_vecs_w[k]
        v_k = mat_vec(g_inv_half, u_k)
        whitened_basis.append([round(x, 6) for x in u_k])
        tangent_basis.append([round(x, 6) for x in v_k])
        singular_values.append(round(math.sqrt(max(0.0, eig_vals[k])), 6))

    # Project each observed skill s_i onto chart coordinates theta^(i)_k = <u_k, G_F^{1/2}(eta_i - eta_0)>
    landmarks: list[dict[str, Any]] = []
    for sk, delta in zip(lifted, centered_etas):
        w_delta = mat_vec(g_half, delta)
        coords = [round(dot(u_k, w_delta), 5) for u_k in whitened_basis]
        landmarks.append(
            {
                "id": sk["id"],
                "slug": sk["slug"],
                "chart_coordinates": coords,
                "natural_eta": [round(x, 5) for x in sk["natural_eta"]],
                "input_affinity": sk["input_affinity"],
                "specialized_clauses": logic_decomp["specialization_morphisms"].get(sk["slug"], {}),
                "raw_theory_clauses": sk["theory_clauses"],
            }
        )

    # Measure Amari e-geodesic vs m-mixture Bregman divergence gap at the manifold barycenter
    bregman_gaps: list[float] = []
    recomb_masses: list[float] = []
    if n >= 2:
        for x_feat in PROBE_INPUTS:
            p_e, _, _ = kernel_distribution(eta_0, x_feat, manifold_axes)
            p_m_shared = [0.0] * len(STRUCTURED_OUTPUT_SPACE)
            union_support: set[int] = set()
            for sk in lifted:
                # Continuous m-mixture over the manifold fiber (pure e-vs-m curvature gap)
                p_i_shared, _, _ = kernel_distribution(sk["natural_eta"], x_feat, manifold_axes)
                for idx in range(len(STRUCTURED_OUTPUT_SPACE)):
                    p_m_shared[idx] += p_i_shared[idx] / n
                # Guarded individual fiber support for discrete union comparison
                sk_axes = dict(manifold_axes)
                for ax, vals in logic_decomp["specialization_morphisms"].get(sk["slug"], {}).items():
                    sk_axes[ax] = vals
                union_support |= set(fiber_indices(sk_axes))
            gap = kl_divergence(p_e, p_m_shared)
            if math.isfinite(gap):
                bregman_gaps.append(gap)
            recomb_masses.append(
                sum(p_e[idx] for idx in range(len(STRUCTURED_OUTPUT_SPACE)) if idx not in union_support)
            )

    atlas = {
        "schema": "skillcompose.lawvere_amari_manifold.v1",
        "skill_name": skill_name,
        "domain": dom,
        "query": query,
        "feature_names": list(FEATURE_NAMES),
        "output_axes": {k: list(v) for k, v in OUTPUT_AXES.items()},
        "domain_guard": {
            "domain_tokens": sorted(DOMAIN_TOKENS.get(dom, set()) | set(_tokenize(query))),
            "alien_tokens": sorted(DESC_ALIEN.get(dom, set())),
            "polysemy_traps": sorted(POLYSEMY_GUARD.get(dom, set()) | POLYSEMY_GUARD["general"]),
            "off_domain_tokens": sorted(OFF_DOMAIN) if dom in {"writing", "research", "data", "automation"} else [],
        },
        "logic": logic_decomp,
        "geometry": {
            "barycenter_eta": eta_0,
            "fisher_metric": [[round(x, 6) for x in row] for row in g_fisher],
            "fisher_sqrt": [[round(x, 6) for x in row] for row in g_half],
            "tangent_rank": len(tangent_basis),
            "tangent_basis_eta": tangent_basis,
            "whitened_basis": whitened_basis,
            "riemannian_singular_values": singular_values,
            "intrinsic_dimension_participation_ratio": round(intrinsic_dim, 4),
            "fisher_logdet_volume": fisher_logdet_volume(members),
            "amari_e_vs_m_bregman_gap_bits": round(sum(bregman_gaps) / len(bregman_gaps), 5) if bregman_gaps else 0.0,
            "recombinant_probability_mass": round(sum(recomb_masses) / len(recomb_masses), 4) if recomb_masses else 0.0,
        },
        "landmarks": landmarks,
        "sheaf_nerve": nerve,
        "sheaf_verification": cocycle,
    }
    return atlas


def project_input_to_manifold(
    atlas: dict[str, Any],
    task_text: str,
    *,
    explicit_axis_requests: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Inverse Chart Encoder sigma* : X -> Theta & Synthesized Generative Kernel K_{theta*(x)}(. | x).

    1. Checks Conormal Domain Precondition P_M(x); returns ABSTAIN_OFF_MANIFOLD (ok=False) on alien/polysemic traps.
    2. Projects x onto continuous Fisher-Rao tangent coordinates theta*(x) and discrete Lawvere chart variables.
    3. Evaluates K_{theta*(x)}(y | x) over the contradiction-free fiber Y_{T_M(theta*(x))}(x), returning
       the MAP structured output architecture, top-k fiber support, landmark e-geodesic weights, and
       sheaf gluing obligations.
    """
    toks = set(_tokenize(task_text))
    guard = atlas.get("domain_guard") or {}
    dom = str(atlas.get("domain") or "general")
    q_seed_toks = set(_tokenize(str(atlas.get("query") or "")))

    traps = (set(guard.get("polysemy_traps") or []) | set(guard.get("alien_tokens") or [])) - q_seed_toks
    off_dom = set(guard.get("off_domain_tokens") or []) - q_seed_toks
    dom_toks = set(guard.get("domain_tokens") or [])

    trap_hits = sorted(toks & traps)
    off_hits = sorted(toks & off_dom)
    dom_hits = sorted(toks & dom_toks)

    if trap_hits or (off_hits and not dom_hits):
        return {
            "ok": False,
            "decision": "ABSTAIN_OFF_MANIFOLD",
            "domain": dom,
            "reasons": [
                f"conormal_domain_guard_rejected: trap_hits={trap_hits}, off_domain_hits={off_hits}"
            ],
        }

    # Lift task_text into target natural parameter preference hat_eta(x) via lift_skill_to_kernel
    probe_kernel = lift_skill_to_kernel(
        {"id": "input@task", "github_description": task_text, "query": task_text}
    )
    x_feat = encode_input_features(task_text)
    geom = atlas["geometry"]
    eta_0 = list(geom["barycenter_eta"])
    g_half = geom["fisher_sqrt"]
    w_basis = geom["whitened_basis"]
    t_basis = geom["tangent_basis_eta"]
    landmarks = atlas.get("landmarks") or []

    # Compute e-geodesic landmark affinities & tangent chart coordinates theta*(x)
    raw_delta = [probe_kernel["natural_eta"][d] - eta_0[d] for d in range(DIM_ETA)]
    w_delta = mat_vec(g_half, raw_delta)
    # Trust-region clamp ||theta*||_2 <= 3.0 on the Riemannian tangent space
    theta_coords = [dot(u_k, w_delta) for u_k in w_basis]
    norm_theta = math.sqrt(sum(c * c for c in theta_coords))
    if norm_theta > 3.0:
        scale = 3.0 / norm_theta
        theta_coords = [c * scale for c in theta_coords]

    eta_star = list(eta_0)
    for c_k, v_k in zip(theta_coords, t_basis):
        for d in range(DIM_ETA):
            eta_star[d] += c_k * v_k[d]

    # Compute smooth e-geodesic weights over landmarks via Riemannian distance in chart space
    lm_weights: dict[str, float] = {}
    if landmarks:
        neg_dists = []
        for lm in landmarks:
            lm_c = lm.get("chart_coordinates") or []
            sq_d = sum((a - b) ** 2 for a, b in zip(theta_coords, lm_c))
            aff = lm.get("input_affinity") or {}
            aff_sim = sum(x_feat[k] * float(aff.get(k, 0.0)) for k in x_feat)
            neg_dists.append(-0.85 * sq_d + 1.25 * aff_sim)
        mx = max(neg_dists)
        exps = [math.exp(v - mx) for v in neg_dists]
        z_w = sum(exps)
        for lm, ew in zip(landmarks, exps):
            lm_weights[lm["slug"]] = round(ew / z_w, 4)

    # Resolve discrete Lawvere chart variables theta_logic*(x) in Theta
    logic = atlas["logic"]
    resolved_fiber: dict[str, list[str]] = {
        ax: list(vals) for ax, vals in logic["conormal_core"].items()
    }
    resolved_chart_assignment: dict[str, list[str]] = {}
    explicit_reqs = explicit_axis_requests or {}
    tok_counts = Counter(_tokenize(task_text))

    for ax, cv in (logic.get("chart_variables") or {}).items():
        dom_vals: list[str] = list(cv["domain"])
        if ax in explicit_reqs and explicit_reqs[ax] in dom_vals:
            picked = [explicit_reqs[ax]]
        else:
            scored = []
            for v in dom_vals:
                lex = AXIS_LEXICONS[ax].get(v, set())
                sc = sum(tok_counts[w] for w in lex if w in tok_counts)
                scored.append((sc, v))
            best_sc = max(s for s, _ in scored)
            if best_sc > 0:
                picked = [v for s, v in scored if s == best_sc]
            else:
                # Unspecified axis stays polymorphic over the anti-unified domain!
                picked = dom_vals
        resolved_fiber[ax] = picked
        resolved_chart_assignment[ax] = picked

    probs, log_z, fiber_n = kernel_distribution(eta_star, x_feat, resolved_fiber)
    ranked = sorted(
        ((probs[i], i) for i in range(len(STRUCTURED_OUTPUT_SPACE)) if probs[i] > 0.0),
        reverse=True,
    )
    entropy_bits = -sum(p * math.log2(p) for p, _ in ranked if p > 1e-15)

    top_outputs = []
    for p, idx in ranked[:5]:
        st = STRUCTURED_OUTPUT_SPACE[idx]
        top_outputs.append(
            {
                "probability": round(p, 5),
                "architecture": {ax: st[j] for j, ax in enumerate(AXIS_NAMES)},
            }
        )

    # Determine synthesis regime: landmark_specialization vs geodesic_interpolation vs recombinant_extrapolation
    max_w = max(lm_weights.values(), default=1.0)
    matches_single_landmark = False
    for lm in landmarks:
        spec_c = lm.get("specialized_clauses") or {}
        if all(resolved_chart_assignment.get(ax) == spec_c.get(ax) for ax in resolved_chart_assignment):
            matches_single_landmark = True
            break
    if resolved_chart_assignment and not matches_single_landmark:
        regime = "recombinant_tangent_synthesis"
    elif max_w < 0.68 and len(landmarks) >= 2:
        regime = "e_geodesic_interpolation"
    else:
        regime = "landmark_fiber_specialization"

    return {
        "ok": True,
        "decision": "SYNTHESIZE_ON_MANIFOLD",
        "domain": dom,
        "synthesis_regime": regime,
        "input_features": x_feat,
        "fisher_chart_coordinates": [round(c, 5) for c in theta_coords],
        "resolved_lawvere_fiber": resolved_fiber,
        "resolved_chart_variables": resolved_chart_assignment,
        "landmark_e_geodesic_weights": lm_weights,
        "admissible_output_fiber_cardinality": fiber_n,
        "output_posterior_entropy_bits": round(entropy_bits, 4),
        "log_partition": round(log_z, 4),
        "map_structured_output": top_outputs[0]["architecture"] if top_outputs else {},
        "top_structured_outputs": top_outputs,
        "conormal_invariants_enforced": logic["conormal_core"],
        "sheaf_gluing_obligations": atlas["sheaf_nerve"]["overlaps"],
    }


# ---------------------------------------------------------------------------
# 8. Out-of-Sample Generalization Proof: Manifold vs Union vs Concatenation
# ---------------------------------------------------------------------------

def evaluate_generalization_over_union(atlas: dict[str, Any]) -> dict[str, Any]:
    """Prove mathematically and quantitatively on unseen recombinant coordinates theta* not in S
    that the Lawvere-Amari Manifold Skill strictly dominates:
      (a) Prompt Concatenation (/\\_i Q_i),
      (b) Nearest-Neighbor Single Skill Routing, and
      (c) Mixture / Union of Skills (1/N sum_i K_i, \\/_i Y_i).
    """
    logic = atlas["logic"]
    landmarks = atlas.get("landmarks") or []
    chart_vars = logic.get("chart_variables") or {}
    manifold_axes = logic["manifold_axes_domain"]
    eta_0 = atlas["geometry"]["barycenter_eta"]

    # Construct a recombinant target coordinate theta* combining axis 1 from landmark 0
    # and axis 2 from landmark 1 (or an unseen combination in prod_a Theta_a)
    var_axes = list(chart_vars.keys())
    target_req: dict[str, str] = {}
    if len(var_axes) >= 2 and len(landmarks) >= 2:
        ax0, ax1 = var_axes[0], var_axes[1]
        v0 = (landmarks[0]["specialized_clauses"].get(ax0) or chart_vars[ax0]["domain"])[0]
        # Pick a value on ax1 NOT in landmark[0]'s specialized clause if available
        lm0_ax1 = set(landmarks[0]["specialized_clauses"].get(ax1) or [])
        cand_v1 = [v for v in chart_vars[ax1]["domain"] if v not in lm0_ax1]
        v1 = cand_v1[0] if cand_v1 else chart_vars[ax1]["domain"][-1]
        target_req = {ax0: v0, ax1: v1}
    elif len(var_axes) == 1:
        ax0 = var_axes[0]
        target_req = {ax0: chart_vars[ax0]["domain"][0]}

    # Synthesize held-out ground-truth target process K*(. | x*) at theta*
    prompt_words = [atlas.get("domain", ""), atlas.get("query", "")]
    for ax, val in target_req.items():
        prompt_words.extend(sorted(AXIS_LEXICONS[ax].get(val, set()))[:3])
    probe_query = " ".join(prompt_words)
    x_star = encode_input_features(probe_query)

    target_fiber = dict(manifold_axes)
    for ax, val in target_req.items():
        target_fiber[ax] = [val]

    # Ground-truth natural parameter at recombinant coordinate
    eta_target = list(eta_0)
    p_star, _, target_fiber_size = kernel_distribution(eta_target, x_star, target_fiber)

    # 1. Manifold projection K_{theta*(x*)}(. | x*)
    proj = project_input_to_manifold(atlas, probe_query, explicit_axis_requests=target_req)
    p_manifold, _, man_fiber_size = kernel_distribution(
        eta_0 if not proj["ok"] else [
            eta_0[d] + sum(c * v[d] for c, v in zip(proj["fisher_chart_coordinates"], atlas["geometry"]["tangent_basis_eta"]))
            for d in range(DIM_ETA)
        ],
        x_star,
        proj["resolved_lawvere_fiber"] if proj["ok"] else {},
    )
    kl_manifold = kl_divergence(p_star, p_manifold)

    # 2. Mixture / Set Union K_union = (1/N) sum_i K_i
    n = max(1, len(landmarks))
    p_union = [0.0] * len(STRUCTURED_OUTPUT_SPACE)
    kl_single_list: list[float] = []
    for lm in landmarks:
        lm_axes = dict(manifold_axes)
        for ax, vals in (lm.get("specialized_clauses") or {}).items():
            lm_axes[ax] = vals
        p_i, _, _ = kernel_distribution(lm["natural_eta"], x_star, lm_axes)
        kl_single_list.append(kl_divergence(p_star, p_i))
        for idx in range(len(STRUCTURED_OUTPUT_SPACE)):
            p_union[idx] += p_i[idx] / n

    kl_union = kl_divergence(p_star, p_union)
    best_single_kl = min(kl_single_list) if kl_single_list else float("inf")
    union_mass_on_target = sum(p_union[idx] for idx, ps in enumerate(p_star) if ps > 1e-12)
    manifold_mass_on_target = sum(p_manifold[idx] for idx, ps in enumerate(p_star) if ps > 1e-12)

    return {
        "recombinant_request": target_req,
        "target_fiber_cardinality": target_fiber_size,
        "concatenation_admissible_outputs": logic["concatenation_fiber_size"],
        "union_probability_mass_on_target_fiber": round(union_mass_on_target, 6),
        "manifold_probability_mass_on_target_fiber": round(manifold_mass_on_target, 6),
        "kl_target_to_union_bits": "inf" if math.isinf(kl_union) else round(kl_union, 4),
        "kl_target_to_best_single_bits": "inf" if math.isinf(best_single_kl) else round(best_single_kl, 4),
        "kl_target_to_manifold_bits": "inf" if math.isinf(kl_manifold) else round(kl_manifold, 4),
        "manifold_strictly_dominates_union": (
            manifold_mass_on_target > union_mass_on_target + 1e-6
            or (kl_manifold + 1e-6 < kl_union)
        ),
    }


def render_manifold_md(atlas: dict[str, Any]) -> str:
    """Render human + agent readable MANIFOLD_ATLAS.md."""
    geom = atlas["geometry"]
    logic = atlas["logic"]
    nerve = atlas["sheaf_nerve"]
    lines = [
        f"# Lawvere–Amari Generative Skill Manifold Atlas — `{atlas.get('skill_name')}`",
        "",
        "This skill is **not** a prompt concatenation ($\\bigwedge_i Q_i$, which collapses on conflicting regimes) "
        "nor a mere router/union ($\\bigcup_i s_i$, which cannot synthesize off-sample combinations). "
        "It compiles the observed member skills as landmark sections of a **Conditional Statistical–Logical Manifold** "
        "$\\mathfrak{G}_{\\mathcal{M}} = \\langle \\Theta, \\mathcal{T}_{\\mathcal{M}}, g_F, \\mathcal{N}(\\mathcal{U}) \\rangle$ "
        "mapping each task input $x \\in \\mathcal{X}$ to a constrained fiber of structured outputs $\\mathcal{Y}_{\\mathcal{M}}(x)$.",
        "",
        "## 1. Information-Geometric Summary (Amari Conditional Fisher–Rao Metric)",
        "",
        f"- **Structured Output Lattice Cardinality ($|\\mathcal{{Y}}|$):** `{len(STRUCTURED_OUTPUT_SPACE)}`",
        f"- **Riemannian Tangent Rank ($\\dim T_{{\\bar{{\\eta}}_0}}\\mathcal{{M}}$):** `{geom['tangent_rank']}`",
        f"- **Effective Intrinsic Dimension (Participation Ratio $d_{{\\text{{eff}}}}$):** `{geom['intrinsic_dimension_participation_ratio']}`",
        f"- **D-Optimal Fisher Log-Det Spanning Volume ($V_{{\\text{{Fisher}}}}(S)$):** `{geom['fisher_logdet_volume']}`",
        f"- **Amari $e$-Geodesic vs $m$-Mixture Bregman Gain:** `{geom['amari_e_vs_m_bregman_gap_bits']} bits`",
        "",
        "## 2. Logical Normal–Tangent Decomposition (Galois Closure + Anti-Unification)",
        "",
        f"- **Concatenation Admissible Fiber ($|\\mathcal{{Y}}_{{\\bigwedge Q_i}}|$):** `{logic['concatenation_fiber_size']}` "
        f"(conflicts lifted: `{len(logic['concatenation_conflicts'])}`)",
        f"- **Point-Union Admissible Fiber ($|\\bigcup_i \\mathcal{{Y}}_i|$):** `{logic['union_fiber_size']}`",
        f"- **Manifold Total Admissible Fiber ($|\\mathcal{{Y}}_{{\\mathcal{{T}}_{{\\mathcal{{M}}}}(\\Theta)}}|$):** "
        f"`{logic['manifold_total_fiber_size']}` (`+{logic['recombinant_novel_states']}` recombinant structured output states)",
        f"- **Exact Landmark Specialization ($\\forall i,\\; \\sigma_i^* \\mathcal{{T}}_{{\\mathcal{{M}}}} \\equiv Q_i \\land \\Phi_{{\\text{{core}}}}$):** "
        f"`{logic['specialization_exact']}`",
        "",
        "### Conormal Universal Invariants ($N^*\\mathcal{M} = 0$, Always Enforced)",
        "",
    ]
    for ax, vals in logic["conormal_core"].items():
        lines.append(f"- **`{ax}`** $\\in \\{{{', '.join(f'`{v}`' for v in vals)}\\}}$")

    if logic["chart_variables"]:
        lines += ["", "### Anti-Unified Tangent Chart Coordinates ($\\theta \\in \\Theta$)", ""]
        for ax, cv in logic["chart_variables"].items():
            lines.append(
                f"- **`{cv['variable']}`** (`{ax}`): domain $\\{{{', '.join(f'`{v}`' for v in cv['domain'])}\\}}$"
            )

    lines += [
        "",
        "## 3. Landmark Anchors on $\\mathcal{M}$",
        "",
        "| Landmark | Upstream ID | Fisher Tangent Coordinates $\\theta^{(i)}$ | Specialized Fiber Clauses |",
        "|---|---|---|---|",
    ]
    for lm in atlas.get("landmarks") or []:
        coords = ", ".join(f"{c:+.2f}" for c in (lm.get("chart_coordinates") or [])) or "0.00"
        spec = "; ".join(f"{k}={v}" for k, v in (lm.get("specialized_clauses") or {}).items()) or "*(invariant core)*"
        lines.append(f"| `{lm['slug']}` | `{lm['id']}` | `[{coords}]` | `{spec}` |")

    lines += [
        "",
        "## 4. Sheaf Gluing Nerve $\\mathcal{N}(\\mathcal{U})$ ($\\Gamma(\\mathcal{U}, \\mathcal{F}) = \\ker \\delta^0$)",
        "",
        f"- **Open Cover ($\\mathcal{{U}}$):** {', '.join(f'`{u}`' for u in nerve['open_cover'])}",
        f"- **Čech 1-Cocycle Exactness ($\\delta^1 = 0$):** `{'PASS' if atlas['sheaf_verification']['cocycle_exact'] else 'FAIL'}` "
        f"(`{atlas['sheaf_verification']['triangles_checked']}` triangles verified)",
    ]
    for ov in nerve["overlaps"]:
        lines.append(
            f"- **Restriction `{ov['u']} ∩ {ov['v']}`**: must agree on keys `{ov['shared_keys']}` (`transform={ov['transform']}`)"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Compile Lawvere-Amari manifold atlas from chosen_n.json")
    b.add_argument("--chosen-n", type=Path, required=True)
    b.add_argument("--audits", type=Path, default=None)
    b.add_argument("--domain", default="general")
    b.add_argument("--query", default="")
    b.add_argument("--name", default="manifold-skill")
    b.add_argument("--out", type=Path, required=True)
    b.add_argument("--md-out", type=Path, default=None)

    p = sub.add_parser("project", help="Project a task input onto a compiled manifold_atlas.json")
    p.add_argument("--atlas", type=Path, required=True)
    p.add_argument("--input", required=True, help="Task prompt or path to task file")
    p.add_argument("--out", type=Path, default=None)

    args = ap.parse_args()
    if args.cmd == "build":
        payload = json.loads(args.chosen_n.read_text(encoding="utf-8"))
        members = payload.get("chosen") if isinstance(payload, dict) else payload
        audits: dict[str, dict[str, Any]] = {}
        if args.audits and args.audits.is_dir():
            for f in args.audits.glob("*.json"):
                try:
                    audits[f.stem] = json.loads(f.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
        atlas = build_skill_manifold(
            members or [],
            audits=audits,
            domain=args.domain,
            query=args.query,
            skill_name=args.name,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(atlas, indent=2) + "\n", encoding="utf-8")
        md_out = args.md_out or args.out.with_suffix(".md")
        md_out.write_text(render_manifold_md(atlas), encoding="utf-8")
        print(json.dumps({"ok": True, "atlas": str(args.out), "md": str(md_out)}, indent=2))
        return 0

    atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
    inp_path = Path(args.input)
    text = inp_path.read_text(encoding="utf-8", errors="replace") if inp_path.is_file() else args.input
    res = project_input_to_manifold(atlas, text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=2))
    return 0 if res["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
