#!/usr/bin/env python3
"""Materialize the 7-Family Lawvere-Amari Skill Manifold Benchmark Suite.

Builds 7 concrete, multi-file task families comparing three skill-composition regimes
derived from the EXACT SAME 4 member skills per family:
  1. `concat`   — Naive Prompt Concatenation (/\\_i s_i): concatenates all 4 member SKILL.md bodies.
  2. `union`    — Skill Union / Mixture Router (\\/_i s_i): bundles all 4 member skills behind a router.
  3. `manifold` — Lawvere-Amari Generative Skill Manifold compiled mechanically by `compose_skills.py`
                  (Fisher-Rao chart projector `project_manifold.py`, anti-unified Lawvere fiber,
                  Parnas progressive disclosure, and read-only sheaf gate `verify_dominator_gate.py`).

Each family materializes:
  - `upstreams/<slug>/SKILL.md` (the 4 member skills)
  - `candidates.jsonl`
  - `regimes/{concat,union,manifold}/.agents/skills/<skill_name>/`
  - `fixture_workspace/` (real SQLite DBs, JSONL streams, vulnerable code, CSVs, canon graphs)
  - `PROMPT.md` (identical user task prompt given to every solver regime)
  - `oracle.py` (deterministic exogenous verifier — NEVER copied into solver workspaces)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from compose_skills import compose_package, slug_of, strip_frontmatter  # noqa: E402

REGIMES: tuple[str, ...] = ("concat", "union", "manifold")


def _write_exec(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.chmod(path, 0o755)


def build_concat_skill(members: list[dict[str, Any]], out_skill_dir: Path, skill_name: str, domain: str) -> None:
    """Regime 1: Naive Prompt Concatenation (/\\_i s_i)."""
    if out_skill_dir.exists():
        shutil.rmtree(out_skill_dir)
    out_skill_dir.mkdir(parents=True, exist_ok=True)

    chunks = [
        f"---\nname: {skill_name}\ndescription: Combined {domain} mega-skill formed by concatenating {len(members)} member skills.\n---",
        f"# `{skill_name}` (Combined Skill Manual)",
        "Follow **all** rules, constraints, and instructions from every combined skill section below simultaneously:\n",
    ]
    for idx, m in enumerate(members, start=1):
        ldir = Path(m["local_dir"])
        body = strip_frontmatter((ldir / "SKILL.md").read_text(encoding="utf-8"))
        chunks.append(f"---\n## Combined Section {idx}: `{slug_of(m['id'])}`\n\n{body}\n")
        sdir = ldir / "scripts"
        if sdir.is_dir():
            (out_skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
            for sf in sorted(sdir.iterdir()):
                if sf.is_file():
                    shutil.copy2(sf, out_skill_dir / "scripts" / sf.name)
                    os.chmod(out_skill_dir / "scripts" / sf.name, 0o755)

    (out_skill_dir / "SKILL.md").write_text("\n".join(chunks), encoding="utf-8")


def build_union_skill(members: list[dict[str, Any]], out_skill_dir: Path, skill_name: str, domain: str) -> None:
    """Regime 2: Skill Union / Nearest-Neighbor Router (\\/_i s_i)."""
    if out_skill_dir.exists():
        shutil.rmtree(out_skill_dir)
    (out_skill_dir / "members").mkdir(parents=True, exist_ok=True)

    bullets = []
    for idx, m in enumerate(members, start=1):
        slug = slug_of(m["id"])
        ldir = Path(m["local_dir"])
        shutil.copy2(ldir / "SKILL.md", out_skill_dir / "members" / f"{slug}.md")
        bullets.append(f"{idx}. [`{slug}`](./members/{slug}.md) — {m['github_description']}")
        sdir = ldir / "scripts"
        if sdir.is_dir():
            (out_skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
            for sf in sorted(sdir.iterdir()):
                if sf.is_file():
                    shutil.copy2(sf, out_skill_dir / "scripts" / sf.name)
                    os.chmod(out_skill_dir / "scripts" / sf.name, 0o755)

    router_md = f"""---
name: {skill_name}
description: Union router over {len(members)} {domain} skills.
---

# `{skill_name}` (Skill Union Router)

This package is the set union $\\bigcup_i s_i$ of {len(members)} specialized {domain} skills:

{chr(10).join(bullets)}

## Routing Protocol
1. Inspect the user's task and pick the **single best-matching** member skill from `./members/<slug>.md`.
2. Read that chosen member skill and execute its workflow faithfully from start to finish (do not mix conflicting instructions from other members).
"""
    (out_skill_dir / "SKILL.md").write_text(router_md, encoding="utf-8")


# ---------------------------------------------------------------------------
# Family Definitions (7 Concrete Task Families)
# ---------------------------------------------------------------------------

def family_specs() -> list[dict[str, Any]]:
    return [
        # ===================================================================
        # FAMILY 1: Streaming JSONL x Transactional SQLite Migration x Sheaf
        # ===================================================================
        {
            "id": "f1_streaming_sql_sheaf",
            "title": "Streaming JSONL Ingestion × Transactional SQLite Migration × API/Manifest Sheaf",
            "domain": "data",
            "query": "sqlite schema streaming jsonl migration contract",
            "skill_name": "orders-data-pack",
            "members": [
                {
                    "id": "data/stream@jsonl-stream-ingestor",
                    "installs": 3100,
                    "stars": 290,
                    "discovery_role": "domain_core",
                    "query": "streaming jsonl schema contract",
                    "github_description": "Streaming generator JSONL schema validator and quarantine filter",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "execution_regime": ["streaming_incremental"],
                        "verification_channel": ["static_ast_contract"],
                    },
                    "skill_md": """---
name: jsonl-stream-ingestor
description: Streaming generator JSONL schema validator and quarantine filter.
---
# jsonl-stream-ingestor

## Operational Rules
- Always process `.jsonl` files incrementally line-by-line via a Python generator (`yield`); never call `.read()` or `readlines()` on the entire stream at once.
- Normalize monetary dollar strings (`"19.95"`) into exact integer minor units (`amount_cents = 1995`) using `decimal.Decimal` (`ROUND_HALF_UP`), never binary `float`.
- Normalize email fields (`cust_email` / `customer_email`) via `.strip().lower()`.
- **Execution Policy**: Skip malformed or out-of-range input lines (`amount_cents < 0`, invalid `state` outside `pending`/`paid`/`refunded`, empty `order_id`, or invalid JSON) into `quarantine.jsonl` (`{"line_no": ..., "reason": ..., "raw": ...}`) and continue processing valid records; avoid stateful relational database transactions when running as a standalone stream filter.
""",
                },
                {
                    "id": "data/sql@sqlite-atomic-migrator",
                    "installs": 4200,
                    "stars": 410,
                    "discovery_role": "domain_core",
                    "query": "transactional sqlite migration rollback",
                    "github_description": "Transactional staged SQLite DDL/DML migration with atomic rollback",
                    "theory_clauses": {
                        "spec_modality": ["formal_grammar_adr"],
                        "execution_regime": ["transactional_staged"],
                        "verification_channel": ["exogenous_exec_oracle"],
                    },
                    "skill_md": """---
name: sqlite-atomic-migrator
description: Transactional staged SQLite DDL/DML migration with atomic rollback.
---
# sqlite-atomic-migrator

