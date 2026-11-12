#!/usr/bin/env bash
# Public installer for skillcompose + ml-paper-manifold across Gemini, Claude, Cursor, and Codex.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ $# -eq 0 ]; then
  bash "$ROOT/scripts/install_skill_dual.sh" "$ROOT" --name skillcompose
  if [ -d "$ROOT/paper/composed_skill/ml-paper-manifold" ]; then
    bash "$ROOT/scripts/install_skill_dual.sh" "$ROOT/paper/composed_skill/ml-paper-manifold" --name ml-paper-manifold
  fi
else
  case "$1" in
    --*)
      bash "$ROOT/scripts/install_skill_dual.sh" "$ROOT" --name skillcompose "$@"
      if [ -d "$ROOT/paper/composed_skill/ml-paper-manifold" ]; then
        bash "$ROOT/scripts/install_skill_dual.sh" "$ROOT/paper/composed_skill/ml-paper-manifold" --name ml-paper-manifold "$@"
      fi
      ;;
    *)
      NAME="$1"
      shift || true
      bash "$ROOT/scripts/install_skill_dual.sh" "$ROOT" --name "$NAME" "$@"
      ;;
  esac
fi
