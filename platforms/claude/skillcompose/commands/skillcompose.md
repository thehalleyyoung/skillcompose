---
description: "Principled Kleisli, information-theoretic, and control-theoretic skill composition & upgrade meta-skill via /skillcompose [query|--pin owner/repo@skill] [--domain writing|devops..."
argument-hint: "<task or arguments>"
---

Execute the `skillcompose` skill located at `~/.claude/skills/skillcompose/SKILL.md` on the user's request (`$ARGUMENTS`).

1. Read `~/.claude/skills/skillcompose/SKILL.md` and follow its staged protocol.
2. Run the deterministic helper and gate scripts in `~/.claude/skills/skillcompose/scripts/` before declaring completion.
