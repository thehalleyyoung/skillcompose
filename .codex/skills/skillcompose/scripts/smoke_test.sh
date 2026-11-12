#!/usr/bin/env bash
# Offline smoke for skillremix scripts (no skills.sh network required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/scripts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$S/parse_args.py" --domain writing --discover-only hello \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['domain']=='writing' and d['discover_only'] and d['mode']=='upgrade'"

python3 "$S/parse_args.py" --n 3 --domain writing \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['mode']=='remix' and d['n']==3"

set +e
python3 "$S/parse_args.py" --n 1 >/dev/null 2>"$TMP/n1.err"
n1=$?
set -e
test "$n1" -ne 0

cat > "$TMP/c.jsonl" <<'EOF'
{"id":"mega/x@y","installs":200000,"stars":9000}
{"id":"mid/a@b","url":"https://github.com/mid/a","installs":500,"stars":40,"license":"mit"}
{"id":"mid/c@d","url":"https://github.com/mid/c","installs":400,"stars":30,"license":"mit"}
{"id":"other/e@outline-plan","url":"https://github.com/other/e","installs":300,"stars":25,"license":"apache-2.0"}
{"id":"ghost/z@w","installs":2,"stars":0}
EOF
python3 "$S/pick_eligible.py" --candidates "$TMP/c.jsonl" --seed zz --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('n_eligible', d.get('n_middling'))==4; assert d['band']=='eligible'; assert d['chosen']['id'] in ('mega/x@y','mid/a@b','mid/c@d','other/e@outline-plan')"

# Optional ceiling still works when explicitly requested
python3 "$S/pick_eligible.py" --candidates "$TMP/c.jsonl" --seed zz --max-installs 8000 --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('n_eligible', d.get('n_middling'))==3; assert d['chosen']['id']!='mega/x@y'"

python3 "$S/pick_n_eligible.py" --candidates "$TMP/c.jsonl" --n 2 --seed remix --write-chosen "$TMP/chosen_n.json" --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['decision']=='PASS' and len(d['chosen'])==2; assert d.get('n_eligible', d.get('n_middling'))==4"

# Practice-support expands when n is large (offline)
python3 - <<PY
import sys
from pathlib import Path
sys.path.insert(0, "$S")
from discover_skills import build_query_plan, resolve_practice_support, LARGE_N_THRESHOLD
from pick_n_eligible import pick_diverse
assert resolve_practice_support("auto", LARGE_N_THRESHOLD) is True
assert resolve_practice_support("auto", 2) is False
plan_small = build_query_plan("writing", "", [], False, 6)
plan_large = build_query_plan("writing", "", [], True, 14)
assert all(r == "domain_core" for _, r in plan_small)
assert any(r == "practice_support" for _, r in plan_large)
assert len(plan_large) > len(plan_small)
rows = [
  {"id": f"o{i}/r@skill{i}", "installs": 200, "discovery_role": "domain_core" if i < 4 else "practice_support"}
  for i in range(8)
]
chosen = pick_diverse(rows, 6, "seed", practice_mix=True)
roles = {c["discovery_role"] for c in chosen}
assert "domain_core" in roles and "practice_support" in roles
print("practice_support_ok")
PY

mkdir -p "$TMP/audits" "$TMP/skill"
cat > "$TMP/skill/SKILL.md" <<'EOF'
---
name: demo
description: demo skill
---
# demo
Do the thing.
EOF
python3 "$S/audit_incumbent.py" --skill-dir "$TMP/skill" --out "$TMP/audits/mid_a_b.json" --themes-out "$TMP/themes.json" --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert len(d['proposed_phases'])==4; assert d['proposed_phases'][0]['kind']=='unify'"
test -f "$TMP/themes.json"
python3 -c "import json; d=json.load(open('$TMP/themes.json')); assert d['forge_rounds']==50; assert len(d['phases'])==4"
# second audit copy for second member
cp "$TMP/audits/mid_a_b.json" "$TMP/audits/other_e_outline-plan.json"

# Fix audit filenames to match safe_id of chosen ids
python3 - <<PY
import json, re
from pathlib import Path
chosen = json.loads(Path("$TMP/chosen_n.json").read_text())
aud = Path("$TMP/audits")
sample = json.loads((aud/"mid_a_b.json").read_text())
for m in chosen["chosen"]:
    sid = re.sub(r"[^a-zA-Z0-9._-]+", "_", m["id"])[:120]
    (aud/f"{sid}.json").write_text(json.dumps(sample, indent=2))
PY

python3 "$S/propose_remix.py" --chosen-n "$TMP/chosen_n.json" --audits "$TMP/audits" \
  --out "$TMP/remix_plan.json" --domain writing --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['decision']=='PASS'"
test -f "$TMP/remix_plan.json"
test -f "$TMP/remix_plan.md"

python3 "$S/license_gate.py" --license mit --json | python3 -c "import json,sys; assert json.load(sys.stdin)['decision']=='PASS'"
set +e
python3 "$S/license_gate.py" --license gpl-3.0 --json > "$TMP/lg.json"
lg_ec=$?
set -e
python3 -c "import json; assert json.load(open('$TMP/lg.json'))['decision']=='FAIL'"
# license-gate-exit2 ship: FAIL uses exit 2 (not 1)
test "$lg_ec" -eq 2

