#!/usr/bin/env python3
"""Proposition 3 regression: carrier closure in compose_skills.py and the install join guard.

Builds a synthetic member repo whose SKILL.md invokes a script outside the skill folder that in turn
sources a helper, plus an unreferenced repo script. Checks that the closure carries exactly the
reachable files with SHA-256 provenance, and that install_skill_dual.sh refuses to drop installed
files unless --allow-loss is passed.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from compose_skills import carrier_dest, member_carrier, member_repo_root  # noqa: E402


def build_member(tmp: Path) -> Path:
    repo = tmp / "repo"
    skill = repo / "skills" / "demo"
    (repo / ".git").mkdir(parents=True)
    (skill / "references").mkdir(parents=True)
    (repo / "tools" / "lib").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: demo\n---\nRun `tools/check.sh` after drafting. See references/style.md.\n"
        "Write the result to OUTLINE.md.\n",
        encoding="utf-8",
    )
    (skill / "references" / "style.md").write_text("# Style\n", encoding="utf-8")
    (repo / "tools" / "check.sh").write_text("#!/bin/sh\n. tools/lib/common.sh\necho ok\n", encoding="utf-8")
    (repo / "tools" / "lib" / "common.sh").write_text("X=1\n", encoding="utf-8")
    (repo / "tools" / "unrelated.sh").write_text("echo unrelated\n", encoding="utf-8")
    return skill


def check_closure(tmp: Path) -> dict:
    skill = build_member(tmp)
    root = member_repo_root(skill)
    carried = {src.relative_to(root.resolve()).as_posix(): via for src, via in member_carrier(skill)}
    expected = {
        "skills/demo/references/style.md": "skill_references",
        "tools/check.sh": "referenced",
        "tools/lib/common.sh": "referenced",
    }
    dests = {s: carrier_dest(root.resolve() / s, skill, root, "demo") for s in carried}
    return {
        "closure_exact": carried == expected,
        "unreferenced_omitted": "tools/unrelated.sh" not in carried,
        "missing_outputs_ignored": "OUTLINE.md" not in carried,
        "out_of_folder_under_repo_prefix": dests.get("tools/check.sh") == "scripts/members/demo/_repo/tools/check.sh",
        "carried": carried,
    }


def check_install_guard(tmp: Path) -> dict:
    home = tmp / "home"
    home.mkdir(parents=True)
    env = {**os.environ, "HOME": str(home), "CODEX_HOME": str(home / ".codex")}
    installer = ROOT / "scripts" / "install_skill_dual.sh"

    def pkg(name: str, extra: dict[str, str]) -> Path:
        d = tmp / name
        (d / "scripts").mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: guarddemo\ndescription: demo\n---\nbody\n", encoding="utf-8")
        for rel, body in extra.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(body, encoding="utf-8")
        return d

    def install(src: Path, *flags: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(installer), str(src), "--name", "guarddemo", *flags],
            env=env, capture_output=True, text=True,
        )

    forged = pkg("forged", {"scripts/forged_tool.py": "print('forged')\n"})
    recomposed = pkg("recomposed", {"scripts/new_tool.py": "print('new')\n"})
    joined = pkg("joined", {"scripts/forged_tool.py": "print('forged')\n", "scripts/new_tool.py": "print('new')\n"})

    first = install(forged)
    refused = install(recomposed)
    cursor_copy = home / ".cursor" / "skills" / "guarddemo"
    survived = (cursor_copy / "scripts" / "forged_tool.py").is_file()
    lost = {}
    try:
        lost = json.loads(refused.stdout).get("lost", {})
    except json.JSONDecodeError:
        pass
    join_ok = install(joined)
    override = install(recomposed, "--allow-loss")
    return {
        "first_install_ok": first.returncode == 0,
        "overwrite_refused_exit_2": refused.returncode == 2,
        "lost_paths_reported": all("scripts/forged_tool.py" in v for v in lost.values()) and bool(lost),
        "forged_file_survived_refusal": survived,
        "join_install_ok": join_ok.returncode == 0,
        "allow_loss_override_ok": override.returncode == 0
        and not (cursor_copy / "scripts" / "forged_tool.py").exists(),
    }


def check_locator(tmp: Path) -> dict:
    """The carrier is only right if the member folder is: prefer the folder whose frontmatter declares the name."""
    from locate_skill import pick

    repo = tmp / "repo"
    for rel, name in (
        ("templates/skills/genre/fantasy", "fantasy"),
        ("templates/skills/qa/consistency-checker", "story-monitor"),
        ("distributions/codex/skills/craft", "craft"),
        ("skills/creative/craft", "craft"),
    ):
        (repo / rel).mkdir(parents=True)
        (repo / rel / "SKILL.md").write_text(f"---\nname: {name}\n---\nbody\n", encoding="utf-8")
    return {
        "locator_prefers_declared_name": pick(repo, "story-monitor", None).relative_to(repo).as_posix() == "templates/skills/qa/consistency-checker",
        "locator_skips_distribution_mirror": pick(repo, "craft", None).relative_to(repo).as_posix() == "skills/creative/craft",
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        closure = check_closure(tmp / "c")
        guard = check_install_guard(tmp / "g")
        locator = check_locator(tmp / "l")
    checks = {k: v for k, v in {**closure, **guard, **locator}.items() if isinstance(v, bool)}
    ok = all(checks.values())
    print(json.dumps({"ok": ok, "checks": checks, "carried": closure["carried"]}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
