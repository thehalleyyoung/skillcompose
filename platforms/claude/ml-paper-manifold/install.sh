#!/usr/bin/env bash
# Install `ml-paper-manifold` for Claude Code (~/.claude/skills/ml-paper-manifold + ~/.claude/commands/ml-paper-manifold.md).
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
copy_tree() {
  python3 - "$1" "$2" <<'PY'
import os, shutil, sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
for root, dirs, files in os.walk(src):
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
    rel = Path(root).relative_to(src)
    troot = dst / rel
    troot.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f.endswith((".pyc", ".pyo")) or f == ".DS_Store":
            continue
        sp, dp = Path(root) / f, troot / f
        shutil.copyfile(sp, dp)
        if dp.suffix in {".sh", ".py"} or "scripts" in rel.parts:
            try:
                os.chmod(dp, 0o755)
            except OSError:
                pass
PY
}
DEST="$HOME/.claude/skills/ml-paper-manifold"
mkdir -p "$DEST" "$HOME/.claude/commands"
copy_tree "$SRC" "$DEST"
cp "$SRC/commands/ml-paper-manifold.md" "$HOME/.claude/commands/ml-paper-manifold.md"
echo "installed (claude): $DEST"
