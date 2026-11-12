#!/usr/bin/env python3
"""Score remix member complementarity vs query/domain; reject incoherent picks.

Reads chosen_n.json (+ optional query/domain) and exits 2 if any member falls
below --min-score (default 0.15) unless --allow-weak.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= 3}


# Domain packs → expected vocabulary
DOMAIN_TOKENS = {
    "writing": tokens("novel story fiction chapter prose outline character plot writing creative"),
    "research": tokens(
        "research literature review paper arxiv citation systematic search evidence science academic"
    ),
    "devops": tokens("deploy ci cd docker kubernetes terraform devops infrastructure pipeline"),
    "data": tokens("data etl pandas spark sql warehouse analytics dataframe"),
    "automation": tokens("automate workflow agent bot schedule script orchestration"),
}

# Framework / stack tokens that are rarely the intended domain skill
OFF_DOMAIN = {
    "springboot",
    "laravel",
    "django",
    "rails",
    "kubernetes",
    "helm",
    "terraform",
    "react",
    "vue",
    "storybook",
    "reactnative",
}

# github_description lexicons that contradict packed domains (UC03 writing false-PASS)
DESC_ALIEN = {
    "writing": tokens(
        "security scanner vulnerability malicious kubernetes docker terraform "
        "storybook component ui kit react native mobile devops infrastructure"
    ),
    "research": tokens(
        "springboot laravel kubernetes helm terraform react vue storybook ecommerce"
    ),
    "devops": tokens("novel fiction chapter prose romance manga fanfiction"),
    "data": tokens("novel fiction chapter prose romance kubernetes helm"),
    "automation": tokens("novel fiction chapter prose romance manga"),
}


def member_blob(m: dict) -> str:
    parts = [
        m.get("id") or "",
        m.get("query") or "",
        m.get("github_description") or "",
        m.get("skills_sh_url") or "",
        (m.get("id") or "").split("@")[-1].replace("-", " "),
    ]
    return " ".join(parts)


def score_member(m: dict, query: str, domain: str | None) -> dict:
    qtok = tokens(query)
    domain_l = (domain or "").lower()
    dtok = DOMAIN_TOKENS.get(domain_l, set())
    target = qtok | dtok
    desc = m.get("github_description") or ""
    slug = ((m.get("id") or "").split("@")[-1] or "").replace("-", " ")
    blob = member_blob(m)
    mtok = tokens(blob)
    desc_tok = tokens(desc)
    slug_tok = tokens(slug)
    if not target:
        overlap = 0.0
    else:
        # Prefer description+query overlap; dampen slug-only matches that also
        # carry OFF_DOMAIN stack tokens (UC03 Storybook "writing-*" false-PASS).
        full = len(target & mtok) / max(1, len(target))
        via_slug = len(target & slug_tok) / max(1, len(target))
        via_desc = len(target & desc_tok) / max(1, len(target)) if desc_tok else 0.0
        id_tok = tokens(m.get("id") or "")
        stack_in_id = bool(OFF_DOMAIN & (slug_tok | id_tok))
        if (
            via_desc == 0.0
            and via_slug > 0.0
            and full <= via_slug + 0.05
            and stack_in_id
        ):
            overlap = min(full, 0.12)
        else:
            overlap = full
    penalty = 0.0
    hits = sorted(OFF_DOMAIN & mtok)
    # Off-domain stack hits penalize any packed domain (not only research)
    if hits and (dtok or qtok):
        penalty = max(penalty, 0.5 if domain_l in {"research", "writing"} else 0.35)
    # Description contradicts domain lexicon (security scanner as "writing", etc.)
    alien = DESC_ALIEN.get(domain_l, set())
    alien_hits = sorted(alien & desc_tok) if desc_tok and alien else []
    if alien_hits:
        penalty = max(penalty, 0.55)
        hits = sorted(set(hits) | set(alien_hits))
    score = max(0.0, overlap - penalty)
    # Practice-support / verify-eval skills are allowed floors when not off-domain
    role = (m.get("discovery_role") or "").lower()
    supportish = role in {"practice_support", "support"} or bool(
        mtok & {"eval", "verify", "harness", "citation", "arxiv", "handoff"}
    )
    if supportish and not hits and not alien_hits:
        score = max(score, 0.2)
    return {
        "id": m.get("id"),
        "score": round(score, 4),
        "overlap": round(overlap, 4),
        "off_domain_hits": hits,
        "penalty": round(penalty, 4),
        "supportish": supportish,
        "alien_desc_hits": alien_hits,
    }


def evaluate(chosen_n: dict, query: str, domain: str | None, min_score: float) -> dict:
    members = chosen_n.get("chosen") if isinstance(chosen_n.get("chosen"), list) else []
    scored = [score_member(m, query, domain) for m in members if isinstance(m, dict)]
    weak = [s for s in scored if s["score"] < min_score]
    return {
        "ok": len(weak) == 0,
        "min_score": min_score,
        "query": query,
        "domain": domain,
        "members": scored,
        "weak": weak,
        "n": len(scored),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chosen-n", type=Path, required=True)
    ap.add_argument("--query", default="")
    ap.add_argument("--domain", default=None)
    ap.add_argument("--min-score", type=float, default=0.15)
    ap.add_argument("--allow-weak", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    chosen_n = json.loads(args.chosen_n.read_text(encoding="utf-8"))
    result = evaluate(chosen_n, args.query, args.domain, args.min_score)
    if args.allow_weak:
        result["ok"] = True
        result["allowed_weak"] = True
    print(json.dumps(result, indent=2) if args.json else json.dumps(result))
    if not result["ok"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
