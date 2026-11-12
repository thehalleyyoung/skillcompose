#!/usr/bin/env python3
"""Generate idiomatic Gemini, Codex, Claude, and Cursor skill packages.

Supports two modes:
  1. `--in-place`: Stamps native client manifests directly inside `<skill_dir>`:
     - Gemini CLI / Antigravity: `gemini-extension.json` + `GEMINI.md`
     - OpenAI Codex: `agents/openai.yaml`
     - Claude Code: `.claude-plugin/plugin.json` + `commands/<name>.md`
     - Cursor: `rules/<name>.mdc`
  2. `--platforms-root <dir>` (and optional `--workspace-root <dir>`):
     Exports four standalone, platform-tailored skill packages under:
       - `<platforms_root>/gemini/<name>/`
       - `<platforms_root>/codex/<name>/`
       - `<platforms_root>/claude/<name>/`
       - `<platforms_root>/cursor/<name>/`
     and optionally populates workspace auto-discovery mirrors under:
       - `<workspace_root>/.gemini/skills/<name>/`
       - `<workspace_root>/.codex/skills/<name>/`
       - `<workspace_root>/.claude/skills/<name>/` + `.claude/commands/<name>.md`
       - `<workspace_root>/.cursor/skills/<name>/` + `.cursor/rules/<name>.mdc`
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

SKIP_COPY_DIRS = {
    ".git",
    ".gemini",
    ".codex",
    ".claude",
    ".claude-plugin",
    ".cursor",
    ".agents",
    ".agent",
    "__pycache__",
    "node_modules",
    "platforms",
    "paper",
    "evals",
    "metrics",
    "review",
}


def parse_frontmatter(skill_md_text: str, fallback_name: str) -> tuple[str, str, str]:
    """Return (name, description, markdown_body)."""
    if not skill_md_text.startswith("---"):
        return fallback_name, f"{fallback_name} agent skill.", skill_md_text
    parts = skill_md_text.split("---", 2)
    if len(parts) < 3:
        return fallback_name, f"{fallback_name} agent skill.", skill_md_text
    fm = parts[1]
    body = parts[2].lstrip("\n")

    m_name = re.search(r"(?m)^name:\s*(\S+)", fm)
    name = m_name.group(1).strip().strip("'\"") if m_name else fallback_name

    # Extract single-line or folded/multiline description
    desc = f"{name} agent skill."
    lines = fm.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("description:"):
            tail = line.split(":", 1)[1].strip()
            if tail and tail not in {">-", ">", "|", "|-"}:
                desc = tail.strip("'\"")
            else:
                collected: list[str] = []
                for sub in lines[idx + 1 :]:
                    if sub.startswith(("  ", "\t")):
                        collected.append(sub.strip())
                    elif not sub.strip():
                        continue
                    else:
                        break
                if collected:
                    desc = " ".join(collected)
            break
    return name, desc, body


def display_title(name: str) -> str:
    tokens = [t for t in re.split(r"[-_]+", name) if t]
    special = {"ml": "ML", "ai": "AI", "api": "API", "sql": "SQL", "skillcompose": "SkillCompose"}
    return " ".join(special.get(t.lower(), t.capitalize()) for t in tokens) or name


def yaml_quote(val: str) -> str:
    escaped = val.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_openai_yaml(name: str, desc: str) -> str:
    short_desc = desc if len(desc) <= 160 else (desc[:157].rstrip() + "...")
    title = display_title(name)
    default_prompt = (
        f"Use ${name} to execute its Lawvere-Amari manifold workflow and verify all deliverables before completion."
    )
    return (
        "interface:\n"
        f"  display_name: {yaml_quote(title)}\n"
        f"  short_description: {yaml_quote(short_desc)}\n"
        f"  default_prompt: {yaml_quote(default_prompt)}\n"
        "policy:\n"
        "  allow_implicit_invocation: true\n"
    )


def render_gemini_extension_json(name: str, desc: str) -> str:
    payload = {
        "name": name,
        "version": "1.0.0",
        "description": desc,
        "contextFileName": "GEMINI.md",
    }
    return json.dumps(payload, indent=2) + "\n"


def render_gemini_md(name: str, desc: str) -> str:
    return (
        f"# `{name}` — Gemini CLI & Antigravity Skill Context\n\n"
        f"{desc}\n\n"
        "## Activation & Execution\n\n"
        f"- Primary skill specification: [SKILL.md](./SKILL.md)\n"
        "- Follow all stages in `SKILL.md`, consulting `./references/` on demand and running deterministic verification scripts under `./scripts/`.\n"
    )


def render_claude_plugin_json(name: str, desc: str) -> str:
    payload = {
        "name": name,
        "version": "1.0.0",
        "description": desc,
        "author": {"name": "SkillCompose"},
        "license": "MIT",
        "skills": "./",
        "commands": ["./commands"],
    }
    return json.dumps(payload, indent=2) + "\n"


def render_claude_command_md(name: str, desc: str, skill_path_expr: str) -> str:
    short_desc = desc if len(desc) <= 180 else (desc[:177].rstrip() + "...")
    return (
        "---\n"
        f"description: {yaml_quote(short_desc)}\n"
        'argument-hint: "<task or arguments>"\n'
        "---\n\n"
        f"Execute the `{name}` skill located at `{skill_path_expr}/SKILL.md` on the user's request (`$ARGUMENTS`).\n\n"
        f"1. Read `{skill_path_expr}/SKILL.md` and follow its staged protocol.\n"
        f"2. Run the deterministic helper and gate scripts in `{skill_path_expr}/scripts/` before declaring completion.\n"
    )


def render_cursor_mdc(name: str, desc: str, body: str, skill_path_expr: str) -> str:
    short_desc = desc if len(desc) <= 180 else (desc[:177].rstrip() + "...")
    rewritten_body = rewrite_skill_paths(body, name, skill_path_expr)
    return (
        "---\n"
        f"description: {yaml_quote(short_desc)}\n"
        "globs:\n"
        "alwaysApply: false\n"
        "---\n\n"
        f"{rewritten_body}"
    )


def rewrite_skill_paths(text: str, name: str, target_skill_dir_expr: str) -> str:
    out = text.replace(f".agents/skills/{name}", target_skill_dir_expr)
    out = out.replace("~/.gemini/config/skills/skillcompose", target_skill_dir_expr)
    return out


def render_platform_skill_md(platform: str, name: str, desc: str, body: str, path_expr: str) -> str:
    adapted_body = rewrite_skill_paths(body, name, path_expr)
    extra_fm = ""
    if platform == "claude":
        extra_fm = 'argument-hint: "<task or flags>"\nuser-invocable: true\n'
    return (
        "---\n"
        f"name: {name}\n"
        f"description: >-\n  {desc}\n"
        f"{extra_fm}"
        "---\n\n"
        f"{adapted_body}"
    )


def render_platform_installer(platform: str, name: str) -> str:
    py_copy = """copy_tree() {
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
}"""
    if platform == "gemini":
        return f"""#!/usr/bin/env bash
