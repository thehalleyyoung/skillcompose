---
name: ml-paper-manifold
description: >-
  Lawvere-Amari generative manifold & Kleisli-composed research skill (post-research ml conference paper writing latex booktabs venue templates claim2evidence figures citations peer review) synthesized by /skillcompose. Maps each input x onto Fisher-Rao tangent coordinates and anti-unified logical fibers to synthesize global sheaf-consistent structured outputs beyond the union of member skills.
---

# `ml-paper-manifold` — Lawvere–Amari Generative Manifold Transducer (`/skillcompose`)

This skill is **not** a prompt concatenation ($\bigwedge_i Q_i$) nor a discrete router/union ($\bigcup_i s_i$). It compiles 8 landmark modules into a **Conditional Statistical–Logical Manifold** $\mathfrak{G}_{\mathcal{M}}$ ($x \xrightarrow{\sigma^*} \theta^*(x) \xrightarrow{K_{\theta^*}} \Gamma(\mathcal{U}, \mathcal{F}_{\theta^*(x)})$) with anti-unified tangent axes (`spec_modality`, `execution_regime`, `verification_channel`, `failure_semantics`, `gluing_topology`):

1. **`spec_grounding` (`θ=[+0.30, +1.05, +0.78, -0.28, -0.47, +0.02]`) — [latex-fmt](./references/members/latex-fmt.md)**: 
2. **`static_contract` (`θ=[-0.73, -0.23, +0.15, -0.32, -0.23, -0.40]`) — [citation-verifier](./references/members/citation-verifier.md)**: 
3. **`static_contract` (`θ=[+0.59, +0.28, -0.72, -0.82, +0.47, -0.11]`) — [citation-management](./references/members/citation-management.md)**: 
4. **`synthesis` (`θ=[+1.43, -0.00, -0.29, +0.74, -0.13, -0.07]`) — [anti-defensive-writing](./references/members/anti-defensive-writing.md)**: 
5. **`synthesis` (`θ=[+0.18, -0.65, +0.86, -0.26, +0.31, +0.36]`) — [conference-paper-writing](./references/members/conference-paper-writing.md)**: 
6. **`synthesis` (`θ=[-0.18, -1.24, +0.14, +0.27, -0.04, -0.16]`) — [research-paper-writing](./references/members/research-paper-writing.md)**: 
7. **`synthesis` (`θ=[-0.92, +0.87, +0.07, +0.70, +0.50, -0.02]`) — [paper-writing-skill](./references/members/paper-writing-skill.md)**: 
8. **`adversarial_verify` (`θ=[-0.67, -0.08, -0.98, -0.03, -0.41, +0.36]`) — [peer-review](./references/members/peer-review.md)**: 

Manifold atlas & chart equations: [MANIFOLD_ATLAS.md](./references/MANIFOLD_ATLAS.md) · Wiring contract: [WIRING_CONTRACT.md](./references/WIRING_CONTRACT.md).

## Mandatory Execution Protocol

1. **Stage 1 — Chart Projection & Contradiction-Free Fiber Lock ($\sigma^* : \mathcal{X} \to \Theta$)**:
   - Project the user's task onto the manifold before writing deliverables:
     ```bash
     python3 .gemini/skills/ml-paper-manifold/scripts/project_manifold.py \
       --input "<task_summary_or_prompt_file>" \
       --out "/tmp/manifold_section_ml-paper-manifold_$$.json"
     ```
   - If `project_manifold.py` exits `2` (`ABSTAIN_OFF_MANIFOLD`), halt cleanly, do **not** generate off-domain deliverables, and report refusal.
   - Read the landmark module references in `./references/members/` needed to cover all required output facets. Whenever two landmarks specialize conflicting narrow shortcuts (which would collapse under naive conjunction $\bigwedge_i Q_i$), resolve them via `resolved_lawvere_fiber` and the **Conormal Universal Invariants** ($\Phi_{\text{core}}$: exogenous verification, non-silent quarantine/rollback, causal/epistemic soundness, and sheaf global section $\delta^0(y)=0$), locking your chosen invariants in `"/tmp/locked_contract_ml-paper-manifold_$$.json"`.
2. **Stage 2 — Geodesic Synthesis & Global Sheaf Gluing ($\Gamma(\mathcal{U}, \mathcal{F}) = \ker \delta^0$)**:
   - Synthesize the complete structured output bundle $y = (y_u)_{u \in \mathcal{U}}$ governed by `map_structured_output` (recombining capabilities across landmarks rather than dropping facets).
   - Enforce Sheaf Restriction & Pullback Invariant (`claim_provenance_table`): `every quantitative claim cites source_id + exact numerator/denominator check`. Coupled JSON/artifact views must satisfy exact restriction equality ($\delta^0(y) = 0$) on all shared overlap keys.
3. **Stage 3 — Exogenous Observation & Read-Only Post-Dominator Gate ($\mathcal{W}(S_{\text{gate}}) = \emptyset$)**:
   - Run deterministic tests and certify via the read-only post-dominator & sheaf coboundary gate (passing `--glue left.json:right.json:key1,key2` for coupled JSON views):
     ```bash
     python3 .gemini/skills/ml-paper-manifold/scripts/verify_dominator_gate.py \
       --manifold-section "/tmp/manifold_section_ml-paper-manifold_$$.json" \
       --contract "/tmp/locked_contract_ml-paper-manifold_$$.json" \
       --protect <each_deliverable_file> \
       --glue <left_view.json>:<right_view.json>:<shared_key1>,<shared_key2> \
       --cmd "<your_verification_test_command>"
     ```
   - **Never declare `DONE` until `verify_dominator_gate.py` prints `"decision": "PASS"` (exit `0`).**
