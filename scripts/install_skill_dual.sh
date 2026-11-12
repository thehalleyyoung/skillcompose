#!/usr/bin/env bash
# Install a skill package across all four agent platforms:
#   - Gemini CLI (~/.gemini/skills) + Antigravity (~/.gemini/config/skills)
#   - Claude Code (~/.claude/skills + ~/.claude/commands)
#   - Cursor (~/.cursor/skills)
#   - OpenAI Codex (${CODEX_HOME:-$HOME/.codex}/skills + agents/openai.yaml)
# Excludes .git / .gemini / .agents / .agent / .claude / .cursor / .codex / platforms to prevent recursive nesting.
set -euo pipefail

usage() {
  echo "usage: $0 <skill-dir> [--name NAME] [--repo-root DIR] [--gemini-only] [--dry-run]" >&2
  exit 1
}

SCRIPT_HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR=""
NAME=""
REPO_ROOT=""
GEMINI_ONLY=0
DRY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="${2:-}"; shift 2 ;;
    --repo-root) REPO_ROOT="${2:-}"; shift 2 ;;
    --gemini-only) GEMINI_ONLY=1; shift ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage ;;
    *)
      if [ -z "$SKILL_DIR" ]; then SKILL_DIR="$1"; shift
      else usage
      fi
      ;;
  esac
done

[ -n "$SKILL_DIR" ] || usage
SKILL_DIR="$(cd "$SKILL_DIR" && pwd)"
[ -f "$SKILL_DIR/SKILL.md" ] || { echo "error: missing SKILL.md" >&2; exit 1; }

if [ -z "$NAME" ]; then
  NAME="$(basename "$SKILL_DIR")"
fi
NAME="$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9-]+/-/g; s/^-+//; s/-+$//')"

CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"

GEMINI_AGY_DEST="${HOME}/.gemini/config/skills/${NAME}"
GEMINI_CLI_DEST="${HOME}/.gemini/skills/${NAME}"
CLAUDE_DEST="${HOME}/.claude/skills/${NAME}"
CURSOR_DEST="${HOME}/.cursor/skills/${NAME}"
CODEX_DEST="${CODEX_HOME_DIR}/skills/${NAME}"

copy_one() {
  local dest="$1"
  if [ "$DRY" -eq 1 ]; then
    echo "dry-run: $SKILL_DIR -> $dest"
    return 0
  fi
  if [ "$SKILL_DIR" = "$dest" ]; then
    echo "skip: already at destination: $dest"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  mkdir -p "$dest"
  python3 - "$SKILL_DIR" "$dest" <<'PY'
import os, shutil, sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
excl = {
    ".git", ".gemini", ".agents", ".agent", ".claude", ".claude-plugin",
    ".cursor", ".codex", "platforms", "paper", "evals", "__pycache__", "node_modules",
}
for root, dirs, files in os.walk(src):
    rel_root = Path(root).relative_to(src)
    dirs[:] = [
        d for d in dirs
        if d not in excl and not d.startswith(("randomupgrade-wip-", "skillremix-wip-", "skillcompose-wip-"))
    ]
    target_root = dst / rel_root
    target_root.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f.endswith((".pyc", ".pyo")) or f == ".DS_Store":
            continue
        sp = Path(root) / f
        dp = target_root / f
        shutil.copyfile(sp, dp)
        if dp.suffix in {".sh", ".py"} or "scripts" in rel_root.parts:
            try:
                os.chmod(dp, 0o755)
            except OSError:
                pass
PY
  echo "installed: $dest"
}

stamp_manifests() {
  local dest="$1"
  [ "$DRY" -eq 1 ] && return 0
  local exporter="${SCRIPT_HERE}/export_platform_targets.py"
  if [ -f "$exporter" ]; then
    python3 "$exporter" --skill-dir "$dest" --name "$NAME" --in-place >/dev/null 2>&1 || true
  fi
}