# Install `{name}` for Gemini CLI (~/.gemini/skills) and Antigravity (~/.gemini/config/skills).
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
{py_copy}
for DEST in "$HOME/.gemini/config/skills/{name}" "$HOME/.gemini/skills/{name}"; do
  mkdir -p "$DEST"
  copy_tree "$SRC" "$DEST"
  echo "installed (gemini): $DEST"
done
"""
    if platform == "codex":
        return f"""#!/usr/bin/env bash
# Install `{name}` for OpenAI Codex (${{CODEX_HOME:-$HOME/.codex}}/skills/{name}).
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
{py_copy}
DEST="${{CODEX_HOME:-$HOME/.codex}}/skills/{name}"
mkdir -p "$DEST"
copy_tree "$SRC" "$DEST"
echo "installed (codex): $DEST"
"""
    if platform == "claude":
        return f"""#!/usr/bin/env bash
# Install `{name}` for Claude Code (~/.claude/skills/{name} + ~/.claude/commands/{name}.md).
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
{py_copy}
DEST="$HOME/.claude/skills/{name}"
mkdir -p "$DEST" "$HOME/.claude/commands"
copy_tree "$SRC" "$DEST"
cp "$SRC/commands/{name}.md" "$HOME/.claude/commands/{name}.md"
echo "installed (claude): $DEST"
"""
    if platform == "cursor":
        return f"""#!/usr/bin/env bash
