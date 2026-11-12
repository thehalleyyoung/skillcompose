#!/usr/bin/env python3
"""--new-skill-name regression: parser refusals and the installer's --new mode, in a throwaway HOME."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARSE = ROOT / "scripts" / "parse_args.py"
INSTALL = ROOT / "scripts" / "install_skill_dual.sh"


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        home = tmp / "home"
        env = {**os.environ, "HOME": str(home), "CODEX_HOME": str(home / ".codex")}
        (home / ".cursor" / "skills" / "old-fantasy").mkdir(parents=True)
        (home / ".cursor" / "skills" / "old-fantasy" / "SKILL.md").write_text("old\n", encoding="utf-8")

        def parse(*argv: str) -> tuple[int, dict]:
            r = subprocess.run(["python3", str(PARSE), *argv], env=env, capture_output=True, text=True)
            try:
                return r.returncode, json.loads(r.stdout)
            except json.JSONDecodeError:
                return r.returncode, {}

        base = ["--n", "4", "--domain", "writing", "end-to-end fantasy novel writing"]
        rc_ok, ok = parse(*base, "--new-skill-name", "fantasy-novel-v2")
        rc_taken, taken = parse(*base, "--new-skill-name", "old-fantasy")
        rc_bad, bad = parse(*base, "--new-skill-name", "Bad_Name")
        rc_res, res = parse(*base, "--new-skill-name", "skillcompose")
        rc_conf, conf = parse(*base, "--new-skill-name", "a-b", "--name", "c-d")
        rc_none, none = parse(*base)
        rc_slash, slash = parse(*base, "--new-skill-name", "/fantasy-draft", "--new")
        rc_bare_new, bare_new = parse(*base, "--new")

        pkg = tmp / "pkg"
        pkg.mkdir()
        (pkg / "SKILL.md").write_text("---\nname: x\ndescription: x\n---\nnew\n", encoding="utf-8")

        def install(name: str) -> subprocess.CompletedProcess:
            return subprocess.run(["bash", str(INSTALL), str(pkg), "--name", name, "--new"], env=env, capture_output=True, text=True)

        inst_taken = install("old-fantasy")
        old_intact = (home / ".cursor" / "skills" / "old-fantasy" / "SKILL.md").read_text(encoding="utf-8") == "old\n"
        inst_fresh = install("fantasy-novel-v2")

        checks = {
            "fresh_name_accepted": rc_ok == 0 and ok.get("new_skill_name") == "fantasy-novel-v2" and ok.get("name") == "fantasy-novel-v2",
            "installed_name_refused": rc_taken == 2 and taken.get("error") == "new_skill_name_taken" and bool(taken.get("installed_at")),
            "invalid_name_refused": rc_bad == 2 and bad.get("error") == "invalid_new_skill_name",
            "reserved_name_refused": rc_res == 2 and res.get("error") == "reserved_new_skill_name",
            "conflicting_name_refused": rc_conf == 2 and conf.get("error") == "conflicting_skill_names",
            "flag_optional": rc_none == 0 and none.get("new_skill_name") is None,
            "leading_slash_dropped_with_new": rc_slash == 0 and slash.get("new_skill_name") == "fantasy-draft",
            "bare_new_refused": rc_bare_new == 2 and bare_new.get("error") == "new_requires_new_skill_name",
            "installer_new_refuses_existing": inst_taken.returncode == 2 and "skill_name_taken" in inst_taken.stdout,
            "existing_skill_untouched": old_intact,
            "installer_new_accepts_fresh": inst_fresh.returncode == 0
            and (home / ".cursor" / "skills" / "fantasy-novel-v2" / "SKILL.md").is_file(),
        }
    ok_all = all(checks.values())
    print(json.dumps({"ok": ok_all, "checks": checks}, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
