#!/usr/bin/env python3
"""Resolve a single owner/repo@skill pin without a full discover pass.

Used when --pin is set: build a minimal enriched candidate via `gh repo view`
(+ optional skills.sh installs hint) so pick_eligible / audit-only paths do not
require candidates_enriched.jsonl from discover_skills.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PIN_RE = re.compile(r"^([^/]+)/([^@]+)@(.+)$")


def parse_pin(pin: str) -> tuple[str, str, str] | None:
    m = PIN_RE.match(pin.strip())
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


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


def skills_sh_installs(owner: str, repo: str, skill: str) -> int | None:
    """Best-effort installs scrape from skills.sh card; None if unavailable."""
    url = f"https://skills.sh/{owner}/{repo}/{skill}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "skillremix-pin-fastpath"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    # Heuristic: look for install counts like "1.4k" or "1400"
    m = re.search(r"([\d.]+)\s*k\s*installs", html, re.I)
    if m:
        try:
            return int(float(m.group(1)) * 1000)
        except ValueError:
            pass
    m = re.search(r"([\d,]+)\s*installs", html, re.I)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def resolve_pin(
    pin: str,
    *,
    min_installs: int = 80,
    min_stars: int = 15,
    allow_below_floor: bool = False,
) -> dict:
    parsed = parse_pin(pin)
    if not parsed:
        return {
            "ok": False,
            "error": "pin_format",
            "message": "pin must be owner/repo@skill",
            "pin": pin,
        }
    owner, repo, skill = parsed
    owner_repo = f"{owner}/{repo}"
    info = gh_repo(owner_repo)
    if "error" in info:
        return {"ok": False, "error": "github", "message": info["error"], "pin": pin}

    installs = skills_sh_installs(owner, repo, skill)
    stars = info.get("stargazerCount")
    lic = info.get("licenseInfo") or {}
    # Adoption floor: installs meet min OR stars meet min (same as pick_eligible)
    meets = False
    if installs is not None and int(installs) >= min_installs:
        meets = True
    elif stars is not None and int(stars) >= min_stars and installs is None:
        # stars-only when installs unknown — still require min_stars, but prefer installs
        meets = int(stars) >= max(min_stars, min_installs)  # stricter when proxying
    elif stars is not None and installs is not None:
        meets = int(installs) >= min_installs or int(stars) >= min_stars
    elif stars is not None:
        meets = int(stars) >= min_stars

    if not meets and not allow_below_floor:
        return {
            "ok": False,
            "error": "below_adoption_floor",
            "message": (
                f"pin {pin} below adoption floor "
                f"(installs={installs}, stars={stars}; need installs>={min_installs} or stars>={min_stars})"
            ),
            "pin": pin,
            "installs": installs,
            "stars": stars,
            "hint": "pick another pin or pass --allow-below-floor (not recommended)",
        }

    row = {
        "id": pin,
        "installs": installs if installs is not None else (stars or 0),
        "installs_approx": installs,
        "installs_source": "skills_sh" if installs is not None else "stars_proxy",
        "query": skill.replace("-", " "),
        "source": "pin_fastpath",
        "url": info.get("url") or f"https://github.com/{owner_repo}",
        "skill_subdir": ".",
        "discovery_role": "pinned",
        "skills_sh_url": f"https://skills.sh/{owner}/{repo}/{skill}",
        "stars": stars,
        "license": lic.get("key") or lic.get("name"),
        "pushed_at": info.get("pushedAt"),
        "archived": info.get("isArchived"),
        "github_url": info.get("url"),
        "github_description": info.get("description"),
        "why_eligible": f"pin_fastpath resolved {pin}",
        "below_floor_allowed": bool(allow_below_floor and not meets),
    }
    return {"ok": True, "chosen": row}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pin", required=True, help="owner/repo@skill")
    ap.add_argument("--min-installs", type=int, default=80)
    ap.add_argument("--min-stars", type=int, default=15)
    ap.add_argument(
        "--allow-below-floor",
        action="store_true",
        help="Allow pins that miss the adoption floor (not recommended)",
    )
    ap.add_argument("--write-chosen", type=Path, default=None)
    ap.add_argument("--write-candidates", type=Path, default=None, help="One-line jsonl for pick_eligible")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    out = resolve_pin(
        args.pin,
        min_installs=args.min_installs,
        min_stars=args.min_stars,
        allow_below_floor=args.allow_below_floor,
    )
    if not out.get("ok"):
        print(json.dumps(out, indent=2))
        return 2
    row = out["chosen"]
    if args.write_chosen:
        args.write_chosen.parent.mkdir(parents=True, exist_ok=True)
        args.write_chosen.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        out["chosen_path"] = str(args.write_chosen)
    if args.write_candidates:
        args.write_candidates.parent.mkdir(parents=True, exist_ok=True)
        args.write_candidates.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        out["candidates_path"] = str(args.write_candidates)
    print(json.dumps(out, indent=2) if args.json else json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