python3 "$S/write_upgrade_plan.py" --themes "$TMP/themes.json" --out "$TMP/UPGRADE_PLAN.md" --incumbent mid/a@b
test -s "$TMP/UPGRADE_PLAN.md"

python3 "$S/init_fork.py" --src "$TMP/skill" --dest "$TMP/fork" --fork-name demo-upgraded \
  --dual-installer "$S/install_skill_dual.sh" --json
test -f "$TMP/fork/UPSTREAM.md"
test -f "$TMP/fork/install.sh"

set +e
python3 "$S/forge_log.py" validate --log "$TMP/empty.jsonl" --rounds 2 --json > "$TMP/v.json"
set -e
python3 -c "import json; assert json.load(open('$TMP/v.json'))['decision']=='FAIL'"

# Thin char append must refuse
set +e
python3 "$S/forge_log.py" append --log "$TMP/thin.jsonl" --round 1 --total 2 --theme t \
  --gap g --addition a --commit deadbeef --compared-to '["x"]' --surfaces '["procedure","code","docs"]' \
  --chars-changed 50 --min-chars 1000 --json >"$TMP/thin_out.json" 2>"$TMP/thin.err"
thin_ec=$?
set -e
test "$thin_ec" -ne 0

# Valid mini-log: 2 enhance rounds at rounds 11-12 would need full 50 for strict; use --no-strict-phases for unit smoke
python3 "$S/forge_log.py" append --log "$TMP/ok.jsonl" --round 1 --total 2 --theme P1-unify \
  --kind unify --unify --gap g --addition a --commit aaa111 --compared-to '["x"]' \
  --surfaces '["procedure","code","docs"]' --chars-changed 1500 --min-chars 1000 --json >/dev/null
python3 "$S/forge_log.py" append --log "$TMP/ok.jsonl" --round 2 --total 2 --theme P1-unify \
  --kind unify --unify --gap g --addition a --commit bbb222 --compared-to '["x"]' \
  --surfaces '["procedure","code","proof"]' --chars-changed 1500 --min-chars 1000 --json >/dev/null
python3 "$S/forge_log.py" validate --log "$TMP/ok.jsonl" --rounds 2 --min-chars 1000 \
  --no-strict-phases --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['decision']=='PASS'"

# Phase helper
python3 "$S/forge_phases.py" --round 21 --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['kind']=='metrics'"
python3 "$S/forge_phases.py" --round 45 --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['kind']=='awesome'"

# Refuse wrong kind on P1
set +e
python3 "$S/forge_log.py" append --log "$TMP/badkind.jsonl" --round 3 --total 50 --theme enhance \
  --kind enhance --gap g --addition a --commit ccc333 --compared-to '["x"]' \
  --surfaces '["procedure","code","docs"]' --chars-changed 1500 --min-chars 1000 --json \
  >"$TMP/badkind.out" 2>"$TMP/badkind.err"
bk=$?
set -e
test "$bk" -ne 0

# Juxtaposition package must FAIL unify_wholeness
mkdir -p "$TMP/juxta/skills/a-upgraded" "$TMP/juxta/skills/b-upgraded"
printf '# a\n' > "$TMP/juxta/skills/a-upgraded/SKILL.md"
printf '# b\n' > "$TMP/juxta/skills/b-upgraded/SKILL.md"
printf '# thin router\ncall a then b\n' > "$TMP/juxta/SKILL.md"
printf '## Install\n\n## Use (after install)\n\n```text\n/x\n```\n' > "$TMP/juxta/README.md"
set +e
python3 "$S/unify_wholeness.py" --package "$TMP/juxta" --rounds 2 --min-chars 1000 --skip-forge --json >"$TMP/u.json"
u_ec=$?
set -e
python3 -c "import json; d=json.load(open('$TMP/u.json')); assert d['decision']=='FAIL'; assert d['failed_predicates']"
test "$u_ec" -ne 0


# --- Refusal suite (ships: contradictory-flags, propose-audits) ---
# Contradictory: --status + --resume (parse_args → exit 2)
set +e
python3 "$S/parse_args.py" --status --resume --wip "$TMP" >"$TMP/contra.json" 2>"$TMP/contra.err"
contra=$?
set -e
python3 -c "import json; d=json.load(open('$TMP/contra.json')); assert d.get('ok') is False; assert d.get('error')=='contradictory_flags'"
test "$contra" -eq 2

# Contradictory: --resume + --discover-only
set +e
python3 "$S/parse_args.py" --resume --discover-only --wip "$TMP" >"$TMP/contra2.json" 2>"$TMP/contra2.err"
contra2=$?
set -e
python3 -c "import json; d=json.load(open('$TMP/contra2.json')); assert d.get('ok') is False; assert d.get('error')=='contradictory_flags'"
test "$contra2" -eq 2

# propose without audits dir must FAIL (exit 2) unless --allow-missing-audits
mkdir -p "$TMP/empty_audits"
set +e
python3 "$S/propose_remix.py" --chosen-n "$TMP/chosen_n.json" --audits "$TMP/empty_audits" \
  --out "$TMP/propose_fail.json" --domain writing --json >"$TMP/propose.out" 2>"$TMP/propose.err"
prop=$?
set -e
test "$prop" -eq 2
python3 -c "import json; d=json.load(open('$TMP/propose.out')); assert d.get('decision')=='FAIL'"

echo "SMOKE_OK"

