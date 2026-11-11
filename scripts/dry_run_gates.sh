#!/usr/bin/env bash
# Fixture dry-run for skillremix refusal/PASS oracles (transfer: gate dry-run before Done).
# Note: includes smoke-refusal-suite — may take ~30–45s offline.
# --fast skips smoke (dev loop only). Publish / Done requires a full run (no --fast).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAST=0
FORCE_FAST=0
for arg in "$@"; do
  case "$arg" in
    --fast) FAST=1 ;;
    --force-fast) FORCE_FAST=1; FAST=1 ;;
    -h|--help)
      echo "Usage: $0 [--fast|--force-fast]"
      echo "  --fast        skip smoke (not valid for publish)"
      echo "  --force-fast  allow --fast to overwrite a mode=full stamp"
      exit 0
      ;;
    *)
      echo "unknown arg: $arg (try --fast / --force-fast)" >&2
      exit 2
      ;;
  esac
done
# Protect full stamp from accidental --fast clobber
if [[ "$FAST" -eq 1 && "$FORCE_FAST" -eq 0 ]]; then
  STAMP="$ROOT/review/last_dry_run.json"
  if [[ -f "$STAMP" ]]; then
    cur=$(python3 -c "import json; print(json.load(open('$STAMP')).get('mode',''))" 2>/dev/null || true)
    if [[ "$cur" == "full" ]]; then
      echo "dry_run_gates: Refusing --fast — stamp is mode=full (would clobber publish-ready state)." >&2
      echo "  Re-run without --fast, or pass --force-fast to overwrite." >&2
      exit 2
    fi
  fi
fi
fail=0
echo "dry_run_gates: check_skill_md ..."
python3 "$ROOT/scripts/check_skill_md.py" --root "$ROOT" --json || fail=1
run_metric() {
  local id="$1"
  local out
  echo "dry_run_gates: measuring $id ..."
  out="$(python3 "$ROOT/metrics/$id/measure.py")"
  echo "$out"
  python3 -c "import json,sys; d=json.loads(sys.argv[1]); v=d.get('values') or {}; pr=v.get('pass_rate'); 
import sys as S
ok = pr is None or float(pr) >= 1.0
S.exit(0 if ok and d.get('ok') is not False else 1)" "$out" || fail=1
}
if [[ "${SKILLREMIX_IN_DRY_RUN_PROTECT:-0}" -eq 0 ]]; then
  run_metric adversarial-args
  run_metric remix-coherence
  run_metric status-pack-bytes
  run_metric propose-audits-gate
  run_metric local-only-cache
  run_metric principled-lift
  run_metric dry-run-protect
  if [[ "$FAST" -eq 0 ]]; then
    run_metric smoke-refusal-suite
  else
    echo "dry_run_gates: skipping smoke-refusal-suite (--fast)"
  fi
fi
mkdir -p "$ROOT/review"
MODE_JSON=full
[[ "$FAST" -eq 1 ]] && MODE_JSON=fast
python3 -c "import json; from datetime import datetime, timezone; from pathlib import Path; p=Path('$ROOT')/'review'/'last_dry_run.json'; p.write_text(json.dumps({'mode':'$MODE_JSON','pass':True,'at':datetime.now(tz=timezone.utc).isoformat()}, indent=2)+'\n'); print('dry_run_gates: stamped', p, 'mode=$MODE_JSON')"

if [[ "$fail" -ne 0 ]]; then
  echo "dry_run_gates: FAIL — fix metrics before ship_check publish" >&2
  exit 2
fi
if [[ "$FAST" -eq 1 ]]; then
  echo "dry_run_gates: PASS (fast — smoke skipped; full run required for publish)"
else
  echo "dry_run_gates: PASS"
  python3 "$ROOT/scripts/assert_dry_run_full.py" --root "$ROOT" --json
fi
exit 0
