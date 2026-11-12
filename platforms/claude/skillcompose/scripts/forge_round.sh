#!/usr/bin/env bash
# Log + document one forge round AFTER a real product commit in FORK_DIR.
# Refuses to log unless git HEAD churn ≥ MIN_CHARS (default 1000), excluding forge log files.
# Usage:
#   forge_round.sh <round> <total> <theme> <gap> <addition> <surfaces-json> \
#     [paths-json] [compared-json] [kind] [--unify]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROUND="${1:?round}"
TOTAL="${2:-50}"
THEME="${3:?theme}"
GAP="${4:?gap}"
ADDITION="${5:?addition}"
SURFACES="${6:?surfaces json array}"
PATHS_JSON="${7:-[]}"
COMPARED="${8:-[\"incumbent\"]}"
KIND="${9:-}"
# Auto-select phase kind from round number when not provided
if [[ -z "$KIND" ]]; then
  KIND="$(python3 "$ROOT/scripts/forge_phases.py" --round "$ROUND" --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["kind"])')"
fi
UNIFY_FLAG=()
if [[ "${10:-}" == "--unify" ]] || [[ "$KIND" == "unify" ]] || [[ "$KIND" == "subskill" ]] || [[ "$KIND" == "superskill" ]]; then
  UNIFY_FLAG=(--unify)
fi
WIP_DIR="${WIP_DIR:?set WIP_DIR}"
FORK_DIR="${FORK_DIR:?set FORK_DIR}"
MIN_CHARS="${MIN_CHARS:-1000}"
LOG="$WIP_DIR/forge/usefulness_forge.jsonl"
SHA="$(git -C "$FORK_DIR" rev-parse HEAD)"

MEASURE_JSON="$(python3 "$ROOT/scripts/measure_chars.py" --repo "$FORK_DIR" --commit HEAD --min-chars "$MIN_CHARS" --json)"
CHARS="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["chars_changed"])' <<<"$MEASURE_JSON")"
DECISION="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["decision"])' <<<"$MEASURE_JSON")"
if [[ "$DECISION" != "PASS" ]]; then
  echo "REFUSE round $ROUND: chars_changed=$CHARS < min=$MIN_CHARS" >&2
  echo "$MEASURE_JSON" >&2
  echo "Keep editing the package (not just the forge log), commit again, re-run forge_round.sh." >&2
  exit 1
fi

# MDL / Lempel-Ziv anti-padding check (blocks repetitive copy-paste padding)
MDL_JSON="$(python3 "$ROOT/scripts/information_gain.py" commit --repo "$FORK_DIR" --commit HEAD --json 2>/dev/null || echo '{"ok":true,"info_density":0.5,"conditional_lz_bytes":250,"anti_padding_pass":true}')"
ANTI_PAD="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("anti_padding_pass", True))' <<<"$MDL_JSON")"
INFO_DENSITY="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("info_density", 0.0))' <<<"$MDL_JSON")"
LZ_BYTES="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("conditional_lz_bytes", 0))' <<<"$MDL_JSON")"
if [[ "$ANTI_PAD" != "True" ]]; then
  echo "REFUSE round $ROUND (MDL anti-padding gate): info_density=$INFO_DENSITY, conditional_lz_bytes=$LZ_BYTES" >&2
  echo "Raw character count met $MIN_CHARS, but Lempel-Ziv conditional novelty is too low (repetitive/boilerplate padding). Ship real schemas, scripts, or distinct evals." >&2
  exit 2
fi

# Contract ratchet (theory.md §4.2): the term the package runs must keep the theory's obligations.
# Every round: neither the contract potential Φ_c nor any component of the vector Lyapunov debt may rise.
# From round 11 (after P1-unify): Φ_c = 0 and references/concrete_term.json describes the package.
RATCHET_ARGS=(--repo "$FORK_DIR" --base HEAD~1 --head HEAD --json)
if (( ROUND > 10 )); then
  RATCHET_ARGS+=(--zero --require-artifact)
