# `skillcompose` — Proof & Gate Verification Card

## Core Verified Capabilities

| Gate / Invariant | What It Proves |
|---|---|
| `principled-lift` (`submodular_beats_github_top_n`) | Monotone submodular + JSD/NCD selection strictly dominates GitHub Popularity-Top-N on coverage, chain synergy, role entropy, and polysemy rejection (`plaid`, `storybook`), with an online Nemhauser–Wolsey optimality certificate. |
| `principled-lift` (`wiring_compiler_sound`) | Compiled Kleisli graphs pass `type_safety`, `separation_logic`, `dpi_exogenous_grounding`, `dominator_orthogonality`, and `parnas_encapsulation`. |
| `principled-lift` (`reject_gate_bypass_shortcut`) | Static post-dominator reachability rejects any graph where a mutator can reach `DONE` bypassing a read-only gate. |
| `principled-lift` (`reject_parallel_write_race`) | Concurrent Separation Logic frame check rejects parallel tensors with overlapping write/read sets. |
| `principled-lift` (`mdl_catches_padding_passes_code`) | Conditional DEFLATE/Lempel–Ziv novelty rejects repetitive prose padding while passing genuine code/contract commits. |
| `principled-lift` (`compose_and_dominator_gate_enforces_separation_logic`) | `compose_skills.py` synthesizes a Parnas-encapsulated package whose `verify_dominator_gate.py` SHA-256-catches critic mutation (`exit 2`). |
| `adversarial-args` / `remix-coherence` / `propose-audits-gate` / `local-only-cache` / `status-pack-bytes` / `dry-run-protect` / `smoke-refusal-suite` | Full backward-compatible CLI refusal safety (exit code `2`), offline cache determinism, compact status telemetry, and full-mode dry-run stamp protection. |

## Reproducible Verification Commands

```bash
bash scripts/dry_run_gates.sh
python3 metrics/principled-lift/measure.py
```

All 8 gate suites must exit `0` and stamp `review/last_dry_run.json` with `"mode": "full", "pass": true`.
