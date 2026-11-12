#!/usr/bin/env python3
"""Enrich candidates.jsonl with GitHub stars, license, pushedAt via `gh`."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PLACEHOLDER_IDS = {
    "owner/repo@skill",
    "owner/repo@name",
    "example/example@example",
}


def is_placeholder_id(sid: str) -> bool:
    s = (sid or "").strip().lower()
    if not s or s in PLACEHOLDER_IDS:
        return True
    if s.startswith("example/") or s.startswith("owner/repo"):
        return True
    if "@" not in s or "/" not in s.split("@", 1)[0]:
        return True
    return False


def gh_repo(owner_repo: str) -> dict:
    try:
        proc = subprocess.run(
            [
                "gh",
                "repo",
                "view",
                owner_repo,
                "--json",
                "nameWithOwner,stargazerCount,licenseInfo,pushedAt,url,isArchived,description",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return {"error": (proc.stderr or proc.stdout or "").strip()[:300]}
        return json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        return {"error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = []
    for line in args.candidates.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))

    enriched = []
    skipped: list[str] = []
    for row in rows[: args.limit]:
        sid = row.get("id") or ""
        if is_placeholder_id(sid):
            skipped.append(sid or "<empty>")
            row = dict(row)
            row["enrich_skipped"] = True
            row["enrich_skip_reason"] = "placeholder_or_invalid_id"
            enriched.append(row)
            continue
        owner_repo = sid.split("@", 1)[0] if "@" in sid else sid
        if "/" not in owner_repo:
            enriched.append(row)
            continue
        info = gh_repo(owner_repo)
        if "error" not in info:
            row = dict(row)
            row["stars"] = info.get("stargazerCount")
            lic = info.get("licenseInfo") or {}
            row["license"] = lic.get("key") or lic.get("name") or row.get("license")
            row["pushed_at"] = info.get("pushedAt")
            row["archived"] = info.get("isArchived")
            row["github_url"] = info.get("url") or row.get("url")
            row["github_description"] = info.get("description")
            if row.get("github_url"):
                row["url"] = row["github_url"]
        else:
            row = dict(row)
            row["github_enrich_error"] = info["error"]
        enriched.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in enriched:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    out = {
        "n": len(enriched),
        "out": str(args.out),
        "with_stars": sum(1 for r in enriched if r.get("stars") is not None),
        "skipped_placeholders": skipped,
        "n_skipped": len(skipped),
    }
    print(json.dumps(out, indent=2) if args.json else out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
