#!/usr/bin/env python3
"""Initialize a fork directory from an upstream skill package."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import stat
from pathlib import Path

INSTALL_SH = """#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
NAME="${1:-%NAME%}"
# Prefer bundled multi-host installer
if [ -f "$ROOT/scripts/install_skill_dual.sh" ]; then
  bash "$ROOT/scripts/install_skill_dual.sh" "$ROOT" --name "$NAME"
elif [ -f "$ROOT/../skillremix/scripts/install_skill_dual.sh" ]; then
  bash "$ROOT/../skillremix/scripts/install_skill_dual.sh" "$ROOT" --name "$NAME"
elif [ -f "$ROOT/../randomupgrade/scripts/install_skill_dual.sh" ]; then
  bash "$ROOT/../randomupgrade/scripts/install_skill_dual.sh" "$ROOT" --name "$NAME"
else
  DEST_G="$HOME/.gemini/config/skills/$NAME"
  DEST_C="$HOME/.claude/skills/$NAME"
  DEST_U="$HOME/.cursor/skills/$NAME"
  DEST_X="${CODEX_HOME:-$HOME/.codex}/skills/$NAME"
  for d in "$DEST_G" "$DEST_C" "$DEST_U" "$DEST_X"; do
    rm -rf "$d"; mkdir -p "$d"
    tar -C "$ROOT" --exclude='.git' --exclude='.gemini' --exclude='.agents' --exclude='.agent' --exclude='.claude' --exclude='.cursor' --exclude='.codex' -cf - . | tar -C "$d" -xf -
    echo "installed: $d"
  done
fi
"""

UPSTREAM_MD = """# Upstream

- **Incumbent:** `{id}`
- **URL:** {url}
- **Installs (approx):** {installs}
- **Stars:** {stars}
- **License:** {license}
- **Fork name:** `{fork_name}`

## Upgrade thesis

This fork keeps the incumbent's useful core and upgrades it across the fixed
50-round forge phases documented in `UPGRADE_PLAN.md`
(unify → enhance → metrics → awesome; see `USEFULNESS_FORGE.md`).
"""

COMPARISON_MD = """# Comparison vs incumbent

| Area | Incumbent | This fork |
|---|---|---|
| Core job | (fill) | (fill) |
| Verification | (fill) | (fill) |
| Scripts / evals | (fill) | (fill) |
| Install UX | (fill) | (fill) |
| Metrics | (fill) | (fill) |

Update this table as forge phases land.
"""

README_TMPL = """# {fork_name}

Upgraded fork of `{incumbent}` — marketplace skill (adoption floor; popular OK) made substantially more useful.

## Install (Antigravity + Claude + Cursor + Codex)

```bash
git clone <repo-url>
cd {fork_name}
bash install.sh {fork_name}
```

## Use (after install)

```text
/{fork_name} <describe your task>
```

## Upstream

See `UPSTREAM.md`. Upgrade plan: `UPGRADE_PLAN.md`. Forge log: `USEFULNESS_FORGE.md`.
"""


def rewrite_skill_md(text: str, fork_name: str, incumbent_id: str, url: str) -> str:
    # Replace name: line
    text2 = re.sub(r"(?m)^name:\s*.*$", f"name: {fork_name}", text, count=1)
    if text2 == text and text.startswith("---"):
        text2 = text.replace("---\n", f"---\nname: {fork_name}\n", 1)
    # Ensure description mentions upgrade
    if "upgrades" not in text2.lower() and "description:" in text2:
        text2 = re.sub(
            r"(?ms)^(description:\s*>-\s*\n)(.*?)(?=\n[a-zA-Z0-9_-]+:|\n---)",
            lambda m: m.group(1)
            + f"  Upgrades {incumbent_id} ({url}). "
            + re.sub(r"^\s+", "  ", m.group(2).strip())
            + "\n",
            text2,
            count=1,
        )
    return text2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, required=True, help="Upstream skill dir with SKILL.md")
    ap.add_argument("--dest", type=Path, required=True, help="Fork destination dir")
    ap.add_argument("--fork-name", required=True)
    ap.add_argument("--chosen", type=Path, help="chosen.json for UPSTREAM.md")
    ap.add_argument("--dual-installer", type=Path, help="Copy install_skill_dual.sh into fork scripts/")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    src = args.src
    dest = args.dest
    if not (src / "SKILL.md").exists():
        raise SystemExit(f"no SKILL.md in {src}")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    # copy tree excluding git and agent install mirrors
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        if any(
            part in {".git", ".gemini", ".agents", ".agent", ".claude", ".cursor", ".codex", "node_modules"}
            for part in rel.parts
        ):
            continue
        out = dest / rel
        if p.is_dir():
            out.mkdir(parents=True, exist_ok=True)
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)

    chosen = {}
    if args.chosen and args.chosen.exists():
        chosen = json.loads(args.chosen.read_text(encoding="utf-8"))

    skill_path = dest / "SKILL.md"
    skill_path.write_text(
        rewrite_skill_md(
            skill_path.read_text(encoding="utf-8"),
            args.fork_name,
            chosen.get("id", "unknown"),
            chosen.get("url", ""),
        ),
        encoding="utf-8",
    )

    (dest / "UPSTREAM.md").write_text(
        UPSTREAM_MD.format(
            id=chosen.get("id", "unknown"),
            url=chosen.get("url", ""),
            installs=chosen.get("installs_approx", chosen.get("installs", "?")),
            stars=chosen.get("stars", "?"),
            license=chosen.get("license", "?"),
            fork_name=args.fork_name,
        ),
        encoding="utf-8",
    )
    (dest / "COMPARISON.md").write_text(COMPARISON_MD, encoding="utf-8")
    (dest / "README.md").write_text(
        README_TMPL.format(fork_name=args.fork_name, incumbent=chosen.get("id", "unknown")),
        encoding="utf-8",
    )
    install = dest / "install.sh"
    install.write_text(INSTALL_SH.replace("%NAME%", args.fork_name), encoding="utf-8")
    install.chmod(install.stat().st_mode | stat.S_IEXEC)

    scripts = dest / "scripts"
    scripts.mkdir(exist_ok=True)
    if args.dual_installer and args.dual_installer.exists():
        shutil.copy2(args.dual_installer, scripts / "install_skill_dual.sh")
        (scripts / "install_skill_dual.sh").chmod(
            (scripts / "install_skill_dual.sh").stat().st_mode | stat.S_IEXEC
        )

    out = {"dest": str(dest), "fork_name": args.fork_name, "files": len(list(dest.rglob("*")))}
    print(json.dumps(out, indent=2) if args.json else out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
