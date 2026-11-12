# Multi-Platform Skill Packages (`gemini`, `codex`, `claude`, `cursor`)

This directory contains standalone, idiomatic builds of both **`skillcompose`** (the Lawvere–Amari Generative Skill Manifold compiler) and **`ml-paper-manifold`** (the 8-landmark post-research ML & LaTeX paper-writing skill composed from public GitHub skills) for all four major coding-agent platforms:

| Platform | Directory | Native Manifests Included | Global Install Target | Workspace Auto-Discovery Path |
|---|---|---|---|---|
| **Gemini** *(Gemini CLI + Antigravity / `agy`)* | [`platforms/gemini/`](./gemini/) | `SKILL.md`, `GEMINI.md`, `gemini-extension.json` | `~/.gemini/skills/<skill>` & `~/.gemini/config/skills/<skill>` | `.gemini/skills/<skill>/` |
| **Codex** *(OpenAI Codex CLI & App)* | [`platforms/codex/`](./codex/) | `SKILL.md`, `agents/openai.yaml` | `${CODEX_HOME:-~/.codex}/skills/<skill>` | `.codex/skills/<skill>/` |
| **Claude** *(Claude Code)* | [`platforms/claude/`](./claude/) | `SKILL.md` (`argument-hint`, `user-invocable`), `.claude-plugin/plugin.json`, `commands/<skill>.md` | `~/.claude/skills/<skill>` & `~/.claude/commands/<skill>.md` | `.claude/skills/<skill>/` & `.claude/commands/` |
| **Cursor** *(Cursor IDE)* | [`platforms/cursor/`](./cursor/) | `SKILL.md`, `rules/<skill>.mdc` | `~/.cursor/skills/<skill>` | `.cursor/skills/<skill>/` & `.cursor/rules/<skill>.mdc` |

## One-Command Install (All 4 Platforms, Both Skills)

From the repository root:

```bash
bash install.sh
```

Or install a single platform/skill directly:

```bash
# Install ml-paper-manifold for a single platform:
bash platforms/gemini/ml-paper-manifold/install.sh
bash platforms/codex/ml-paper-manifold/install.sh
bash platforms/claude/ml-paper-manifold/install.sh
bash platforms/cursor/ml-paper-manifold/install.sh

# Install skillcompose for a single platform:
bash platforms/gemini/skillcompose/install.sh
bash platforms/codex/skillcompose/install.sh
bash platforms/claude/skillcompose/install.sh
bash platforms/cursor/skillcompose/install.sh
```

## Regenerating Platform Packages for Any Composed Skill

Every skill compiled by `scripts/compose_skills.py` automatically stamps `GEMINI.md`, `gemini-extension.json`, `agents/openai.yaml`, `.claude-plugin/plugin.json`, `commands/<name>.md`, and `rules/<name>.mdc`. To export full standalone 4-platform bundles for any skill directory:

```bash
python3 scripts/export_platform_targets.py \
  --skill-dir <path/to/skill> \
  --in-place \
  --platforms-root ./platforms \
  --workspace-root .
```