copy_one "$GEMINI_AGY_DEST"
stamp_manifests "$GEMINI_AGY_DEST"
copy_one "$GEMINI_CLI_DEST"
stamp_manifests "$GEMINI_CLI_DEST"

if [ "$GEMINI_ONLY" -eq 0 ]; then
  copy_one "$CLAUDE_DEST"
  stamp_manifests "$CLAUDE_DEST"
  if [ "$DRY" -eq 0 ] && [ -f "$CLAUDE_DEST/commands/${NAME}.md" ]; then
    mkdir -p "${HOME}/.claude/commands"
    cp "$CLAUDE_DEST/commands/${NAME}.md" "${HOME}/.claude/commands/${NAME}.md"
  fi
  copy_one "$CURSOR_DEST"
  stamp_manifests "$CURSOR_DEST"
  copy_one "$CODEX_DEST"
  stamp_manifests "$CODEX_DEST"
fi

if [ "$DRY" -eq 0 ]; then
  [ -f "$GEMINI_AGY_DEST/SKILL.md" ] || { echo "error: Antigravity (~/.gemini/config/skills) install incomplete" >&2; exit 1; }
  [ -f "$GEMINI_CLI_DEST/SKILL.md" ] || { echo "error: Gemini CLI (~/.gemini/skills) install incomplete" >&2; exit 1; }
  if [ -d "$GEMINI_AGY_DEST/.gemini" ] || [ -d "$GEMINI_AGY_DEST/.agents" ] || [ -d "$GEMINI_AGY_DEST/.claude" ] || [ -d "$GEMINI_AGY_DEST/.cursor" ] || [ -d "$GEMINI_AGY_DEST/.codex" ]; then
    echo "error: nested config dir leaked into Antigravity install — fix excludes" >&2
    exit 1
  fi
  if [ "$GEMINI_ONLY" -eq 0 ]; then
    [ -f "$CLAUDE_DEST/SKILL.md" ] || { echo "error: Claude install incomplete" >&2; exit 1; }
    [ -f "$CURSOR_DEST/SKILL.md" ] || { echo "error: Cursor install incomplete" >&2; exit 1; }
    [ -f "$CODEX_DEST/SKILL.md" ] || { echo "error: Codex install incomplete" >&2; exit 1; }
    [ -f "$CODEX_DEST/agents/openai.yaml" ] || { echo "error: Codex agents/openai.yaml missing" >&2; exit 1; }
    if [ -d "$CLAUDE_DEST/.claude" ] || [ -d "$CURSOR_DEST/.cursor" ] || [ -d "$CODEX_DEST/.codex" ]; then
      echo "error: nested .claude/.cursor/.codex leaked into install — fix excludes" >&2
      exit 1
    fi
  fi
fi

if [ -n "$REPO_ROOT" ]; then
  REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
  copy_one "${REPO_ROOT}/.gemini/skills/${NAME}"
  copy_one "${REPO_ROOT}/.agents/skills/${NAME}"
  if [ "$GEMINI_ONLY" -eq 0 ]; then
    copy_one "${REPO_ROOT}/.claude/skills/${NAME}"
    copy_one "${REPO_ROOT}/.cursor/skills/${NAME}"
    copy_one "${REPO_ROOT}/.codex/skills/${NAME}"
  fi
fi

python3 - <<PY
import json
targets = ["gemini"] if int("$GEMINI_ONLY") == 1 else ["gemini", "claude", "cursor", "codex"]
print(json.dumps({
  "skill": "$NAME",
  "source": "$SKILL_DIR",
  "gemini_antigravity": "$GEMINI_AGY_DEST",
  "gemini_cli": "$GEMINI_CLI_DEST",
  "claude": "$CLAUDE_DEST" if int("$GEMINI_ONLY") == 0 else None,
  "cursor": "$CURSOR_DEST" if int("$GEMINI_ONLY") == 0 else None,
  "codex": "$CODEX_DEST" if int("$GEMINI_ONLY") == 0 else None,
  "dual_user_install": True,
  "targets": targets,
  "dry_run": bool($DRY),
}))
PY