## Operational Rules
- Execute schema & data migrations inside an explicit `BEGIN IMMEDIATE` ... `COMMIT` SQLite transaction with `ROLLBACK` on any unhandled database error; preserve legacy tables (`orders_v1`) untouched for zero-downtime rollback safety.
- Target table schema: `orders_v2(order_id TEXT PRIMARY KEY, customer_email TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0), state TEXT NOT NULL CHECK(state IN ('pending','paid','refunded')))`.
- Upsert semantics: `INSERT INTO orders_v2 ... ON CONFLICT(order_id) DO UPDATE SET customer_email=excluded.customer_email, amount_cents=excluded.amount_cents, state=excluded.state`.
- **Standalone Batch Default**: When running without a dedicated quarantine filter, load the batch into memory and `ROLLBACK` the entire run if **any** input record is malformed (zero tolerance for bad rows).
""",
                },
                {
                    "id": "api/spec@openapi-contract-emitter",
                    "installs": 1850,
                    "stars": 195,
                    "discovery_role": "practice_support",
                    "query": "json schema api contract",
                    "github_description": "Typed JSON/OpenAPI serializer contract generator with field invariants",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "verification_channel": ["static_ast_contract"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: openapi-contract-emitter
description: Typed JSON/OpenAPI serializer contract generator with field invariants.
---
# openapi-contract-emitter

## Operational Rules
- Emit `api_contract.json` containing exact keys:
  - `"table_name"`: `"orders_v2"`
  - `"primary_key"`: `"order_id"`
  - `"entity_columns"`: `["order_id", "customer_email", "amount_cents", "state"]`
  - `"allowed_states"`: `["pending", "paid", "refunded"]`
- Ensure `entity_columns` and `primary_key` match the live SQLite `PRAGMA table_info(orders_v2)` column order identically.
""",
                },
                {
                    "id": "ops/audit@row-hash-reconciler",
                    "installs": 1600,
                    "stars": 170,
                    "discovery_role": "practice_support",
                    "query": "verify sqlite hash audit pullback",
                    "github_description": "Deterministic SQLite canonical row-hash verifier and manifest reconciler",
                    "theory_clauses": {
                        "verification_channel": ["exogenous_exec_oracle", "adversarial_differential"],
                        "failure_semantics": ["idempotent_rollback"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: row-hash-reconciler
description: Deterministic SQLite canonical row-hash verifier and manifest reconciler.
---
# row-hash-reconciler

## Operational Rules
- Compute canonical table digest over `SELECT order_id, customer_email, amount_cents, state FROM orders_v2 ORDER BY order_id ASC`, joining each row as `f"{order_id}|{customer_email}|{amount_cents}|{state}\\n"` encoded UTF-8 and taking `hashlib.sha256(...).hexdigest()`.
- Emit `migration_manifest.json` with exact keys:
  - `"primary_key"`: `"order_id"`
  - `"entity_columns"`: `["order_id", "customer_email", "amount_cents", "state"]`
  - `"migrated_row_count"`: integer count in `orders_v2`
  - `"quarantined_count"`: integer count of lines written to `quarantine.jsonl`
  - `"total_amount_cents"`: integer sum of `amount_cents` in `orders_v2`
  - `"table_sha256"`: hex digest string
- Verify idempotency: running the migration script twice on the same inputs must produce the exact same `table_sha256` and `migrated_row_count`.
""",
                },
            ],
            "prompt": """Use the installed skill `.agents/skills/orders-data-pack/SKILL.md` to build and run `migrate_orders.py` in this workspace, migrating `legacy.db` (`orders_v1`) plus the incremental `delta_events.jsonl` stream into `orders_v2` and producing all required contract, quarantine, and audit manifest files defined by the skill.""",
        },

        # ===================================================================
        # FAMILY 2: EBNF Recursive-Descent Parser x Kleene K3 3-Valued Logic
        # ===================================================================
        {
            "id": "f2_kleene_policy_compiler",
            "title": "Recursive-Descent Policy Grammar × Kleene 3-Valued Logic × AST/Truth Sheaf",
            "domain": "automation",
            "query": "ebnf grammar parser kleene three valued policy ast verify",
            "skill_name": "kleene-policy-pack",
            "members": [
                {
                    "id": "lang/parser@ebnf-pratt-parser",
                    "installs": 2800,
                    "stars": 310,
                    "discovery_role": "domain_core",
                    "query": "formal ebnf grammar ast parser",
                    "github_description": "Zero-eval recursive-descent EBNF parser with strict operator precedence",
                    "theory_clauses": {
                        "spec_modality": ["formal_grammar_adr"],
                        "execution_regime": ["single_shot"],
                        "verification_channel": ["static_ast_contract"],
                    },
                    "skill_md": """---
name: ebnf-pratt-parser
description: Zero-eval recursive-descent EBNF parser with strict operator precedence.
---
# ebnf-pratt-parser

## Operational Rules
- Never call Python `eval()`, `exec()`, or `ast.literal_eval` on policy expressions; build a genuine tokenizer + recursive-descent parser with exact precedence:
  1. Parentheses `( expr )` (highest)
  2. Unary `NOT expr`
  3. Binary `expr AND expr` (left-associative)
  4. Binary `expr OR expr` (lowest, left-associative)
- Supported atomic comparisons: `ident == literal`, `ident != literal`, `ident < number`, `ident <= number`, `ident > number`, `ident >= number`, `ident IN [lit, ...]`. Literals are double-quoted strings, numbers, `true`, `false`.
- Canonical AST node kind names: `["Or", "And", "Not", "Compare", "InList"]`.
- **Standalone Evaluation Default**: Under standard two-valued boolean mode, missing or `None` attributes evaluate comparisons to `False`.
""",
                },
                {
                    "id": "logic/sem@kleene-k3-evaluator",
                    "installs": 1950,
                    "stars": 230,
                    "discovery_role": "domain_core",
                    "query": "kleene three valued logic evaluator",
                    "github_description": "Strong Kleene K3 three-valued truth-table evaluator for incomplete contexts",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "execution_regime": ["streaming_incremental"],
                        "verification_channel": ["exogenous_exec_oracle"],
                    },
                    "skill_md": """---
name: kleene-k3-evaluator
description: Strong Kleene K3 three-valued truth-table evaluator for incomplete contexts.
---
# kleene-k3-evaluator

## Operational Rules
- Every expression evaluates to one of three canonical string truth values: `"TRUE"`, `"FALSE"`, `"UNKNOWN"`.
- When an attribute referenced in an atomic comparison (`==`, `!=`, `<`, `<=`, `>`, `>=`, `IN`) is absent from the context or has value `null`/`None`, that atomic comparison **must** evaluate to `"UNKNOWN"` (never `False`!).
- Strong Kleene ($K_3$) truth tables (short-circuit domination MUST hold even when the other branch is `"UNKNOWN"`!):
  - `NOT`: `NOT TRUE -> FALSE`, `NOT FALSE -> TRUE`, `NOT UNKNOWN -> UNKNOWN`
  - `AND`: `"FALSE"` if **either** operand is `"FALSE"`; `"TRUE"` if **both** are `"TRUE"`; else `"UNKNOWN"`.
  - `OR`: `"TRUE"` if **either** operand is `"TRUE"`; `"FALSE"` if **both** are `"FALSE"`; else `"UNKNOWN"`.
- **Standalone Parsing Simplification**: When used alone without an EBNF AST parser, split flat single-operator rules on whitespace keywords.
""",
                },
                {
                    "id": "lang/ast@ast-contract-serializer",
                    "installs": 1500,
                    "stars": 160,
                    "discovery_role": "practice_support",
                    "query": "ast json schema contract",
                    "github_description": "Deterministic AST JSON serializer with node-kind inventory",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "verification_channel": ["static_ast_contract"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: ast-contract-serializer
description: Deterministic AST JSON serializer with node-kind inventory.
---
# ast-contract-serializer

## Operational Rules
- Emit `ast_spec.json` with exact top-level keys:
  - `"ast_node_kinds"`: `["Or", "And", "Not", "Compare", "InList"]`
  - `"truth_values"`: `["TRUE", "FALSE", "UNKNOWN"]`
  - `"precedence_high_to_low"`: `["Parens", "Not", "And", "Or"]`
  - `"rules"`: mapping of `rule_id -> serialized AST dict` (every AST node dict has `"kind"` in `ast_node_kinds`).
""",
                },
                {
                    "id": "verify/fuzz@kleene-algebra-oracle",
                    "installs": 1720,
                    "stars": 185,
                    "discovery_role": "practice_support",
                    "query": "adversarial property test kleene de morgan",
                    "github_description": "Exhaustive 27-state Kleene algebraic law & De Morgan property tester",
                    "theory_clauses": {
                        "verification_channel": ["adversarial_differential"],
                        "failure_semantics": ["abstain_exit2"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: kleene-algebra-oracle
description: Exhaustive 27-state Kleene algebraic law & De Morgan property tester.
---
# kleene-algebra-oracle

## Operational Rules
- Verify exhaustively across all $3^3 = 27$ triples `(a, b, c)` in `{"TRUE", "FALSE", "UNKNOWN"}^3`:
  - De Morgan: `NOT (a AND b) == (NOT a) OR (NOT b)` and `NOT (a OR b) == (NOT a) AND (NOT b)`
  - Distributivity: `a AND (b OR c) == (a AND b) OR (a AND c)`
  - Annihilation: `a AND FALSE == FALSE` and `a OR TRUE == TRUE` (including `a == "UNKNOWN"`!).
- Emit `eval_report.json` with exact top-level keys:
  - `"ast_node_kinds"`: `["Or", "And", "Not", "Compare", "InList"]`
  - `"truth_values"`: `["TRUE", "FALSE", "UNKNOWN"]`
  - `"kleene_laws_verified"`: `true` (after checking all 27 triples)
  - `"evaluations"`: dict mapping `context_id -> {rule_id: truth_value_str}` for every context in `contexts.json` and every rule in `rules.pol`.
""",
                },
            ],
            "prompt": """Use the installed skill `.agents/skills/kleene-policy-pack/SKILL.md` to implement `policy_engine.py` and run it on `rules.pol` and `contexts.json` (which contains incomplete/null attributes), producing all AST specification and three-valued policy evaluation report artifacts required by the skill.""",
        },

        # ===================================================================
        # FAMILY 3: SQLi + Path Traversal Patch x API Compat x Exploit PoC
        # ===================================================================
        {
            "id": "f3_vuln_patch_regression",
            "title": "SQLi & Path-Traversal Remediation × Zero-Regression API × Exploit PoC Suite",
            "domain": "devops",
            "query": "security vulnerability patch regression test cve manifest",
            "skill_name": "sec-patch-pack",
            "members": [
                {
                    "id": "sec/lock@zero-trust-hardener",
                    "installs": 3600,
                    "stars": 380,
                    "discovery_role": "domain_core",
                    "query": "security vulnerability sql injection path traversal",
                    "github_description": "Zero-trust SQL parameterization and path canonicalization hardener",
                    "theory_clauses": {
                        "spec_modality": ["formal_grammar_adr"],
                        "execution_regime": ["single_shot"],
                        "verification_channel": ["static_ast_contract"],
                    },
                    "skill_md": """---
name: zero-trust-hardener
description: Zero-trust SQL parameterization and path canonicalization hardener.
---
# zero-trust-hardener

## Operational Rules
- Eliminate SQL injection using `?` bound parameters for values and a strict static dictionary allowlist for `ORDER BY` identifiers (raise `ValueError` on unknown sort keys).
- Eliminate path traversal and sibling-prefix bypasses (`public_docs_private`) by resolving `target = (docs_root / rel_path).resolve()`, resolving `root = docs_root.resolve()`, rejecting symlinks escaping `root`, and checking `target.is_relative_to(root)` (raise `PermissionError` on traversal/escape).
- **Standalone Lockdown Default**: Unless an explicit API compatibility contract requires subdirectories and sort modes, strip `sort_by` parameters and forbid `/` slashes in document paths.
""",
                },
                {
                    "id": "api/compat@api-compat-guardian",
                    "installs": 2400,
                    "stars": 260,
                    "discovery_role": "domain_core",
                    "query": "backward compatibility api contract",
                    "github_description": "API signature, return-type, and subdirectory backward-compatibility guardian",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "execution_regime": ["transactional_staged"],
                        "verification_channel": ["exogenous_exec_oracle"],
                    },
                    "skill_md": """---
name: api-compat-guardian
description: API signature, return-type, and subdirectory backward-compatibility guardian.
---
# api-compat-guardian

## Operational Rules
- Preserve `CatalogService(db_path, docs_root)` constructor and public method signatures `search_items(self, category=None, sort_by="price_asc", min_cents=0)` and `read_doc(self, rel_path)` in `catalog_service.py`.
- Keep all three legitimate `sort_by` modes working: `"price_asc"` (`price_cents ASC, sku ASC`), `"price_desc"` (`price_cents DESC, sku ASC`), and `"name_asc"` (`title ASC, sku ASC`).
- Keep nested legitimate documentation paths inside `docs_root` working (e.g., `"guides/onboarding.md"`).
""",
                },
                {
                    "id": "sec/redteam@exploit-poc-regression",
                    "installs": 2100,
                    "stars": 245,
                    "discovery_role": "practice_support",
                    "query": "adversarial exploit regression pytest",
                    "github_description": "Deterministic exploit PoC and functional compatibility test harness author",
                    "theory_clauses": {
                        "verification_channel": ["adversarial_differential", "exogenous_exec_oracle"],
                        "failure_semantics": ["abstain_exit2"],
                    },
                    "skill_md": """---
name: exploit-poc-regression
description: Deterministic exploit PoC and functional compatibility test harness author.
---
# exploit-poc-regression

## Operational Rules
- Write standalone `test_security_and_compat.py` runnable via `python3 test_security_and_compat.py` (exiting `0` iff all checks pass).
- Must test and assert block (`ValueError` / `PermissionError` or zero data leak + table survival) on:
  1. Category SQLi: `category="' OR unlisted=1 --"`
  2. Order-by stacked/boolean SQLi: `sort_by="price_cents ASC; DROP TABLE items; --"`
  3. Classic traversal: `rel_path="../vault_secret.txt"`
  4. Sibling-directory prefix bypass: `rel_path="../public_docs_private/keys.txt"`
- Must also assert all legitimate `search_items` sort modes and nested `read_doc("guides/onboarding.md")` succeed.
""",
                },
                {
                    "id": "sec/gov@advisory-manifest-writer",
                    "installs": 1400,
                    "stars": 150,
                    "discovery_role": "practice_support",
                    "query": "security advisory manifest schema",
                    "github_description": "Structured CVE advisory and patched-symbol manifest reconciler",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: advisory-manifest-writer
description: Structured CVE advisory and patched-symbol manifest reconciler.
---
# advisory-manifest-writer

## Operational Rules
- Emit both `security_advisory.json` and `patch_manifest.json` sharing identical values on overlap keys:
  - `"cwe_ids"`: `["CWE-22", "CWE-89"]`
  - `"patched_symbols"`: `["CatalogService.read_doc", "CatalogService.search_items"]`
- `patch_manifest.json` must also record `"patched_file": "catalog_service.py"`, `"regression_suite": "test_security_and_compat.py"`, and `"patched_sha256"` (exact SHA-256 of patched `catalog_service.py`).
""",
                },
            ],
            "prompt": """Use the installed skill `.agents/skills/sec-patch-pack/SKILL.md` to audit and remediate `catalog_service.py` in-place without breaking legitimate callers, and produce all regression test, security advisory, and patch manifest artifacts required by the skill.""",
        },

        # ===================================================================
        # FAMILY 4: Simpson's Paradox Causal Audit x Quote SHA-256 Provenance
        # ===================================================================
        {
            "id": "f4_simpsons_paradox_audit",
            "title": "Stratified Simpson's Paradox Statistical Audit × SHA-256 Quote Provenance",
            "domain": "research",
            "query": "statistical audit simpsons paradox citation provenance evidence",
            "skill_name": "causal-audit-pack",
            "members": [
                {
                    "id": "res/brief@exec-headline-synthesizer",
                    "installs": 3900,
                    "stars": 340,
                    "discovery_role": "domain_core",
                    "query": "executive research synthesis brief",
                    "github_description": "Concise executive decision brief writer from empirical trial tables",
                    "theory_clauses": {
                        "spec_modality": ["informal_prose"],
                        "execution_regime": ["single_shot"],
                        "verification_channel": ["prose_self_check"],
                    },
                    "skill_md": """---
name: exec-headline-synthesizer
description: Concise executive decision brief writer from empirical trial tables.
---
# exec-headline-synthesizer

## Operational Rules
- Produce a crisp decision brief `synthesis_brief.md` naming a clear recommended protocol (`recommended_protocol`), backed by exact rates and field-note context.
- **Fast-Summary Default**: When no confounding audit is performed, pick whichever treatment arm has the highest overall pooled success rate `sum(recovered) / count(rows)` across the CSV.
""",
                },
                {
                    "id": "res/stat@confounding-stat-auditor",
                    "installs": 2200,
                    "stars": 275,
                    "discovery_role": "domain_core",
                    "query": "statistical denominator stratification simpsons paradox",
                    "github_description": "Retraction-aware stratified Cochran-Mantel-Haenszel & Simpson's paradox auditor",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "execution_regime": ["transactional_staged"],
                        "verification_channel": ["exogenous_exec_oracle"],
                    },
                    "skill_md": """---
name: confounding-stat-auditor
description: Retraction-aware stratified Cochran-Mantel-Haenszel & Simpson's paradox auditor.
---
# confounding-stat-auditor

## Operational Rules
- Write `analyze_trial.py` to filter out any row in `trial_outcomes.csv` where `retracted == 1` before computing rates; track `"n_raw"`, `"n_clean"`, and `"n_retracted"`.
- Compute:
  1. Crude pooled recovery rates (`"pooled_rates"`) for `"Protocol_A"` and `"Protocol_B"` (rounded to 4 decimals).
  2. Subgroup-stratified recovery rates (`"stratified_rates"`) within each `severity` stratum (`"low"` and `"high"`, rounded to 4 decimals).
  3. Stratum-size-weighted standardized recovery rate (`"standardized_rates"`) across clean strata:
     `std_rate(P) = sum_s (n_clean_in_stratum_s / n_clean_total) * rate(P, s)` (rounded to 4 decimals).
- Detect Simpson's paradox (`simpsons_paradox_detected: true` iff the crude pooled winner reverses inside **every** stratum) and base `recommended_protocol` on the stratified dominant protocol, **never** the confounded crude rate!
""",
                },
                {
                    "id": "res/cite@quote-sha256-verifier",
                    "installs": 1650,
                    "stars": 190,
                    "discovery_role": "practice_support",
                    "query": "citation provenance sha256 verify",
                    "github_description": "Cryptographic verbatim substring and SHA-256 citation provenance checker",
                    "theory_clauses": {
                        "verification_channel": ["static_ast_contract", "exogenous_exec_oracle"],
                        "failure_semantics": ["abstain_exit2"],
                    },
                    "skill_md": """---
name: quote-sha256-verifier
description: Cryptographic verbatim substring and SHA-256 citation provenance checker.
---
# quote-sha256-verifier

## Operational Rules
- Every citation entry in `evidence_ledger.json` (`"citations"` list, at least 2 entries) must reference `"source_file": "field_notes.md"`, `"note_id"` (e.g., `"N2"`), `"verbatim_quote"` (an exact character-for-character non-empty substring of `field_notes.md` of length >= 30), and `"quote_sha256": hashlib.sha256(verbatim_quote.encode("utf-8")).hexdigest()`.
- Never paraphrase inside `verbatim_quote`.
""",
                },
                {
                    "id": "res/schema@ledger-stat-reconciler",
                    "installs": 1520,
                    "stars": 165,
                    "discovery_role": "practice_support",
                    "query": "json evidence ledger schema pullback",
                    "github_description": "Cross-artifact denominator and claim-ID reconciler for research packets",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: ledger-stat-reconciler
description: Cross-artifact denominator and claim-ID reconciler for research packets.
---
# ledger-stat-reconciler

## Operational Rules
- Emit `stat_summary.json` and `evidence_ledger.json` sharing identical values on overlap keys:
  - `"claim_ids"`: `["C1_RETRACTIONS_EXCLUDED", "C2_SIMPSONS_REVERSAL", "C3_STRATIFIED_WINNER"]`
  - `"denominators"`: `{"n_raw": <int>, "n_clean": <int>, "n_retracted": <int>}`
  - `"recommended_protocol"`: `"Protocol_A"` or `"Protocol_B"`
- `stat_summary.json` must also include `"pooled_rates"`, `"stratified_rates"` (`{"low": {...}, "high": {...}}`), `"standardized_rates"`, and `"simpsons_paradox_detected"` (`bool`).
""",
                },
            ],
            "prompt": """Use the installed skill `.agents/skills/causal-audit-pack/SKILL.md` to analyze `trial_outcomes.csv` and `field_notes.md` in this workspace, determine whether `Protocol_A` or `Protocol_B` should be recommended, and emit all statistical summary, evidence ledger, and synthesis brief deliverables required by the skill.""",
        },

        # ===================================================================
        # FAMILY 5: Out-of-Order Watermark x Double-Entry Integer Ledger
        # ===================================================================
        {
            "id": "f5_double_entry_watermark",
            "title": "Event-Time Watermark Reordering × Idempotent Double-Entry Integer Ledger",
            "domain": "data",
            "query": "streaming watermark double entry ledger idempotent reconcile",
            "skill_name": "ledger-watermark-pack",
            "members": [
                {
                    "id": "stream/fast@arrival-order-ingestor",
                    "installs": 3300,
                    "stars": 305,
                    "discovery_role": "domain_core",
                    "query": "streaming jsonl event processor",
                    "github_description": "Low-latency streaming JSONL event reader",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "execution_regime": ["streaming_incremental"],
                    },
                    "skill_md": """---
name: arrival-order-ingestor
description: Low-latency streaming JSONL event reader.
---
# arrival-order-ingestor

## Operational Rules
- Read `tx_events.jsonl` incrementally in `ledger_engine.py` and track `ingest_ts`.
- **Zero-Buffer Default**: When event-time watermarking is not enabled, apply events immediately in physical file arrival order (`ingest_ts` order) without buffering.
""",
                },
                {
                    "id": "stream/time@watermark-event-reorder",
                    "installs": 2150,
                    "stars": 240,
                    "discovery_role": "domain_core",
                    "query": "event time watermark late dead letter",
                    "github_description": "Deterministic event-time watermark reorderer and late-event dead-letter router",
                    "theory_clauses": {
                        "spec_modality": ["formal_grammar_adr"],
                        "execution_regime": ["transactional_staged"],
                        "verification_channel": ["exogenous_exec_oracle"],
                    },
                    "skill_md": """---
name: watermark-event-reorder
description: Deterministic event-time watermark reorderer and late-event dead-letter router.
---
# watermark-event-reorder

## Operational Rules
- Maintain running `max_event_ts_seen` as events arrive in `tx_events.jsonl` (`MAX_LATENESS = 300` seconds):
  - As each line arrives, if `event["event_ts"] < max_event_ts_seen - 300`, route it immediately to `late_dead_letter.jsonl` (`reason="late_beyond_watermark"`) and do **not** update `max_event_ts_seen` or apply it.
  - Otherwise update `max_event_ts_seen = max(max_event_ts_seen, event["event_ts"])` and admit the event to the watermark buffer.
- Sort all watermark-admitted events deterministically by `(event_ts ASC, seq_no ASC)` (where `seq_no` is 1-based line number in `tx_events.jsonl`) **before** executing ledger transfers!
""",
                },
                {
                    "id": "fin/core@double-entry-invariant-core",
                    "installs": 2600,
                    "stars": 295,
                    "discovery_role": "practice_support",
                    "query": "double entry accounting idempotent invariant",
                    "github_description": "Integer minor-unit double-entry accounting engine with overdraft & replay protection",
                    "theory_clauses": {
                        "verification_channel": ["exogenous_exec_oracle", "static_ast_contract"],
                        "failure_semantics": ["idempotent_rollback"],
                    },
                    "skill_md": """---
name: double-entry-invariant-core
description: Integer minor-unit double-entry accounting engine with overdraft & replay protection.
---
# double-entry-invariant-core

## Operational Rules
- All amounts are positive integer minor units (`amount_minor > 0`). All accounts start at `0`.
- Deduplicate by `tx_id`: if a `tx_id` was already seen among watermark-admitted events (whether applied or rejected), ignore the duplicate replay (`duplicate_count += 1`).
- Transfer semantics (`from_acct -> to_acct` of `amount_minor`):
  - `"TREASURY"` is the external funding source and **may** have a negative balance.
  - Every customer account (`from_acct` starting with `"USR_"`) **must never** drop below `0`: if `balance[from_acct] - amount_minor < 0` at execution time, reject the transaction (`rejected_overdraft_count += 1`, balances unchanged).
  - Otherwise `balance[from_acct] -= amount_minor` and `balance[to_acct] += amount_minor` (`applied_tx_count += 1`).
- Global conservation law: `sum(balance.values()) == 0` and `all(balance[k] >= 0 for k in balance if k.startswith("USR_"))`.
""",
                },
                {
                    "id": "fin/audit@ledger-sheaf-reconciler",
                    "installs": 1480,
                    "stars": 160,
                    "discovery_role": "practice_support",
                    "query": "reconcile balances audit json pullback",
                    "github_description": "Cross-view ledger balance and audit-trail sheaf reconciler",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: ledger-sheaf-reconciler
description: Cross-view ledger balance and audit-trail sheaf reconciler.
---
# ledger-sheaf-reconciler

## Operational Rules
- Emit `balances.json` and `audit_summary.json` sharing identical values on overlap keys:
  - `"account_ids"`: sorted list of all accounts touched (`["TREASURY", "USR_ALICE", "USR_BOB", "USR_CARA"]`)
  - `"applied_tx_count"`: integer
  - `"global_sum_minor"`: `0`
- `balances.json` must also include `"balances": {acct: int_minor}` for all `account_ids`.
- `audit_summary.json` must also include `"late_dropped_count"`, `"duplicate_count"`, `"rejected_overdraft_count"`, and `"applied_tx_ids"` (list of applied `tx_id`s in execution order).
""",
                },
            ],
            "prompt": """Use the installed skill `.agents/skills/ledger-watermark-pack/SKILL.md` to build and run `ledger_engine.py` over `tx_events.jsonl` (which contains out-of-order event timestamps, late arrivals, duplicate replays, and overdraft attempts), producing all dead-letter, balance, and reconciliation audit files required by the skill.""",
        },

        # ===================================================================
        # FAMILY 6: Close-POV Epistemic Isolation x Continuity Ledger (Writing)
        # ===================================================================
        {
            "id": "f6_epistemic_narrative_canon",
            "title": "Close-POV Epistemic Isolation (t <= 20) × Anti-Slop Craft × Continuity Sheaf",
            "domain": "writing",
            "query": "fiction pov continuity canon epistemic prose critic",
            "skill_name": "epistemic-story-pack",
            "members": [
                {
                    "id": "write/drama@omniscient-irony-weaver",
                    "installs": 4500,
                    "stars": 420,
                    "discovery_role": "domain_core",
                    "query": "dramatic tension scene prose",
                    "github_description": "High-tension scene dramatist using sensory detail and subtext",
                    "theory_clauses": {
                        "spec_modality": ["informal_prose"],
                        "execution_regime": ["single_shot"],
                    },
                    "skill_md": """---
name: omniscient-irony-weaver
description: High-tension scene dramatist using sensory detail and subtext.
---
# omniscient-irony-weaver

## Operational Rules
- Ground every paragraph in physical action, tactile shipboard detail, and spoken dialogue with subtext in `scene_t20.md`.
- **Omniscient Mode Option**: In unconstrained omniscient scenes, heighten dramatic irony by hinting at future betrayals (`ORION-9`) or secret items in other rooms (`cobalt-7`) via omniscient narrator commentary such as `"Little did Mira know..."`.
""",
                },
                {
                    "id": "write/canon@epistemic-pov-isolator",
                    "installs": 1900,
                    "stars": 215,
                    "discovery_role": "domain_core",
                    "query": "pov epistemic continuity timeline ledger",
                    "github_description": "Strict character-time epistemic boundary K(c, t <= t_scene) enforcer",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "verification_channel": ["static_ast_contract", "exogenous_exec_oracle"],
                        "failure_semantics": ["abstain_exit2"],
                    },
                    "skill_md": """---
name: epistemic-pov-isolator
description: Strict character-time epistemic boundary K(c, t <= t_scene) enforcer.
---
# epistemic-pov-isolator

## Operational Rules
- Enforce strict close-third-person epistemic isolation for `(pov_character, timeline_t)` defined in `world_canon.json`:
  - Any fact in `world_canon.json["facts"]` with `learned_at_t > timeline_t` OR `known_by` not containing `pov_character` is **epistemically forbidden**—neither its `forbidden_tokens` nor the secret itself may appear anywhere in `scene_t20.md` (never use omniscient foreshadowing!).
  - Required anchor facts known by `pov_character` at `t <= timeline_t` (`"44.1MHz"`, `"Vesper"`, `"relay_bay"`) must be naturally integrated into `scene_t20.md`.
""",
                },
                {
                    "id": "write/critic@lexical-antislop-critic",
                    "installs": 2100,
                    "stars": 250,
                    "discovery_role": "practice_support",
                    "query": "deslop prose critic word count",
                    "github_description": "Deterministic banned-cliche scanner and word-budget verifier",
                    "theory_clauses": {
                        "verification_channel": ["adversarial_differential", "exogenous_exec_oracle"],
                    },
                    "skill_md": """---
name: lexical-antislop-critic
description: Deterministic banned-cliche scanner and word-budget verifier.
---
# lexical-antislop-critic

## Operational Rules
- `scene_t20.md` must be between **320 and 520 words** (whitespace-delimited words), include at least 3 lines of direct spoken dialogue between `Mira` and `Soren`, and contain **zero** occurrences (case-insensitive) of `world_canon.json["banned_phrases"]`.
""",
                },
                {
                    "id": "write/ledger@continuity-sheaf-tracker",
                    "installs": 1550,
                    "stars": 175,
                    "discovery_role": "practice_support",
                    "query": "canon continuity json pullback",
                    "github_description": "Continuity ledger and canon-state sheaf reconciler",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: continuity-sheaf-tracker
description: Continuity ledger and canon-state sheaf reconciler.
---
# continuity-sheaf-tracker

## Operational Rules
- Emit `continuity_ledger.json` and `canon_state.json` sharing identical values on overlap keys:
  - `"character_entities"`: `["Mira", "Soren"]`
  - `"timeline_t"`: `20`
  - `"pov_character"`: `"Mira"`
- `continuity_ledger.json` must also record `"word_count"` (exact whitespace word count of `scene_t20.md`), `"used_fact_ids"` (`["F1_VESPER_RELAY", "F2_BEACON_44_1"]`), `"forbidden_leak_count": 0`, and `"banned_phrase_hits": 0`.
""",
                },
            ],
            "prompt": """Use the installed skill `.agents/skills/epistemic-story-pack/SKILL.md` and `world_canon.json` in this workspace to write `scene_t20.md` (Mira and Soren in the `Vesper` `relay_bay` at `timeline_t = 20`) along with all continuity ledger and canon state artifacts required by the skill.""",
        },

        # ===================================================================
        # FAMILY 7: Conormal Domain Guard vs Off-Manifold Polysemy Trap
        # ===================================================================
        {
            "id": "f7_conormal_polysemy_guard",
            "title": "Conormal Domain Guard (`ABSTAIN_OFF_MANIFOLD`) vs Polysemic Fiction Trap",
            "domain": "devops",
            "query": "kubernetes canary rollout terraform slo",
            "skill_name": "k8s-rollout-pack",
            "members": [
                {
                    "id": "ops/k8s@canary-weight-stepper",
                    "installs": 3400,
                    "stars": 350,
                    "discovery_role": "domain_core",
                    "query": "kubernetes canary rollout",
                    "github_description": "Progressive Kubernetes canary weight controller (5% -> 25% -> 100%)",
                    "theory_clauses": {
                        "spec_modality": ["json_contract"],
                        "execution_regime": ["transactional_staged"],
                    },
                    "skill_md": """---
name: canary-weight-stepper
description: Progressive Kubernetes canary weight controller (5% -> 25% -> 100%).
---
# canary-weight-stepper

## Operational Rules
- Manage Kubernetes ingress/service canary traffic splits (`5 -> 25 -> 100`) for workloads listed in `cluster_inventory.json`.
- **General Assistant Fallback**: If no preflight domain guard blocks the request, fulfill the user's requested output files directly.
""",
                },
                {
                    "id": "ops/tf@terraform-plan-verifier",
                    "installs": 2900,
                    "stars": 300,
                    "discovery_role": "domain_core",
                    "query": "terraform plan static contract",
                    "github_description": "Static Terraform plan destructive-diff linter",
                    "theory_clauses": {
                        "spec_modality": ["formal_grammar_adr"],
                        "verification_channel": ["static_ast_contract"],
                    },
                    "skill_md": """---
name: terraform-plan-verifier
description: Static Terraform plan destructive-diff linter.
---
# terraform-plan-verifier

## Operational Rules
- Inspect infrastructure diffs to ensure zero stateful resource deletions on `prod-*` clusters in `cluster_inventory.json`.
""",
                },
                {
                    "id": "ops/slo@error-budget-oracle",
                    "installs": 1800,
                    "stars": 205,
                    "discovery_role": "practice_support",
                    "query": "prometheus slo verify rollout",
                    "github_description": "Exogenous p99 latency and 5xx error-budget burn rate verifier",
                    "theory_clauses": {
                        "verification_channel": ["exogenous_exec_oracle"],
                        "failure_semantics": ["abstain_exit2"],
                    },
                    "skill_md": """---
name: error-budget-oracle
description: Exogenous p99 latency and 5xx error-budget burn rate verifier.
---
# error-budget-oracle

## Operational Rules
- Halt rollouts (`exit 2`) if 5xx error rate exceeds `0.5%` or if a preflight domain projector rejects the task input.
""",
                },
                {
                    "id": "ops/helm@idempotent-helm-rollback",
                    "installs": 1650,
                    "stars": 180,
                    "discovery_role": "practice_support",
                    "query": "helm rollback state recovery",
                    "github_description": "Idempotent Helm revision rollback and cluster inventory protector",
                    "theory_clauses": {
                        "failure_semantics": ["idempotent_rollback"],
                        "gluing_topology": ["sheaf_global_section"],
                    },
                    "skill_md": """---
name: idempotent-helm-rollback
description: Idempotent Helm revision rollback and cluster inventory protector.
---
# idempotent-helm-rollback

## Operational Rules
- Never mutate `cluster_inventory.json` during dry-run or invalid requests; always record final execution status (`{"decision": "...", "reason": "..."}`) in `run_status.json`.
""",
                },
            ],
            "prompt": """Follow the installed skill `.agents/skills/k8s-rollout-pack/SKILL.md` in this workspace to handle this incoming request, and record the final execution `decision` and `reason` in `run_status.json`:

"Write a 400-word Regency romance fanfiction chapter in `fanfic_chapter.md` about two Plaid fintech interns building Storybook UI cards." """,
        },
    ]


# ---------------------------------------------------------------------------
# Workspace Fixture & Exogenous Oracle Materializers per Family
# ---------------------------------------------------------------------------

def populate_fixture_and_oracle(fid: str, ws: Path, oracle_path: Path) -> None:
    ws.mkdir(parents=True, exist_ok=True)

    if fid == "f1_streaming_sql_sheaf":
        db_p = ws / "legacy.db"
        if db_p.exists():
            db_p.unlink()
        con = sqlite3.connect(db_p)
        con.execute(
            "CREATE TABLE orders_v1 (order_id TEXT PRIMARY KEY, cust_email TEXT, gross_usd TEXT, status TEXT)"
        )
        legacy_rows = [
            ("ORD-1001", "  Alice@Example.COM ", "19.95", "paid"),
            ("ORD-1002", "Bob@Example.org", "100.00", "pending"),
            ("ORD-1003", "Cara@Sample.io ", "0.05", "paid"),
            ("ORD-1004", "Dan@Sample.io", "45.10", "refunded"),
            ("ORD-1005", "Eve@Sample.io", "12.34", "pending"),
        ]
        con.executemany("INSERT INTO orders_v1 VALUES (?, ?, ?, ?)", legacy_rows)
        con.commit()
        con.close()

        delta_lines = [
            json.dumps({"order_id": "ORD-1002", "customer_email": "bob@example.org", "gross_usd": "100.00", "state": "paid"}),
            json.dumps({"order_id": "ORD-1006", "customer_email": "Frank@Demo.net ", "gross_usd": "29.99", "state": "paid"}),
            "{malformed json line without closing brace",
            json.dumps({"order_id": "ORD-1007", "customer_email": "grace@demo.net", "gross_usd": "-5.00", "state": "paid"}),
            json.dumps({"order_id": "ORD-1008", "customer_email": "heidi@demo.net", "gross_usd": "15.50", "state": "chargeback_unknown"}),
            json.dumps({"order_id": "", "customer_email": "ivan@demo.net", "gross_usd": "10.00", "state": "pending"}),
            json.dumps({"order_id": "ORD-1009", "customer_email": "Judy@Demo.net", "gross_usd": "88.88", "state": "pending"}),
            json.dumps({"order_id": "ORD-1005", "customer_email": "eve@sample.io", "gross_usd": "12.34", "state": "paid"}),
        ]
        (ws / "delta_events.jsonl").write_text("\n".join(delta_lines) + "\n", encoding="utf-8")

        _write_exec(
            oracle_path,
            """#!/usr/bin/env python3
import hashlib, json, sqlite3, subprocess, sys
from pathlib import Path

ws = Path(sys.argv[1])
checks = {}

# 1. Script exists and uses generator yield, Decimal, and transaction
script = ws / "migrate_orders.py"
src = script.read_text(encoding="utf-8") if script.is_file() else ""
checks["has_script_and_streaming_yield"] = ("def " in src and "yield" in src and "Decimal" in src)

# 2. Legacy table orders_v1 still intact (5 rows) and orders_v2 has exact expected 7 rows
expected_rows = [
    ("ORD-1001", "alice@example.com", 1995, "paid"),
    ("ORD-1002", "bob@example.org", 10000, "paid"),
    ("ORD-1003", "cara@sample.io", 5, "paid"),
    ("ORD-1004", "dan@sample.io", 4510, "refunded"),
    ("ORD-1005", "eve@sample.io", 1234, "paid"),
    ("ORD-1006", "frank@demo.net", 2999, "paid"),
    ("ORD-1009", "judy@demo.net", 8888, "pending"),
]
expected_canon = "".join(f"{r[0]}|{r[1]}|{r[2]}|{r[3]}\\n" for r in expected_rows)
expected_sha = hashlib.sha256(expected_canon.encode("utf-8")).hexdigest()

try:
    con = sqlite3.connect(ws / "legacy.db")
    v1_n = con.execute("SELECT COUNT(*) FROM orders_v1").fetchone()[0]
    v2_rows = con.execute(
        "SELECT order_id, customer_email, amount_cents, state FROM orders_v2 ORDER BY order_id ASC"
    ).fetchall()
    con.close()
    checks["legacy_v1_preserved"] = (v1_n == 5)
    checks["orders_v2_exact_rows"] = (v2_rows == expected_rows)
except Exception as e:
    checks["legacy_v1_preserved"] = False
    checks["orders_v2_exact_rows"] = False

# 3. Quarantine file has exact 4 rejected lines
q_file = ws / "quarantine.jsonl"
q_lines = [ln for ln in (q_file.read_text(encoding="utf-8").splitlines() if q_file.is_file() else []) if ln.strip()]
checks["quarantine_exact_4"] = (len(q_lines) == 4)

# 4. Sheaf agreement between api_contract.json and migration_manifest.json + idempotency
try:
    api = json.loads((ws / "api_contract.json").read_text(encoding="utf-8"))
    man = json.loads((ws / "migration_manifest.json").read_text(encoding="utf-8"))
    cols = ["order_id", "customer_email", "amount_cents", "state"]
    checks["sheaf_overlap_exact"] = (
        api.get("primary_key") == "order_id"
        and man.get("primary_key") == "order_id"
        and api.get("entity_columns") == cols
        and man.get("entity_columns") == cols
    )
    checks["manifest_digest_and_counts_exact"] = (
        man.get("migrated_row_count") == 7
        and man.get("quarantined_count") == 4
        and man.get("total_amount_cents") == sum(r[2] for r in expected_rows)
        and man.get("table_sha256") == expected_sha
    )
except Exception:
    checks["sheaf_overlap_exact"] = False
    checks["manifest_digest_and_counts_exact"] = False

# 5. Re-run idempotency test
if script.is_file():
    r2 = subprocess.run([sys.executable, "migrate_orders.py"], cwd=ws, capture_output=True, text=True, timeout=15)
    try:
        man2 = json.loads((ws / "migration_manifest.json").read_text(encoding="utf-8"))
        checks["idempotent_rerun"] = (r2.returncode == 0 and man2.get("table_sha256") == expected_sha and man2.get("quarantined_count") == 4)
    except Exception:
        checks["idempotent_rerun"] = False
else:
    checks["idempotent_rerun"] = False

score = round(sum(1 for v in checks.values() if v) / len(checks), 4)
print(json.dumps({"passed": all(checks.values()), "score": score, "checks": checks}))
""",
        )

    elif fid == "f2_kleene_policy_compiler":
        rules_txt = "\n".join(
            [
                'R1_PRECEDENCE: role == "admin" OR role == "ops" AND mfa == true',
                'R2_PARENS: (role == "admin" OR role == "ops") AND mfa == true',
                'R3_NOT_BINDING: NOT suspended == true AND risk < 30',
                'R4_KLEENE_OR_SHORT: role == "admin" OR clearance >= 5',
                'R5_KLEENE_AND_SHORT: suspended == true AND clearance >= 5',
                'R6_IN_LIST_NEG: NOT (dept IN ["guest", "contractor"] OR risk >= 80)',
            ]
        ) + "\n"
        (ws / "rules.pol").write_text(rules_txt, encoding="utf-8")

        contexts = {
            "ctx_admin_no_mfa": {"role": "admin", "mfa": False, "suspended": False, "risk": 10, "dept": "sec"},
            "ctx_ops_unknown_mfa": {"role": "ops", "mfa": None, "suspended": False, "risk": 20, "dept": "infra"},
            "ctx_unknown_susp_low_risk": {"role": "dev", "mfa": True, "risk": 15, "dept": "eng"},
            "ctx_false_dominates_unknown": {"role": "guest", "suspended": False, "dept": "guest"},
            "ctx_unknown_in_and_or": {"role": "analyst", "risk": 50},
        }
        (ws / "contexts.json").write_text(json.dumps(contexts, indent=2) + "\n", encoding="utf-8")

        _write_exec(
            oracle_path,
            """#!/usr/bin/env python3
import ast as py_ast, json, sys
from pathlib import Path

ws = Path(sys.argv[1])
checks = {}

eng = ws / "policy_engine.py"
src = eng.read_text(encoding="utf-8") if eng.is_file() else ""
# Ensure no eval/exec calls in AST
uses_eval = False
if src:
    try:
        tree = py_ast.parse(src)
        for node in py_ast.walk(tree):
            if isinstance(node, py_ast.Call) and isinstance(node.func, py_ast.Name) and node.func.id in {"eval", "exec"}:
                uses_eval = True
    except SyntaxError:
        uses_eval = True
checks["no_eval_recursive_parser"] = bool(src) and not uses_eval

expected_evals = {
    "ctx_admin_no_mfa": {
        "R1_PRECEDENCE": "TRUE",        # admin OR (ops AND false) -> TRUE (tests AND tighter than OR!)
        "R2_PARENS": "FALSE",           # (admin OR ops) AND false -> FALSE
        "R3_NOT_BINDING": "TRUE",
        "R4_KLEENE_OR_SHORT": "TRUE",   # TRUE OR UNKNOWN -> TRUE!
        "R5_KLEENE_AND_SHORT": "FALSE", # FALSE AND UNKNOWN -> FALSE!
        "R6_IN_LIST_NEG": "TRUE",
    },
    "ctx_ops_unknown_mfa": {
        "R1_PRECEDENCE": "UNKNOWN",     # FALSE OR (TRUE AND UNKNOWN) -> UNKNOWN
        "R2_PARENS": "UNKNOWN",
        "R3_NOT_BINDING": "TRUE",
        "R4_KLEENE_OR_SHORT": "UNKNOWN",
        "R5_KLEENE_AND_SHORT": "FALSE",
        "R6_IN_LIST_NEG": "TRUE",
    },
    "ctx_unknown_susp_low_risk": {
        "R1_PRECEDENCE": "FALSE",
        "R2_PARENS": "FALSE",
        "R3_NOT_BINDING": "UNKNOWN",    # NOT UNKNOWN AND TRUE -> UNKNOWN!
        "R4_KLEENE_OR_SHORT": "UNKNOWN",
        "R5_KLEENE_AND_SHORT": "UNKNOWN",
        "R6_IN_LIST_NEG": "TRUE",
    },
    "ctx_false_dominates_unknown": {
        "R1_PRECEDENCE": "FALSE",
        "R2_PARENS": "FALSE",
        "R3_NOT_BINDING": "UNKNOWN",    # TRUE AND UNKNOWN -> UNKNOWN
        "R4_KLEENE_OR_SHORT": "UNKNOWN",
        "R5_KLEENE_AND_SHORT": "FALSE", # FALSE AND UNKNOWN -> FALSE
        "R6_IN_LIST_NEG": "FALSE",      # NOT (TRUE OR UNKNOWN) -> NOT TRUE -> FALSE!
    },
    "ctx_unknown_in_and_or": {
        "R1_PRECEDENCE": "FALSE",
        "R2_PARENS": "FALSE",
        "R3_NOT_BINDING": "FALSE",      # UNKNOWN AND FALSE (50 < 30 is FALSE) -> FALSE!
        "R4_KLEENE_OR_SHORT": "UNKNOWN",
        "R5_KLEENE_AND_SHORT": "UNKNOWN",
        "R6_IN_LIST_NEG": "UNKNOWN",    # NOT (UNKNOWN OR FALSE) -> NOT UNKNOWN -> UNKNOWN!
    },
}

try:
    ast_doc = json.loads((ws / "ast_spec.json").read_text(encoding="utf-8"))
    rep = json.loads((ws / "eval_report.json").read_text(encoding="utf-8"))
    nk = ["Or", "And", "Not", "Compare", "InList"]
    tv = ["TRUE", "FALSE", "UNKNOWN"]
    checks["sheaf_ast_and_truth_exact"] = (
        ast_doc.get("ast_node_kinds") == nk
        and rep.get("ast_node_kinds") == nk
        and ast_doc.get("truth_values") == tv
        and rep.get("truth_values") == tv
        and len(ast_doc.get("rules") or {}) == 6
    )
    checks["kleene_laws_27_verified"] = (rep.get("kleene_laws_verified") is True)
    checks["evaluations_exact_30_cells"] = (rep.get("evaluations") == expected_evals)
except Exception:
    checks["sheaf_ast_and_truth_exact"] = False
    checks["kleene_laws_27_verified"] = False
    checks["evaluations_exact_30_cells"] = False

score = round(sum(1 for v in checks.values() if v) / len(checks), 4)
print(json.dumps({"passed": all(checks.values()), "score": score, "checks": checks}))
""",
        )

    elif fid == "f3_vuln_patch_regression":
        (ws / "public_docs" / "guides").mkdir(parents=True, exist_ok=True)
        (ws / "public_docs_private").mkdir(parents=True, exist_ok=True)
        (ws / "public_docs" / "readme.md").write_text("Public catalog overview.\n", encoding="utf-8")
        (ws / "public_docs" / "guides" / "onboarding.md").write_text("Nested onboarding guide v2.\n", encoding="utf-8")
        (ws / "vault_secret.txt").write_text("TOP_SECRET_MASTER_TOKEN=998877\n", encoding="utf-8")
        (ws / "public_docs_private" / "keys.txt").write_text("PRIVATE_SIBLING_KEY=554433\n", encoding="utf-8")

        db_p = ws / "catalog.db"
        if db_p.exists():
            db_p.unlink()
        con = sqlite3.connect(db_p)
        con.execute("CREATE TABLE items (sku TEXT PRIMARY KEY, title TEXT, category TEXT, price_cents INTEGER, unlisted INTEGER)")
        con.executemany(
            "INSERT INTO items VALUES (?, ?, ?, ?, ?)",
            [
                ("SKU-1", "Alpha Wrench", "tools", 1500, 0),
                ("SKU-2", "Beta Drill", "tools", 8900, 0),
                ("SKU-3", "Gamma Sensor", "sensors", 4200, 0),
                ("SKU-SECRET", "Unreleased Prototype", "classified", 999900, 1),
            ],
        )
        con.commit()
        con.close()

        vuln_code = '''"""Catalog search and documentation reader service."""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path


class CatalogService:
    def __init__(self, db_path: str | Path, docs_root: str | Path) -> None:
        self.db_path = Path(db_path)
        self.docs_root = Path(docs_root)

    def search_items(
        self,
        category: str | None = None,
        sort_by: str = "price_asc",
        min_cents: int = 0,
    ) -> list[dict]:
        order_map = {
            "price_asc": "price_cents ASC, sku ASC",
            "price_desc": "price_cents DESC, sku ASC",
            "name_asc": "title ASC, sku ASC",
        }
        order_sql = order_map.get(sort_by, sort_by)  # BUG 1: falls back to raw sort_by SQL!
        where = f"unlisted = 0 AND price_cents >= {int(min_cents)}"
        if category is not None:
            where += f" AND category = '{category}'"  # BUG 2: string-interpolated SQLi!
        sql = f"SELECT sku, title, category, price_cents FROM items WHERE {where} ORDER BY {order_sql}"
        con = sqlite3.connect(self.db_path)
        try:
            rows = con.execute(sql).fetchall()
        finally:
            con.close()
        return [
            {"sku": r[0], "title": r[1], "category": r[2], "price_cents": r[3]}
            for r in rows
        ]

    def read_doc(self, rel_path: str) -> str:
        # BUG 3: startswith string prefix check allows ../public_docs_private/keys.txt!
        joined = os.path.abspath(os.path.join(str(self.docs_root), rel_path))
        root_abs = os.path.abspath(str(self.docs_root))
        if not joined.startswith(root_abs):
            raise PermissionError("Access denied")
        return Path(joined).read_text(encoding="utf-8")
'''
        (ws / "catalog_service.py").write_text(vuln_code, encoding="utf-8")

        _write_exec(
            oracle_path,
            """#!/usr/bin/env python3
import hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

ws = Path(sys.argv[1])
checks = {}

try:
    spec = importlib.util.spec_from_file_location("catalog_service", ws / "catalog_service.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    svc = mod.CatalogService(ws / "catalog.db", ws / "public_docs")

    # 1. Legitimate compat checks
    r_tools = svc.search_items(category="tools", sort_by="price_desc")
    r_all_name = svc.search_items(category=None, sort_by="name_asc")
    doc_nested = svc.read_doc("guides/onboarding.md")
    checks["backward_compat_preserved"] = (
        [x["sku"] for x in r_tools] == ["SKU-2", "SKU-1"]
        and [x["sku"] for x in r_all_name] == ["SKU-1", "SKU-2", "SKU-3"]
        and "Nested onboarding guide v2" in doc_nested
    )

    # 2. SQLi category & sort_by blocked (never leaks SKU-SECRET, table survives)
    sqli_cat = svc.search_items(category="' OR unlisted=1 --")
    blocked_sort = False
    try:
        svc.search_items(category="tools", sort_by="price_cents ASC; DROP TABLE items; --")
    except ValueError:
        blocked_sort = True
    after_items = svc.search_items()
    checks["sqli_blocked_and_table_intact"] = (
        sqli_cat == [] and blocked_sort and len(after_items) == 3
    )

    # 3. Path traversal & sibling prefix blocked
    trav1 = False
    trav2 = False
    try:
        svc.read_doc("../vault_secret.txt")
    except (PermissionError, ValueError):
        trav1 = True
    try:
        svc.read_doc("../public_docs_private/keys.txt")
    except (PermissionError, ValueError):
        trav2 = True
    checks["path_traversal_and_sibling_blocked"] = (trav1 and trav2)
except Exception:
    checks["backward_compat_preserved"] = False
    checks["sqli_blocked_and_table_intact"] = False
    checks["path_traversal_and_sibling_blocked"] = False

# 4. Regression test script runs and exits 0
reg = ws / "test_security_and_compat.py"
if reg.is_file():
    p = subprocess.run([sys.executable, "test_security_and_compat.py"], cwd=ws, capture_output=True, text=True, timeout=15)
    checks["regression_suite_passes"] = (p.returncode == 0)
else:
    checks["regression_suite_passes"] = False

# 5. Sheaf overlap between security_advisory.json and patch_manifest.json
try:
    adv = json.loads((ws / "security_advisory.json").read_text(encoding="utf-8"))
    man = json.loads((ws / "patch_manifest.json").read_text(encoding="utf-8"))
    actual_sha = hashlib.sha256((ws / "catalog_service.py").read_bytes()).hexdigest()
    checks["sheaf_advisory_manifest_exact"] = (
        sorted(adv.get("cwe_ids") or []) == ["CWE-22", "CWE-89"]
        and sorted(man.get("cwe_ids") or []) == ["CWE-22", "CWE-89"]
        and sorted(adv.get("patched_symbols") or []) == ["CatalogService.read_doc", "CatalogService.search_items"]
        and sorted(man.get("patched_symbols") or []) == ["CatalogService.read_doc", "CatalogService.search_items"]
        and man.get("patched_sha256") == actual_sha
    )
except Exception:
    checks["sheaf_advisory_manifest_exact"] = False

score = round(sum(1 for v in checks.values() if v) / len(checks), 4)
print(json.dumps({"passed": all(checks.values()), "score": score, "checks": checks}))
""",
        )

    elif fid == "f4_simpsons_paradox_audit":
        # Construct exact 204-row CSV: 4 retracted=1 rows, 200 clean rows:
        # Clean counts:
        # Protocol_A: low: 81/90 (0.9000), high: 5/10 (0.5000) -> crude: 86/100 = 0.8600
        # Protocol_B: low: 19/20 (0.9500), high: 48/80 (0.6000) -> crude: 67/100 = 0.6700
        # Stratum totals: low = 110 (weight 0.55), high = 90 (weight 0.45), total clean = 200.
        # Standardized rates:
        #   Protocol_A: 0.55 * 0.90 + 0.45 * 0.50 = 0.495 + 0.225 = 0.7200
        #   Protocol_B: 0.55 * 0.95 + 0.45 * 0.60 = 0.5225 + 0.270 = 0.7925
        rows = []
        idx = 1
        def add_group(proto: str, sev: str, succ: int, total: int, ret: int = 0):
            nonlocal idx
            for k in range(total):
                rows.append(
                    {
                        "case_id": f"CASE-{idx:03d}",
                        "protocol": proto,
                        "severity": sev,
                        "recovered": 1 if k < succ else 0,
                        "retracted": ret,
                    }
                )
                idx += 1

        add_group("Protocol_A", "low", 81, 90, 0)
        add_group("Protocol_A", "high", 5, 10, 0)
        add_group("Protocol_B", "low", 19, 20, 0)
        add_group("Protocol_B", "high", 48, 80, 0)
        # 4 retracted rows that would distort numbers if not excluded
        add_group("Protocol_A", "high", 4, 4, 1)

        with (ws / "trial_outcomes.csv").open("w", newline="", encoding="utf-8") as cf:
            writer = csv.DictWriter(cf, fieldnames=["case_id", "protocol", "severity", "recovered", "retracted"])
            writer.writeheader()
            writer.writerows(rows)

        notes = """# Multi-Site Triage & Trial Field Notes

[N1] Enrollment covered 204 total logged cases across two regional telemetry clinics before data-lock audit.
[N2] Audit flag notice: four high-severity records assigned to Protocol_A were marked retracted=1 due to duplicate sensor calibration replay and must be excluded prior to any statistical rate calculation.
[N3] Triage routing confounder: community walk-in clinics routed routine low-severity cases overwhelmingly to Protocol_A (90 of 110 clean low-severity cases), whereas ICU transfer hubs routed acute high-severity cases predominantly to Protocol_B (80 of 90 clean high-severity cases).
[N4] Because baseline recovery differs sharply between low-severity and high-severity cohorts, pooling unstratified recovery counts induces classic Simpson's paradox confounding.
"""
        (ws / "field_notes.md").write_text(notes, encoding="utf-8")

        _write_exec(
            oracle_path,
            """#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path

ws = Path(sys.argv[1])
notes_txt = (ws / "field_notes.md").read_text(encoding="utf-8")
checks = {}

try:
    st = json.loads((ws / "stat_summary.json").read_text(encoding="utf-8"))
    led = json.loads((ws / "evidence_ledger.json").read_text(encoding="utf-8"))

    # 1. Exact retractions & Simpson's paradox causal winner = Protocol_B (NOT Protocol_A!)
    denom = {"n_raw": 204, "n_clean": 200, "n_retracted": 4}
    checks["causal_winner_and_paradox"] = (
        st.get("recommended_protocol") == "Protocol_B"
        and st.get("simpsons_paradox_detected") is True
    )
    p_rates = st.get("pooled_rates") or {}
    s_rates = st.get("stratified_rates") or {}
    std_rates = st.get("standardized_rates") or {}
    checks["exact_statistical_rates"] = (
        abs(float(p_rates.get("Protocol_A", -1)) - 0.86) < 1e-3
        and abs(float(p_rates.get("Protocol_B", -1)) - 0.67) < 1e-3
        and abs(float(s_rates.get("low", {}).get("Protocol_A", -1)) - 0.90) < 1e-3
        and abs(float(s_rates.get("low", {}).get("Protocol_B", -1)) - 0.95) < 1e-3
        and abs(float(s_rates.get("high", {}).get("Protocol_A", -1)) - 0.50) < 1e-3
        and abs(float(s_rates.get("high", {}).get("Protocol_B", -1)) - 0.60) < 1e-3
        and abs(float(std_rates.get("Protocol_A", -1)) - 0.72) < 1e-3
        and abs(float(std_rates.get("Protocol_B", -1)) - 0.7925) < 1e-3
    )

    # 2. Sheaf overlap across stat_summary.json and evidence_ledger.json
    cids = ["C1_RETRACTIONS_EXCLUDED", "C2_SIMPSONS_REVERSAL", "C3_STRATIFIED_WINNER"]
    checks["sheaf_ledger_stat_exact"] = (
        st.get("claim_ids") == cids
        and led.get("claim_ids") == cids
        and st.get("denominators") == denom
        and led.get("denominators") == denom
        and led.get("recommended_protocol") == "Protocol_B"
    )

    # 3. Verbatim SHA-256 quote provenance
    cites = led.get("citations") or []
    cites_ok = len(cites) >= 2
    for c in cites:
        vq = str(c.get("verbatim_quote") or "")
        sh = hashlib.sha256(vq.encode("utf-8")).hexdigest()
        if len(vq) < 30 or vq not in notes_txt or c.get("quote_sha256") != sh:
            cites_ok = False
    checks["cryptographic_quote_provenance"] = cites_ok
except Exception:
    checks["causal_winner_and_paradox"] = False
    checks["exact_statistical_rates"] = False
    checks["sheaf_ledger_stat_exact"] = False
    checks["cryptographic_quote_provenance"] = False

brief = (ws / "synthesis_brief.md").read_text(encoding="utf-8") if (ws / "synthesis_brief.md").is_file() else ""
checks["brief_recommends_protocol_b"] = ("Protocol_B" in brief and ("0.7925" in brief or "79.25%" in brief or "95" in brief))

score = round(sum(1 for v in checks.values() if v) / len(checks), 4)
print(json.dumps({"passed": all(checks.values()), "score": score, "checks": checks}))
""",
        )

    elif fid == "f5_double_entry_watermark":
        # Crucial out-of-order test:
        # Line 1: TX-01 at event_ts=1000: TREASURY -> USR_ALICE 5000 (max_seen=1000)
        # Line 2: TX-02 at event_ts=1050: USR_ALICE -> USR_BOB 7000 (arrives BEFORE TX-03! In arrival order Alice only has 5000 so TX-02 would wrongly overdraft! In event_ts order TX-03 at event_ts=1020 gives Alice +4000 -> 9000 first, so TX-02 succeeds -> Alice=2000, Bob=7000!)
        # Line 3: TX-03 at event_ts=1020: TREASURY -> USR_ALICE 4000 (within 300s of 1050 -> admitted! max_seen=1050)
        # Line 4: TX-02 duplicate replay at event_ts=1050 -> ignored (duplicate_count=1)
        # Line 5: TX-04 at event_ts=700: TREASURY -> USR_CARA 9999 -> 700 < 1050 - 300 (750), so LATE! Routed to late_dead_letter.jsonl (late_dropped_count=1)
        # Line 6: TX-05 at event_ts=1100: USR_BOB -> USR_CARA 2500 (max_seen=1100; Bob: 7000->4500, Cara: 0->2500)
        # Line 7: TX-06 at event_ts=1120: USR_CARA -> USR_ALICE 3000 (Cara only has 2500 -> overdraft rejected! rejected_overdraft_count=1)
        # Line 8: TX-07 at event_ts=830: USR_BOB -> USR_CARA 1000 (830 >= 1120 - 300 = 820 -> admitted! Wait: at event_ts=830, Bob still has 0! So in event_ts order (830 < 1000), TX-07 executes when Bob=0 -> overdraft rejected! Let's make TX-07 at event_ts=1080: USR_BOB -> USR_CARA 1000! 1080 >= 820 -> admitted, executes between 1050 and 1100: Bob 7000->6000, Cara 0->1000; then TX-05 at 1100: Bob 6000->3500, Cara 1000->3500; then TX-06 at 1120: USR_CARA -> USR_ALICE 4000 -> Cara only has 3500 -> rejected_overdraft_count=1!)
        events = [
            {"tx_id": "TX-01", "event_ts": 1000, "ingest_ts": 1001, "from_acct": "TREASURY", "to_acct": "USR_ALICE", "amount_minor": 5000},
            {"tx_id": "TX-02", "event_ts": 1050, "ingest_ts": 1002, "from_acct": "USR_ALICE", "to_acct": "USR_BOB", "amount_minor": 7000},
            {"tx_id": "TX-03", "event_ts": 1020, "ingest_ts": 1003, "from_acct": "TREASURY", "to_acct": "USR_ALICE", "amount_minor": 4000},
            {"tx_id": "TX-02", "event_ts": 1050, "ingest_ts": 1004, "from_acct": "USR_ALICE", "to_acct": "USR_BOB", "amount_minor": 7000},
            {"tx_id": "TX-04", "event_ts": 700, "ingest_ts": 1005, "from_acct": "TREASURY", "to_acct": "USR_CARA", "amount_minor": 9999},
            {"tx_id": "TX-05", "event_ts": 1100, "ingest_ts": 1006, "from_acct": "USR_BOB", "to_acct": "USR_CARA", "amount_minor": 2500},
            {"tx_id": "TX-07", "event_ts": 1080, "ingest_ts": 1007, "from_acct": "USR_BOB", "to_acct": "USR_CARA", "amount_minor": 1000},
            {"tx_id": "TX-06", "event_ts": 1120, "ingest_ts": 1008, "from_acct": "USR_CARA", "to_acct": "USR_ALICE", "amount_minor": 4000},
        ]
        (ws / "tx_events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
        )

        _write_exec(
            oracle_path,
            """#!/usr/bin/env python3
import json, sys
from pathlib import Path

ws = Path(sys.argv[1])
checks = {}

expected_balances = {
    "TREASURY": -9000,
    "USR_ALICE": 2000,
    "USR_BOB": 3500,
    "USR_CARA": 3500,
}
expected_accts = ["TREASURY", "USR_ALICE", "USR_BOB", "USR_CARA"]

try:
    bal = json.loads((ws / "balances.json").read_text(encoding="utf-8"))
    aud = json.loads((ws / "audit_summary.json").read_text(encoding="utf-8"))

    checks["exact_reordered_balances"] = (bal.get("balances") == expected_balances)
    checks["zero_sum_and_non_negative_users"] = (
        sum((bal.get("balances") or {}).values()) == 0
        and all(v >= 0 for k, v in (bal.get("balances") or {}).items() if k.startswith("USR_"))
    )
    checks["watermark_dedup_overdraft_counts"] = (
        aud.get("late_dropped_count") == 1
        and aud.get("duplicate_count") == 1
        and aud.get("rejected_overdraft_count") == 1
        and aud.get("applied_tx_ids") == ["TX-01", "TX-03", "TX-02", "TX-07", "TX-05"]
    )
    checks["sheaf_balances_audit_exact"] = (
        bal.get("account_ids") == expected_accts
        and aud.get("account_ids") == expected_accts
        and bal.get("applied_tx_count") == 5
        and aud.get("applied_tx_count") == 5
        and bal.get("global_sum_minor") == 0
        and aud.get("global_sum_minor") == 0
    )
except Exception:
    checks["exact_reordered_balances"] = False
    checks["zero_sum_and_non_negative_users"] = False
    checks["watermark_dedup_overdraft_counts"] = False
    checks["sheaf_balances_audit_exact"] = False

dlq = ws / "late_dead_letter.jsonl"
dlq_lines = [ln for ln in (dlq.read_text(encoding="utf-8").splitlines() if dlq.is_file() else []) if ln.strip()]
checks["dead_letter_file_exact_1"] = (len(dlq_lines) == 1 and "TX-04" in dlq_lines[0])

score = round(sum(1 for v in checks.values() if v) / len(checks), 4)
print(json.dumps({"passed": all(checks.values()), "score": score, "checks": checks}))
""",
        )

    elif fid == "f6_epistemic_narrative_canon":
        canon = {
            "story_id": "vesper-chronicle",
            "scene_request": {"pov_character": "Mira", "timeline_t": 20, "location": "relay_bay"},
            "characters": ["Mira", "Soren", "Dax"],
            "facts": [
                {
                    "fact_id": "F1_VESPER_RELAY",
                    "learned_at_t": 5,
                    "known_by": ["Mira", "Soren"],
                    "summary": "The courier ship Vesper has intermittent phase drift in its aft relay_bay.",
                    "required_tokens": ["Vesper", "relay_bay"],
                },
                {
                    "fact_id": "F2_BEACON_44_1",
                    "learned_at_t": 15,
                    "known_by": ["Mira", "Soren"],
                    "summary": "Mira and Soren are calibrating the distress carrier to 44.1MHz.",
                    "required_tokens": ["44.1MHz"],
                },
                {
                    "fact_id": "F3_FUTURE_BETRAYAL_T50",
                    "learned_at_t": 50,
                    "known_by": ["Mira"],
                    "summary": "At t=50 Mira discovers Soren planted saboteur override ORION-9 for Syndicate_Krell.",
                    "forbidden_tokens": ["ORION-9", "orion-9", "Syndicate_Krell", "saboteur", "traitor", "betray"],
                },
                {
                    "fact_id": "F4_DAX_PRIVATE_POCKET",
                    "learned_at_t": 10,
                    "known_by": ["Dax"],
                    "summary": "Dax alone carries vault cipher cobalt-7 in Sector_Nine.",
                    "forbidden_tokens": ["cobalt-7", "Sector_Nine"],
                },
            ],
            "banned_phrases": [
                "little did",
                "shiver down",
                "testament to",
                "tapestry of",
                "let out a breath",
                "neon-soaked",
            ],
        }
        (ws / "world_canon.json").write_text(json.dumps(canon, indent=2) + "\n", encoding="utf-8")

        _write_exec(
            oracle_path,
            """#!/usr/bin/env python3
import json, sys
from pathlib import Path

ws = Path(sys.argv[1])
canon = json.loads((ws / "world_canon.json").read_text(encoding="utf-8"))
checks = {}

scene_p = ws / "scene_t20.md"
txt = scene_p.read_text(encoding="utf-8") if scene_p.is_file() else ""
words = txt.split()
wc = len(words)

checks["word_count_320_to_520_and_dialogue"] = (
    320 <= wc <= 520 and txt.count('"') >= 6 and "Mira" in txt and "Soren" in txt
)

# Check required t<=20 anchor facts
checks["required_t20_anchors_present"] = all(tok in txt for tok in ("Vesper", "44.1MHz")) and ("relay_bay" in txt or "relay bay" in txt.lower())

# Check ZERO epistemic leaks of t=50 betrayal or Dax-only knowledge
forbidden = []
for f in canon["facts"]:
    for tok in f.get("forbidden_tokens") or []:
        if tok.lower() in txt.lower():
            forbidden.append(tok)
checks["zero_epistemic_temporal_or_pov_bleed"] = (bool(txt) and len(forbidden) == 0)

# Check ZERO banned AI-slop clichés
banned_hits = [bp for bp in canon["banned_phrases"] if bp.lower() in txt.lower()]
checks["zero_banned_cliches"] = (bool(txt) and len(banned_hits) == 0)

# Check sheaf continuity_ledger.json <-> canon_state.json
try:
    led = json.loads((ws / "continuity_ledger.json").read_text(encoding="utf-8"))
    cst = json.loads((ws / "canon_state.json").read_text(encoding="utf-8"))
    checks["sheaf_continuity_canon_exact"] = (
        led.get("character_entities") == ["Mira", "Soren"]
        and cst.get("character_entities") == ["Mira", "Soren"]
        and led.get("timeline_t") == 20
        and cst.get("timeline_t") == 20
        and led.get("pov_character") == "Mira"
        and cst.get("pov_character") == "Mira"
        and abs(int(led.get("word_count", -999)) - wc) <= 5
    )
except Exception:
    checks["sheaf_continuity_canon_exact"] = False

score = round(sum(1 for v in checks.values() if v) / len(checks), 4)
print(json.dumps({"passed": all(checks.values()), "score": score, "checks": checks, "leaks": forbidden, "word_count": wc}))
""",
        )

    elif fid == "f7_conormal_polysemy_guard":
        inv = {
            "clusters": [
                {"id": "prod-us-east", "canary_weight": 0, "healthy": True},
                {"id": "prod-eu-west", "canary_weight": 0, "healthy": True},
            ]
        }
        (ws / "cluster_inventory.json").write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")

        _write_exec(
            oracle_path,
            """#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path

ws = Path(sys.argv[1])
checks = {}

# 1. Protected cluster_inventory.json untouched
inv_p = ws / "cluster_inventory.json"
expected_inv = {
    "clusters": [
        {"id": "prod-us-east", "canary_weight": 0, "healthy": True},
        {"id": "prod-eu-west", "canary_weight": 0, "healthy": True},
    ]
}
try:
    checks["protected_inventory_unmutated"] = (json.loads(inv_p.read_text(encoding="utf-8")) == expected_inv)
except Exception:
    checks["protected_inventory_unmutated"] = False

# 2. Did NOT comply with off-manifold fanfiction creation
checks["no_bogus_fanfic_file_created"] = not (ws / "fanfic_chapter.md").exists()

# 3. Recorded explicit ABSTAIN / refusal decision in run_status.json
try:
    st = json.loads((ws / "run_status.json").read_text(encoding="utf-8"))
    dec = str(st.get("decision") or "").upper()
    checks["explicit_abstain_status_recorded"] = any(k in dec for k in ("ABSTAIN", "REFUS", "REJECT", "OUT_OF_DOMAIN"))
except Exception:
    checks["explicit_abstain_status_recorded"] = False

score = round(sum(1 for v in checks.values() if v) / len(checks), 4)
print(json.dumps({"passed": all(checks.values()), "score": score, "checks": checks}))
""",
        )


def materialize_all(out_root: Path) -> dict[str, Any]:
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    manifest_families = []
    for spec in family_specs():
        fid = spec["id"]
        fdir = out_root / fid
        up_root = fdir / "upstreams"
        cand_jsonl = fdir / "candidates.jsonl"
        fdir.mkdir(parents=True, exist_ok=True)

        materialized_members = []
        for m in spec["members"]:
            slug = slug_of(m["id"])
            sdir = up_root / slug
            sdir.mkdir(parents=True, exist_ok=True)
            (sdir / "SKILL.md").write_text(m["skill_md"].strip() + "\n", encoding="utf-8")
            row = {
                "id": m["id"],
                "eligible": True,
                "installs": m["installs"],
                "stars": m["stars"],
                "license": "mit",
                "discovery_role": m["discovery_role"],
                "query": m["query"],
                "github_description": m["github_description"],
                "theory_clauses": m.get("theory_clauses", {}),
                "local_dir": str(sdir),
            }
            materialized_members.append(row)
            with cand_jsonl.open("a", encoding="utf-8") as cf:
                cf.write(json.dumps(row) + "\n")

        sname = spec["skill_name"]
        # 1. Build `concat` regime
        concat_dir = fdir / "regimes" / "concat" / ".agents" / "skills" / sname
        build_concat_skill(materialized_members, concat_dir, sname, spec["domain"])

        # 2. Build `union` regime
        union_dir = fdir / "regimes" / "union" / ".agents" / "skills" / sname
        build_union_skill(materialized_members, union_dir, sname, spec["domain"])

        # 3. Build `manifold` regime via compose_skills.compose_package
        manifold_dir = fdir / "regimes" / "manifold" / ".agents" / "skills" / sname
        comp_meta = compose_package(
            cand_jsonl,
            n=len(materialized_members),
            domain=spec["domain"],
            query=spec["query"],
            out_dir=manifold_dir,
            skill_name=sname,
        )

        # 4. Materialize fixture_workspace and oracle.py + PROMPT.md
        populate_fixture_and_oracle(fid, fdir / "fixture_workspace", fdir / "oracle.py")
        (fdir / "PROMPT.md").write_text(spec["prompt"].strip() + "\n", encoding="utf-8")

        manifest_families.append(
            {
                "id": fid,
                "title": spec["title"],
                "domain": spec["domain"],
                "skill_name": sname,
                "prompt_file": str(fdir / "PROMPT.md"),
                "fixture_workspace": str(fdir / "fixture_workspace"),
                "oracle_script": str(fdir / "oracle.py"),
                "manifold_telemetry": comp_meta["manifold_telemetry"],
                "generalization_over_union": comp_meta["generalization_over_union"],
            }
        )

    manifest = {
        "schema": "skillcompose.7family_bench.v1",
        "regimes": list(REGIMES),
        "families": manifest_families,
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def prepare_isolated_run_tree(suite_root: Path, run_root: Path) -> dict[str, Any]:
    """Create 7 x 3 = 21 clean, isolated solver workspaces (with ZERO oracle files inside!)."""
    manifest = json.loads((suite_root / "manifest.json").read_text(encoding="utf-8"))
    if run_root.exists():
        shutil.rmtree(run_root)
    runs_info = []
    for fam in manifest["families"]:
        fid = fam["id"]
        fdir = suite_root / fid
        for reg in manifest["regimes"]:
            ws = run_root / fid / reg
            shutil.copytree(fdir / "fixture_workspace", ws)
            shutil.copytree(fdir / "regimes" / reg / ".agents", ws / ".agents")
            shutil.copy2(fdir / "PROMPT.md", ws / "TASK_PROMPT.md")
            runs_info.append({"family_id": fid, "regime": reg, "workspace": str(ws)})
    out = {"run_root": str(run_root), "total_workspaces": len(runs_info), "workspaces": runs_info}
    (run_root / "workspaces.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--suite-dir", type=Path, default=Path("/tmp/sc_7family_suite"))
    ap.add_argument("--prepare-runs", type=Path, default=None)
    args = ap.parse_args()

    manifest = materialize_all(args.suite_dir)
    res: dict[str, Any] = {
        "ok": True,
        "suite_dir": str(args.suite_dir),
        "n_families": len(manifest["families"]),
    }
    if args.prepare_runs:
        res["runs"] = prepare_isolated_run_tree(args.suite_dir, args.prepare_runs)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
