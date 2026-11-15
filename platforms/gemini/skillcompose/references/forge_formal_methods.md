# Forge as a formal methods problem (all 50 rounds)

This is the operational semantics of the `/skillcompose` forge, aligned with
`references/theory.md` (Kleisli term \(\tau(P)\), contract potential \(\Phi_c\),
outcome contract, carrier closure). It applies to **every** round \(r \in \{1,\dots,50\}\).

---

## 1. Objects

| Symbol | Meaning |
|---|---|
| \(P_r\) | Skill package after round \(r\) (files + `SKILL.md` invocations) |
| \(\tau(P)\) | Concrete term: scripts `SKILL.md` runs, in order (`concrete_term.py`) |
| \(\Phi_c(P)\) | Contract potential: count of broken wiring/carrier obligations |
| \(d(P)\) | Vector Lyapunov debt (componentwise; no hiding upstream regressions) |
| \(\mathcal{X}\) | Space of **task definitions** a real user of the domain might issue |
| \(\theta : \mathcal{X} \to \prod_a A_a\) | Finite **task chart**: each axis \(A_a\) is a small discrete set |
| \(C_r \subseteq \prod_a A_a\) | **Coverage** after round \(r\) (which chart cells have been exercised) |
| \(\varphi\) | A **desired output property** (reader criterion / gate / score threshold) |
| \(K_P(x)\) | What package \(P\) produces on task \(x\) (the skill run) |

The atlas \(\{A_a\}\) is domain-specific and lives at `forge/task_space/atlas.json`.
Coordinates for round \(r\) live at `forge/outcomes/rNN/task_coords.json` (rounds ≥11)
or `forge/task_space/rounds/rNN.json` (rounds 1–10).

---

## 2. Problem statement

**Given** an initial composed package \(P_0\) and a task chart \(\theta\),

**find** a sequence \(P_0 \to P_1 \to \cdots \to P_{50}\) such that for every round \(r\):

1. **Contract ratchet (safety).**
   \(\Phi_c(P_r) \le \Phi_c(P_{r-1})\) and \(d(P_r) \le d(P_{r-1})\) componentwise.
   For \(r \ge 11\): \(\Phi_c(P_r) = 0\) and `concrete_term.json` matches \(\tau(P_r)\).

2. **Task expansion (liveness on \(\mathcal{X}\)).**
   Round \(r\) nominates a task \(x_r\) with coordinates \(\theta_r = \theta(x_r)\).
   Novelty: \(\theta_r\) is not already in \(C_{r-1}\), **or** (allowed only if the atlas
   is already fully covered) Hamming distance to nearest prior cell is maximized and
   a new **property** \(\varphi_r\) is targeted.
   Then \(C_r := C_{r-1} \cup \{\theta_r\}\).

3. **Desired-output improvement (liveness on \(Y\)).**
   - Rounds **1–10 (unify):** \(x_r\) is a package-obligation task; “output” is the
     package satisfying a named unify predicate / \(\Phi_c\) component. Round must
     close that cell without raising \(\Phi_c\).
   - Rounds **11–50:** run \(y^- = K_{P_{r-1}}(x_r)\), record flaw against \(\varphi_r\),
     edit the skill, run \(y^+ = K_{P_r}(x_r)\). Require verbatim evidence and
     \(\texttt{verdict}=\texttt{better}\) as the success case (same/worse logged as misses).

4. **Anti-self-measurement.**
   Majority of product churn is skill procedure/scripts/docs that change \(K_P\),
   not evals that only score \(K_P\).

5. **Product lower bound.**
   \(\ge 1000\) changed product characters across \(\ge 3\) surfaces; one commit.

**Ship** when \(r=50\), \(\Phi_c(P_{50})=0\), coverage and outcome audits pass, and
`AWESOME_PROOF.md` cites a real artifact (or ≥99% third-party bug).

---

## 3. Why this matches the theory

| Theory failure / law | Forge obligation |
|---|---|
| DPI / no exogenous eyes | Every improve step is judged on **output files** + read-only gates |
| Self-grading correlation | Excerpts must be verbatim in before/after; instrumentation share capped |
| Carrier loss | \(\Phi_c\) / carrier checks every round |
| Union rank deficit | Task **chart coverage** forces new cells in \(\mathcal{X}\), not repeats |
| Concat collapse | Edits must keep \(\Phi_c=0\) (consistent term), not pile contradictory prose |
| Sheaf / glue | Multi-view gates remain in \(\tau(P)\); awesome rounds exercise end-to-end artifacts |

Improving only one favorite scene forever would cover a single cell of \(\mathcal{X}\).
The forge’s second objective is **measure-and-expand** the space of tasks the skill
actually handles under stated \(\varphi\).

---

## 4. Phase specialization (still one problem)

| Rounds | Kind | \(x_r\) | \(\varphi_r\) focus |
|---:|---|---|---|
| 1–10 | unify | obligation / wiring cell | \(\Phi_c\) component, dead carrier, handoff |
| 11–20 | enhance | real user task on a new chart cell | worst reader flaw in \(y^-\) |
| 21–44 | metrics | held-out task + baseline | rubric score vs baseline; fix until skill wins |
| 45–50 | awesome | artifact-scale task (novel stretch / bug hunt) | ship-blocking proof property |

Rounds **40–50** are not a different problem: they are the same pair of objectives
with harder coverage (prefer uncovered cells; after atlas saturation, new \(\varphi\))
and, from 45, artifact-scale \(x_r\).

---

## 5. Executable checks

```bash
# Atlas (once per forge, early)
python3 scripts/task_space.py init-atlas --fork "$FORK_DIR" --domain writing

# Each round: register coordinates + property before/with outcome init
python3 scripts/task_space.py register --fork "$FORK_DIR" --round "$R" \
  --coords '{"time":"dusk","place":"well","cast":"two"}' \
  --phi "short_vivid" \
  --task-summary "dusk well; two mouths; no lecture"

# Refuse non-novel / invalid coords
python3 scripts/task_space.py check --fork "$FORK_DIR" --round "$R" --json

# Coverage report (ship / status)
python3 scripts/task_space.py coverage --fork "$FORK_DIR" --json
```

`forge_round.sh` runs `task_space.py check` for **every** round.
`outcome_round.py` for rounds ≥11 requires `task_coords.json` beside `task.md`.
`ship_check.py` requires atlas present and coverage audit PASS.

---

## 6. Invariants (monitorable)

Let \(C_r\) be computed from registered coords. A forge log is **sound** only if:

- \(\forall r: \Phi_c(P_r) \le \Phi_c(P_{r-1})\) (and \(=0\) for \(r\ge 11\))
- \(\forall r\ge 11:\) outcome evidence exists and focus is not majority instrumentation
  beyond the global 20% budget
- \(\lvert C_{50}\rvert\) grows: either atlas coverage fraction \(\ge\)
  `min_coverage_fraction` (default 0.5) **or** every round after saturation names a
  distinct \(\varphi_r\) not used before

This is the formal methods reading of “50 rounds of improving specific desired
output **and** the greater space of possible task definitions.”
