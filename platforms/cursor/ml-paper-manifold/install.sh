#!/usr/bin/env bash
# Install `ml-paper-manifold` for Cursor (~/.cursor/skills/ml-paper-manifold + optional workspace .cursor/rules/ml-paper-manifold.mdc).
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
DEST="$HOME/.cursor/skills/ml-paper-manifold"
mkdir -p "$DEST"
copy_tree "$SRC" "$DEST"
if [ "${1:-}" = "--workspace" ] && [ -n "${2:-}" ]; then
  mkdir -p "$2/.cursor/rules"
  cp "$SRC/rules/ml-paper-manifold.mdc" "$2/.cursor/rules/ml-paper-manifold.mdc"
  echo "installed workspace rule (cursor): $2/.cursor/rules/ml-paper-manifold.mdc"
fi
echo "installed (cursor): $DEST"
