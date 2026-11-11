#!/usr/bin/env python3
"""Discover eligible marketplace skill candidates via `npx skills find` (+ domain packs).

When remixing a large --n, also search **practice-support** skills: capabilities you would
need while practicing the domain end-to-end, even if those skills are not *only* about
the domain (verify, research, git, evals, handoff, install UX, …).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ANSI strip
ANSI = re.compile(r"\x1b\[[0-9;]*m")

LINE_ID = re.compile(
    r"(?P<id>[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+)"
)
INSTALLS = re.compile(r"(?P<n>\d+(?:\.\d+)?)(?P<suf>[KkMm]?)\s+installs")
URL = re.compile(r"https://skills\.sh/(?P<path>[^\s]+)")

# Domain-exact marketplace searches
DOMAIN_PACKS = {
    "writing": ["novel writing", "fiction draft", "chapter outline", "creative writing", "story writing"],
    "devops": ["ci cd", "deploy", "kubernetes", "docker", "terraform"],
    "data": ["synthetic data", "csv", "sql", "dataset", "etl"],
    "research": ["arxiv", "literature review", "citation", "eval harness", "verification"],
    "automation": ["desktop", "browser", "filesystem", "rename files", "computer use"],
    "general": ["skill", "agent workflow", "claude skill", "cursor skill", "plan"],
}

# Skills necessary when *practicing* the domain end-to-end — not only domain-labeled skills.
# Used when --n is large (or --practice-support on).
PRACTICE_SUPPORT_PACKS = {
    "writing": [
        "manuscript verify",
        "prose revision",
        "story continuity memory",
        "character bible",
        "research notes",
        "citation bibliography",
        "llm as judge eval",
        "false done verification",
        "git commit workflow",
        "file organization",
    ],
    "devops": [
        "observability monitoring",
        "incident response",
        "secrets management",
        "test automation",
        "infrastructure review",
        "runbook documentation",
        "rollback recovery",
        "false done verification",
        "gitops",
    ],
    "data": [
        "data quality validation",
        "schema design",
        "privacy pii scrub",
        "eval harness",
        "pipeline orchestration",
        "sql review",
        "false done verification",
        "documentation",
    ],
    "research": [
        "note taking zettelkasten",
        "pdf extract",
        "claim verification",
        "experiment tracking",
        "reproducible eval",
        "false done verification",
        "bibliography citation",
        "writing outline",
    ],
    "automation": [
        "filesystem verify",
        "screenshot ocr",
        "retry recovery",
        "task planning",
        "false done verification",
        "logging audit trail",
        "permissions sandbox",
    ],
    "general": [
        "verification false done",
        "eval harness metrics",
        "git workflow",
        "install dual skill",
        "handoff pack schema",
        "resume checkpoint",
        "documentation readme",
    ],
}

# Always useful glue when composing a large remix, regardless of domain
UNIVERSAL_PRACTICE_SUPPORT = [
    "agent skill verify",
    "llm as judge",
    "eval harness",
    "checkpoint resume",
    "skill install",
]

# Remix size at/above which practice-support queries auto-enable
LARGE_N_THRESHOLD = 5


def parse_installs(text: str) -> int | None:
    m = INSTALLS.search(text)
    if not m:
        return None
    n = float(m.group("n"))
    suf = (m.group("suf") or "").upper()
    mult = {"": 1, "K": 1_000, "M": 1_000_000}.get(suf, 1)
    return int(n * mult)


def parse_skills_find(output: str, query: str, role: str) -> list[dict]:
    text = ANSI.sub("", output)
    rows: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        mid = LINE_ID.search(line)
        if mid:
            if current:
                rows.append(current)
            current = {
                "id": mid.group("id"),
                "installs": parse_installs(line),
                "query": query,
                "source": "skills_sh",
                "url": None,
                "skill_subdir": ".",
                "discovery_role": role,
            }
            owner_repo = current["id"].split("@", 1)[0]
            current["url"] = f"https://github.com/{owner_repo}"
            continue
        if current:
            um = URL.search(line)
            if um:
                current["skills_sh_url"] = f"https://skills.sh/{um.group('path')}"
            if current.get("installs") is None:
                inst = parse_installs(line)
                if inst is not None:
                    current["installs"] = inst
    if current:
        rows.append(current)
    return rows


def run_find(query: str, timeout: int = 90) -> str:
    try:
        proc = subprocess.run(
            ["npx", "--yes", "skills", "find", query],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (proc.stdout or "") + "\n" + (proc.stderr or "")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"ERROR: {e}"


def resolve_practice_support(mode: str, n: int | None) -> bool:
    mode = (mode or "auto").lower()
    if mode in {"on", "true", "1", "yes"}:
        return True
    if mode in {"off", "false", "0", "no"}:
        return False
    # auto
    return n is not None and n >= LARGE_N_THRESHOLD


def build_query_plan(
    domain: str | None,
    extra: str,
    explicit: list[str],
    practice_support: bool,
    max_queries: int,
) -> list[tuple[str, str]]:
    """Return ordered (query, discovery_role) pairs."""
    plan: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(q: str, role: str):
        q = q.strip()
        if not q or q in seen:
            return
        seen.add(q)
        plan.append((q, role))

    for q in explicit:
        add(q, "domain_core")
    if domain:
        for q in DOMAIN_PACKS.get(domain, []):
            add(q, "domain_core")
    if extra.strip():
        add(extra.strip(), "domain_core")
    if not plan:
        for q in DOMAIN_PACKS["general"]:
            add(q, "domain_core")

    if practice_support:
        pack = PRACTICE_SUPPORT_PACKS.get(domain or "general", PRACTICE_SUPPORT_PACKS["general"])
        for q in pack:
            add(q, "practice_support")
        for q in UNIVERSAL_PRACTICE_SUPPORT:
            add(q, "practice_support")

    return plan[:max_queries]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True, help="candidates.jsonl path")
    ap.add_argument("--query", action="append", default=[], help="Repeatable search query")
    ap.add_argument("--domain", default=None, choices=sorted(DOMAIN_PACKS.keys()))
    ap.add_argument("--extra", default="", help="Free-form query appended")
    ap.add_argument(
        "--n",
        type=int,
        default=None,
        help="Remix size; when >= %d (auto), expand practice-support queries" % LARGE_N_THRESHOLD,
    )
    ap.add_argument(
        "--practice-support",
        choices=["auto", "on", "off"],
        default="auto",
        help="Include practice-adjacent skills (not only domain-exact). auto: on when --n is large",
    )
    ap.add_argument(
        "--max-queries",
        type=int,
        default=None,
        help="Cap search queries (default 6; 14 when practice-support on)",
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--no-cache-store",
        action="store_true",
        help="Do not auto-store candidates into discover_cache after a successful run",
    )
    ap.add_argument(
        "--local-only",
        action="store_true",
        help="Do not call skills find / network — only reuse discover_cache hit for domain+extra",
    )
    args = ap.parse_args()

    if args.local_only:
        try:
            from discover_cache import cache_paths  # type: ignore
            import time as _time

            cand, meta_path = cache_paths(args.domain or "general", args.extra or "")
            if not cand.is_file():
                miss = {
                    "decision": "FAIL",
                    "error": "local_only_cache_miss",
                    "message": (
                        f"no discover_cache for domain={args.domain or 'general'!r} "
                        f"extra={args.extra or ''!r} — run a networked discover once, or drop --local-only"
                    ),
                    "hint": "python3 scripts/discover_cache.py --domain … --extra … --lookup",
                }
                print(json.dumps(miss, indent=2) if args.json else miss)
                return 2
            import shutil

            args.out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cand, args.out)
            rows = [
                json.loads(l)
                for l in args.out.read_text(encoding="utf-8").splitlines()
                if l.strip()
            ]
            age = None
            if meta_path.is_file():
                try:
                    m = json.loads(meta_path.read_text(encoding="utf-8"))
                    age = _time.time() - float(m.get("stored_at") or 0)
                except (json.JSONDecodeError, TypeError, ValueError):
                    age = None
            summary = {
                "decision": "PASS" if rows else "FAIL",
                "local_only": True,
                "cache_hit": str(cand),
                "cache_age_sec": age,
                "n_candidates": len(rows),
                "out": str(args.out),
                "n_queries": 0,
                "queries": [],
            }
            print(json.dumps(summary, indent=2) if args.json else summary)
            return 0 if rows else 2
        except Exception as e:  # noqa: BLE001
            err = {"decision": "FAIL", "error": "local_only_failed", "message": str(e)}
            print(json.dumps(err, indent=2) if args.json else err)
            return 2

    use_support = resolve_practice_support(args.practice_support, args.n)
    max_q = args.max_queries if args.max_queries is not None else (14 if use_support else 6)
    plan = build_query_plan(args.domain, args.extra, list(args.query), use_support, max_q)

    all_rows: list[dict] = []
    by_id: dict[str, dict] = {}
    for q, role in plan:
        raw = run_find(q)
        for row in parse_skills_find(raw, q, role):
            prev = by_id.get(row["id"])
            if prev is None:
                by_id[row["id"]] = row
                all_rows.append(row)
            else:
                if (row.get("installs") or 0) > (prev.get("installs") or 0):
                    prev["installs"] = row["installs"]
                prev.setdefault("queries", [prev.get("query")])
                if isinstance(prev.get("queries"), list):
                    prev["queries"].append(q)
                # If any search found it as domain_core, keep that; else keep practice_support
                roles = set(prev.get("discovery_roles") or [prev.get("discovery_role")])
                roles.add(role)
                prev["discovery_roles"] = sorted(roles)
                if "domain_core" in roles:
                    prev["discovery_role"] = "domain_core"
                elif prev.get("discovery_role") != "domain_core":
                    prev["discovery_role"] = role

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    cache_stored = None
    summary_cache_error = None
    if all_rows and not args.no_cache_store:
        try:
            from discover_cache import cache_paths  # type: ignore

            import shutil
            import time as _time

            cand, meta = cache_paths(args.domain or "general", args.extra or "")
            cand.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(args.out, cand)
            meta.write_text(
                json.dumps(
                    {
                        "domain": args.domain or "general",
                        "extra": args.extra or "",
                        "stored_at": _time.time(),
                        "src": str(args.out),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            cache_stored = str(cand)
        except Exception as e:  # noqa: BLE001 — cache must not fail discover
            cache_stored = None
            summary_cache_error = str(e)

    n_core = sum(1 for r in all_rows if r.get("discovery_role") == "domain_core")
    n_support = sum(1 for r in all_rows if r.get("discovery_role") == "practice_support")
    summary = {
        "decision": "PASS" if all_rows else "FAIL",
        "n_queries": len(plan),
        "queries": [q for q, _ in plan],
        "query_plan": [{"query": q, "role": role} for q, role in plan],
        "practice_support": use_support,
        "large_n_threshold": LARGE_N_THRESHOLD,
        "n": args.n,
        "n_candidates": len(all_rows),
        "n_domain_core": n_core,
        "n_practice_support": n_support,
        "out": str(args.out),
        "cache_stored": cache_stored,
        "top": sorted(
            [r for r in all_rows if r.get("installs") is not None],
            key=lambda r: r["installs"],
            reverse=True,
        )[:8],
    }
    if summary_cache_error:
        summary["cache_store_error"] = summary_cache_error
    print(json.dumps(summary, indent=2) if args.json else summary)
    return 0 if all_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
