#!/usr/bin/env bash
# Legacy Cursor/CLI 90s-spaced forge-round wake helper for /skillremix.
#
# NOTE FOR ANTIGRAVITY (AGY): Do NOT run shell sleep timers in Antigravity!
# In Antigravity, generate the next round prompt via:
#   python3 scripts/forge_phases.py --prompt-round $((R+1)) --wip "$WIP_DIR" --fork "$FORK_DIR" --json
# and call the native `schedule` tool (`DurationSeconds: 90`, `Prompt: <prompt>`), then end your turn.
#
# Legacy Cursor Shell tool usage:
#   block_until_ms: 0
#   notify_on_output: { pattern: "^AGENT_LOOP_TICK_skillremix_forge", reason: "forge wake" }
# Do NOT use bare `bash … &` inside another command — that drops wake notifications.
#
# Emits AGENT_LOOP_TICK_skillremix_forge (+ JSON prompt) so the agent wakes and runs
# ONE round. If the agent is still mid-round (busy lock), waits instead of waking.
#
# Usage:
#   export WIP_DIR=… FORK_DIR=…
#   bash schedule_forge_loop.sh [--from N] [--to N] [--interval 90] [--busy-poll 15]
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FROM=1
TO=50
INTERVAL=90
BUSY_POLL=15
SKIP_IF_BUSY=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM="${2:?}"; shift 2 ;;
    --to) TO="${2:?}"; shift 2 ;;
    --interval) INTERVAL="${2:?}"; shift 2 ;;
    --busy-poll) BUSY_POLL="${2:?}"; shift 2 ;;
    --skip-if-busy) SKIP_IF_BUSY=1; shift ;;
    --no-skip-if-busy) SKIP_IF_BUSY=0; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
WIP_DIR="${WIP_DIR:?set WIP_DIR}"
FORK_DIR="${FORK_DIR:?set FORK_DIR}"

echo "skillremix forge scheduler: rounds ${FROM}–${TO}, interval ${INTERVAL}s, skip_if_busy=$SKIP_IF_BUSY, wip=$WIP_DIR"

r="$FROM"
while [[ "$r" -le "$TO" ]]; do
  sleep "$INTERVAL"

  if [[ "$SKIP_IF_BUSY" -eq 1 ]]; then
    # Agent still awake/mid-round → do NOT wake; poll until free (or lock stale).
    while python3 "$ROOT/scripts/agent_busy.py" check --wip "$WIP_DIR" >/dev/null 2>&1; do
      # Different sentinel — must NOT match notify_on_output ^AGENT_LOOP_TICK_skillremix_forge
      echo "AGENT_LOOP_DEFER_skillremix_forge {\"round\":$r,\"reason\":\"agent_busy\",\"wip\":\"$WIP_DIR\"}"
      sleep "$BUSY_POLL"
    done
  fi

  # If this round was already logged (agent finished early / duplicate arm), skip ahead.
  if [[ -f "$WIP_DIR/forge/usefulness_forge.jsonl" ]]; then
    if python3 - "$WIP_DIR/forge/usefulness_forge.jsonl" "$r" <<'PY'
import json, sys
path, want = sys.argv[1], int(sys.argv[2])
done = set()
try:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(int(json.loads(line).get("round")))
            except Exception:
                pass
except FileNotFoundError:
    pass
sys.exit(0 if want in done else 1)
PY
    then
      echo "AGENT_LOOP_DEFER_skillremix_forge {\"round\":$r,\"reason\":\"already_logged\",\"wip\":\"$WIP_DIR\"}"
      r=$((r + 1))
      continue
    fi
  fi

  PAYLOAD="$(python3 "$ROOT/scripts/forge_phases.py" --prompt-round "$r" --wip "$WIP_DIR" --fork "$FORK_DIR" --json)"
  # Wake sentinel — notify_on_output must match this prefix
  echo "AGENT_LOOP_TICK_skillremix_forge ${PAYLOAD}"
  r=$((r + 1))
done
echo "AGENT_LOOP_DONE_skillremix_forge {\"rounds\":[${FROM},${TO}],\"wip\":\"${WIP_DIR}\"}"