# Install `{name}` for Cursor (~/.cursor/skills/{name} + optional workspace .cursor/rules/{name}.mdc).
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
{py_copy}
DEST="$HOME/.cursor/skills/{name}"
mkdir -p "$DEST"
copy_tree "$SRC" "$DEST"
if [ "${{1:-}}" = "--workspace" ] && [ -n "${{2:-}}" ]; then
  mkdir -p "$2/.cursor/rules"
  cp "$SRC/rules/{name}.mdc" "$2/.cursor/rules/{name}.mdc"
  echo "installed workspace rule (cursor): $2/.cursor/rules/{name}.mdc"
fi
echo "installed (cursor): $DEST"
"""
    raise ValueError(f"unknown platform: {platform}")


def copy_core_tree(src_skill_dir: Path, dst_dir: Path) -> None:
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for item in sorted(src_skill_dir.iterdir()):
        if item.name in SKIP_COPY_DIRS or item.name.startswith(("skillremix-wip-", "randomupgrade-wip-")):
            continue
        if item.name in {"SKILL.md", "GEMINI.md", "gemini-extension.json", "install.sh"}:
            continue
        if item.name in {"agents", "commands", "rules"}:
            continue
        target = dst_dir / item.name
        if item.is_dir():
            shutil.copytree(
                item,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"),
            )
        elif item.is_file():
            shutil.copy2(item, target)


def stamp_in_place(skill_dir: Path, skill_name_override: str | None = None) -> dict[str, Any]:
    skill_md_path = skill_dir / "SKILL.md"
    raw = skill_md_path.read_text(encoding="utf-8")
    name, desc, body = parse_frontmatter(raw, skill_name_override or skill_dir.name)
    if skill_name_override:
        name = skill_name_override

    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "agents" / "openai.yaml").write_text(render_openai_yaml(name, desc), encoding="utf-8")

    (skill_dir / "gemini-extension.json").write_text(render_gemini_extension_json(name, desc), encoding="utf-8")
    (skill_dir / "GEMINI.md").write_text(render_gemini_md(name, desc), encoding="utf-8")

    (skill_dir / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (skill_dir / ".claude-plugin" / "plugin.json").write_text(
        render_claude_plugin_json(name, desc), encoding="utf-8"
    )
    (skill_dir / "commands").mkdir(parents=True, exist_ok=True)
    (skill_dir / "commands" / f"{name}.md").write_text(
        render_claude_command_md(name, desc, f"~/.claude/skills/{name}"), encoding="utf-8"
    )

    (skill_dir / "rules").mkdir(parents=True, exist_ok=True)
    (skill_dir / "rules" / f"{name}.mdc").write_text(
        render_cursor_mdc(name, desc, body, f"~/.cursor/skills/{name}"), encoding="utf-8"
    )
    return {"skill": name, "in_place": str(skill_dir)}


def export_four_platforms(
    skill_dir: Path,
    platforms_root: Path,
    workspace_root: Path | None = None,
    skill_name_override: str | None = None,
) -> dict[str, Any]:
    raw = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    name, desc, body = parse_frontmatter(raw, skill_name_override or skill_dir.name)
    if skill_name_override:
        name = skill_name_override

    path_exprs = {
        "gemini": f"~/.gemini/config/skills/{name}",
        "codex": f"${{CODEX_HOME:-$HOME/.codex}}/skills/{name}",
        "claude": f"~/.claude/skills/{name}",
        "cursor": f"~/.cursor/skills/{name}",
    }
    ws_path_exprs = {
        "gemini": f".gemini/skills/{name}",
        "codex": f".codex/skills/{name}",
        "claude": f".claude/skills/{name}",
        "cursor": f".cursor/skills/{name}",
    }

    exported: dict[str, str] = {}
    for platform in ("gemini", "codex", "claude", "cursor"):
        pdir = platforms_root / platform / name
        copy_core_tree(skill_dir, pdir)
        (pdir / "SKILL.md").write_text(
            render_platform_skill_md(platform, name, desc, body, path_exprs[platform]),
            encoding="utf-8",
        )
        inst = pdir / "install.sh"
        inst.write_text(render_platform_installer(platform, name), encoding="utf-8")
        os.chmod(inst, 0o755)

        if platform == "gemini":
            (pdir / "gemini-extension.json").write_text(render_gemini_extension_json(name, desc), encoding="utf-8")
            (pdir / "GEMINI.md").write_text(render_gemini_md(name, desc), encoding="utf-8")
        elif platform == "codex":
            (pdir / "agents").mkdir(parents=True, exist_ok=True)
            (pdir / "agents" / "openai.yaml").write_text(render_openai_yaml(name, desc), encoding="utf-8")
        elif platform == "claude":
            (pdir / ".claude-plugin").mkdir(parents=True, exist_ok=True)
            (pdir / ".claude-plugin" / "plugin.json").write_text(
                render_claude_plugin_json(name, desc), encoding="utf-8"
            )
            (pdir / "commands").mkdir(parents=True, exist_ok=True)
            (pdir / "commands" / f"{name}.md").write_text(
                render_claude_command_md(name, desc, path_exprs["claude"]), encoding="utf-8"
            )
        elif platform == "cursor":
            (pdir / "rules").mkdir(parents=True, exist_ok=True)
            (pdir / "rules" / f"{name}.mdc").write_text(
                render_cursor_mdc(name, desc, body, path_exprs["cursor"]), encoding="utf-8"
            )
        exported[platform] = str(pdir)

    if workspace_root is not None:
        for platform, dot_sub in (
            ("gemini", ".gemini/skills"),
            ("codex", ".codex/skills"),
            ("claude", ".claude/skills"),
            ("cursor", ".cursor/skills"),
        ):
            wdir = workspace_root / dot_sub / name
            copy_core_tree(skill_dir, wdir)
            (wdir / "SKILL.md").write_text(
                render_platform_skill_md(platform, name, desc, body, ws_path_exprs[platform]),
                encoding="utf-8",
            )
            if platform == "gemini":
                (wdir / "gemini-extension.json").write_text(
                    render_gemini_extension_json(name, desc), encoding="utf-8"
                )
                (wdir / "GEMINI.md").write_text(render_gemini_md(name, desc), encoding="utf-8")
            elif platform == "codex":
                (wdir / "agents").mkdir(parents=True, exist_ok=True)
                (wdir / "agents" / "openai.yaml").write_text(render_openai_yaml(name, desc), encoding="utf-8")
            elif platform == "claude":
                cmd_dir = workspace_root / ".claude" / "commands"
                cmd_dir.mkdir(parents=True, exist_ok=True)
                (cmd_dir / f"{name}.md").write_text(
                    render_claude_command_md(name, desc, ws_path_exprs["claude"]), encoding="utf-8"
                )
            elif platform == "cursor":
                rules_dir = workspace_root / ".cursor" / "rules"
                rules_dir.mkdir(parents=True, exist_ok=True)
                (rules_dir / f"{name}.mdc").write_text(
                    render_cursor_mdc(name, desc, body, ws_path_exprs["cursor"]), encoding="utf-8"
                )

    return {"skill": name, "platforms": exported}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skill-dir", type=Path, required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--platforms-root", type=Path, default=None)
    ap.add_argument("--workspace-root", type=Path, default=None)
    args = ap.parse_args()

    sdir = args.skill_dir.resolve()
    if not (sdir / "SKILL.md").is_file():
        print(json.dumps({"ok": False, "error": f"missing SKILL.md in {sdir}"}), file=sys.stderr)
        return 2

    res: dict[str, Any] = {"ok": True}
    if args.in_place:
        res.update(stamp_in_place(sdir, args.name))
    if args.platforms_root is not None:
        ws = args.workspace_root.resolve() if args.workspace_root else None
        res.update(export_four_platforms(sdir, args.platforms_root.resolve(), ws, args.name))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