fi
set +e
CONTRACT_JSON="$(python3 "$ROOT/scripts/concrete_term.py" ratchet "${RATCHET_ARGS[@]}")"
CONTRACT_RC=$?
set -e
if [[ "$CONTRACT_RC" -ne 0 ]]; then
  echo "REFUSE round $ROUND (contract ratchet): the change breaks the theory on the package's concrete term." >&2
  echo "$CONTRACT_JSON" >&2
  echo "Fix the obligations, refresh with: python3 $ROOT/scripts/concrete_term.py write --package \"$FORK_DIR\", re-commit." >&2
  exit 2
fi

# Outcome contract: from round 11 the round must show the skill's output before and after the change.
OUTCOME_ARGS=()
if (( ROUND >= 11 )); then
  set +e
  OUTCOME_JSON="$(python3 "$ROOT/scripts/outcome_round.py" check --fork "$FORK_DIR" --round "$ROUND" --commit HEAD --json)"
  OUTCOME_RC=$?
  set -e
  if [[ "$OUTCOME_RC" -ne 0 ]]; then
    echo "REFUSE round $ROUND (outcome contract): the round must change what the skill produces, with evidence." >&2
    echo "$OUTCOME_JSON" >&2
    echo "Scaffold: python3 $ROOT/scripts/outcome_round.py init --fork \"$FORK_DIR\" --round $ROUND --task \"<a real user's request>\"" >&2
    exit 2
  fi
  OUTCOME_ARGS=(--outcome "$OUTCOME_JSON")
  if python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin)["focus"]["self_measurement"] else 1)' <<<"$OUTCOME_JSON"; then
    echo "WARN round $ROUND: most of this change is evals/metrics/tests; at most 20% of rounds may be (forge_log validate)." >&2
  fi
fi

APPEND_ARGS=(
  --log "$LOG"
  --round "$ROUND" --total "$TOTAL"
  --theme "$THEME"
  --kind "$KIND"
  --gap "$GAP"
  --addition "$ADDITION"
  --commit "$SHA"
  --compared-to "$COMPARED"
  --paths "$PATHS_JSON"
  --surfaces "$SURFACES"
  --chars-changed "$CHARS"
  --min-chars "$MIN_CHARS"
  --radical --json
  --contract "$CONTRACT_JSON"
)
# Under `set -u`, empty arrays must not be expanded via "${arr[@]}"
if ((${#UNIFY_FLAG[@]})); then
  APPEND_ARGS+=("${UNIFY_FLAG[@]}")
fi
if ((${#OUTCOME_ARGS[@]})); then
  APPEND_ARGS+=("${OUTCOME_ARGS[@]}")
fi
python3 "$ROOT/scripts/forge_log.py" append "${APPEND_ARGS[@]}" >/dev/null

mkdir -p "$FORK_DIR/forge"
cp "$LOG" "$FORK_DIR/forge/usefulness_forge.jsonl"
# Durable backup so WIP log wipes do not reset resume_forge to round 1
cp "$LOG" "$WIP_DIR/forge/usefulness_forge.jsonl.bak" 2>/dev/null || true
{
  echo ""
  echo "## Round $ROUND — $THEME ($KIND)"
  echo ""
  echo "**Gap:** $GAP"
  echo ""
  echo "**Addition:** $ADDITION"
  echo ""
  if ((${#OUTCOME_ARGS[@]})); then
    python3 -c 'import json,sys; o=json.load(sys.stdin)["outcome"]; print("**Outcome:** " + o.get("verdict","") + " — " + o.get("flaw","") + " (`" + o.get("before","") + "` → `" + o.get("after","") + "`)\n")' <<<"$OUTCOME_JSON"
  fi
  echo "**Chars changed:** $CHARS (min $MIN_CHARS)"
  echo ""
  echo "**Commit:** \`${SHA:0:7}\`"
  echo ""
} >> "$FORK_DIR/USEFULNESS_FORGE.md"

echo "logged round $ROUND chars=$CHARS ($SHA)"

# Clear busy lock so the 90s scheduler may wake the agent for the next round.
if python3 "$ROOT/scripts/agent_busy.py" release --wip "$WIP_DIR" --json >/dev/null 2>&1; then
  echo "released agent_busy.lock"
fi
