#!/usr/bin/env bash
# Public installer for /skillcompose (Antigravity + Claude + Cursor + Codex).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
NAME="${1:-skillcompose}"
shift || true
bash "$ROOT/scripts/install_skill_dual.sh" "$ROOT" --name "$NAME" "$@"
