#!/usr/bin/env bash
# Install a skill package into ~/.gemini/config/skills (Antigravity),
# ~/.claude/skills, ~/.cursor/skills, and $CODEX_HOME/skills (default ~/.codex/skills).
# (Name kept as install_skill_dual.sh for compatibility; installs across all four agent roots.)
# Excludes .git / .gemini / .agents / .agent / .claude / .cursor / .codex to prevent recursive nesting.
set -euo pipefail

usage() {
  echo "usage: $0 <skill-dir> [--name NAME] [--repo-root DIR] [--gemini-only] [--dry-run]" >&2
  exit 1
}

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

GEMINI_DEST="${HOME}/.gemini/config/skills/${NAME}"
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
  # Exclude VCS + prior install mirrors to avoid infinite nesting
  tar -C "$SKILL_DIR" \
    --exclude='.git' \
    --exclude='.gemini' \
    --exclude='.agents' \
    --exclude='.agent' \
    --exclude='.claude' \
    --exclude='.cursor' \
    --exclude='.codex' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='randomupgrade-wip-*' \
    --exclude='skillremix-wip-*' \
    -cf - . | tar -C "$dest" -xf -
  echo "installed: $dest"
}

gen_codex_yaml() {
  local dest="$1"
  [ "$DRY" -eq 1 ] && return 0
  [ -f "$dest/agents/openai.yaml" ] && return 0
  local gen="${CODEX_HOME_DIR}/skills/.system/skill-creator/scripts/generate_openai_yaml.py"
  if [ -f "$gen" ]; then
    python3 "$gen" "$dest" --name "$NAME" 2>/dev/null || true
  fi
}

copy_one "$GEMINI_DEST"
if [ "$GEMINI_ONLY" -eq 0 ]; then
  copy_one "$CLAUDE_DEST"
  copy_one "$CURSOR_DEST"
  copy_one "$CODEX_DEST"
  gen_codex_yaml "$CODEX_DEST"
fi

if [ "$DRY" -eq 0 ]; then
  [ -f "$GEMINI_DEST/SKILL.md" ] || { echo "error: Antigravity (~/.gemini/config/skills) install incomplete" >&2; exit 1; }
  if [ -d "$GEMINI_DEST/.gemini" ] || [ -d "$GEMINI_DEST/.agents" ] || [ -d "$GEMINI_DEST/.claude" ] || [ -d "$GEMINI_DEST/.cursor" ] || [ -d "$GEMINI_DEST/.codex" ]; then
    echo "error: nested config dir leaked into Antigravity install — fix excludes" >&2
    exit 1
  fi
  if [ "$GEMINI_ONLY" -eq 0 ]; then
    [ -f "$CLAUDE_DEST/SKILL.md" ] || { echo "error: Claude install incomplete" >&2; exit 1; }
    [ -f "$CURSOR_DEST/SKILL.md" ] || { echo "error: Cursor install incomplete" >&2; exit 1; }
    [ -f "$CODEX_DEST/SKILL.md" ] || { echo "error: Codex install incomplete" >&2; exit 1; }
    if [ -d "$CLAUDE_DEST/.claude" ] || [ -d "$CURSOR_DEST/.cursor" ] || [ -d "$CODEX_DEST/.codex" ]; then
      echo "error: nested .claude/.cursor/.codex leaked into install — fix excludes" >&2
      exit 1
    fi
  fi
fi

if [ -n "$REPO_ROOT" ]; then
  REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
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
  "gemini": "$GEMINI_DEST",
  "claude": "$CLAUDE_DEST" if int("$GEMINI_ONLY") == 0 else None,
  "cursor": "$CURSOR_DEST" if int("$GEMINI_ONLY") == 0 else None,
  "codex": "$CODEX_DEST" if int("$GEMINI_ONLY") == 0 else None,
  "dual_user_install": True,
  "targets": targets,
  "dry_run": bool($DRY),
}))
PY
