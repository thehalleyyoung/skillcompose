# Pipeline cheat sheet

Assume `SCRIPTS=~/.gemini/config/skills/skillremix/scripts` and `WIP=…/skillremix-wip-ID`.

```bash
# 0 args
python3 $SCRIPTS/parse_args.py $ARGS | tee $WIP/discovery/args.json

# 1 discover
python3 $SCRIPTS/discover_skills.py --out $WIP/discovery/candidates.jsonl --domain writing --extra "novel" --json
python3 $SCRIPTS/enrich_github.py --candidates $WIP/discovery/candidates.jsonl --out $WIP/discovery/candidates_enriched.jsonl --json
python3 $SCRIPTS/pick_middling.py --candidates $WIP/discovery/candidates_enriched.jsonl --seed $RUN_ID --json | tee $WIP/discovery/pick.json
python3 $SCRIPTS/license_gate.py --chosen $WIP/discovery/chosen.json --json

# 2 clone + fork
git clone --depth 50 "$URL" $WIP/upstream/repo
python3 $SCRIPTS/locate_skill.py --repo $WIP/upstream/repo --skill-name NAME --json
python3 $SCRIPTS/init_fork.py --src "$SKILL_SRC" --dest $WIP/$FORK --fork-name $FORK \
  --chosen $WIP/discovery/chosen.json --dual-installer $SCRIPTS/install_skill_dual.sh --json

# 3 lock phases (not T1–T5)
python3 $SCRIPTS/audit_incumbent.py --skill-dir "$SKILL_SRC" \
  --out $WIP/discovery/audit.json --phases-out $WIP/forge/forge_phases.json --json
python3 $SCRIPTS/write_upgrade_plan.py --phases $WIP/forge/forge_phases.json \
  --out $WIP/$FORK/UPGRADE_PLAN.md --incumbent ID

# 4 rounds (real loop: ≥1000 chars → commit → forge_round.sh)
export WIP_DIR=$WIP FORK_DIR=$WIP/$FORK MIN_CHARS=1000
python3 $SCRIPTS/resume_forge.py next --wip $WIP --json
# … implement multi-surface leap for active kind … commit forge(R/50): …
bash $SCRIPTS/forge_round.sh R 50 THEME "gap" "addition" '["procedure","code","docs"]'

python3 $SCRIPTS/forge_log.py validate --log $WIP/forge/usefulness_forge.jsonl --rounds 50 --min-chars 1000 --strict-phases --json
python3 $SCRIPTS/check_phases.py --phases $WIP/forge/forge_phases.json --log $WIP/forge/usefulness_forge.jsonl --rounds 50 --json

# 5–6 ship + install (needs METRICS.md + AWESOME_PROOF.md)
python3 $SCRIPTS/ship_check.py --fork $FORK_DIR --rounds 50 --min-chars 1000 --json
bash $SCRIPTS/install_skill_dual.sh $FORK_DIR --name $FORK
```

## Remix (`--n N`)

```bash
python3 $SCRIPTS/parse_args.py --n 3 --domain writing | tee $WIP/discovery/args.json
python3 $SCRIPTS/discover_skills.py --out $WIP/discovery/candidates.jsonl --domain writing --json
python3 $SCRIPTS/enrich_github.py --candidates $WIP/discovery/candidates.jsonl --out $WIP/discovery/candidates_enriched.jsonl --json
python3 $SCRIPTS/pick_n_middling.py --candidates $WIP/discovery/candidates_enriched.jsonl --n 3 --seed $RUN_ID \
  --write-chosen $WIP/discovery/chosen_n.json --json
# clone+audit each → $WIP/discovery/audits/*.json
python3 $SCRIPTS/propose_remix.py --chosen-n $WIP/discovery/chosen_n.json --audits $WIP/discovery/audits \
  --out $WIP/forge/remix_plan.json --domain writing --json
# refine → 50×≥1000-char forge (90s between round prompts) (P1–P4) → unify_wholeness + ship_check PASS
python3 $SCRIPTS/unify_wholeness.py --package $PKG --rounds 50 --min-chars 1000 --json
python3 $SCRIPTS/ship_check.py --fork $PKG --rounds 50 --min-chars 1000 --json
```

## Resume

```bash
python3 $SCRIPTS/resume_forge.py status --wip $WIP --json
/skillremix --resume --wip $WIP
```
