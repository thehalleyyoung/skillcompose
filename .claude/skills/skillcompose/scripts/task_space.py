#!/usr/bin/env python3
"""Task-space atlas for the skillcompose forge (all 50 rounds).

Formal role: expand coverage of a discrete chart θ: X → ∏ A_a while each round
improves a named desired-output property φ. See references/forge_formal_methods.md.

  task_space.py init-atlas --fork F [--domain writing|automation|devops|generic]
  task_space.py register  --fork F --round R --coords '{...}' --phi NAME [--task-summary S]
  task_space.py check     --fork F --round R [--json]
  task_space.py coverage  --fork F [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MIN_COVERAGE_FRACTION = 0.5
SCHEMA = "skillcompose.task_space.v1"

# Domain presets: small discrete axes so coverage is checkable.
PRESETS: dict[str, dict[str, list[str]]] = {
    "writing": {
        "time": ["dawn", "noon", "dusk", "night", "rain"],
        "place": ["well", "road", "scaffold", "kiln", "market", "doorway", "camp"],
        "cast": ["one", "two", "three"],
        "pressure": ["scarcity", "travel", "ownership", "silence", "export"],
    },
    "automation": {
        "stage": ["parse", "plan", "apply", "verify", "rollback"],
        "failure": ["clean", "partial", "conflict", "timeout"],
        "iface": ["cli", "api", "file"],
    },
    "devops": {
        "surface": ["webhook", "auth", "deps", "ci", "runtime"],
        "severity": ["fail-closed", "fail-open", "idempotent"],
        "evidence": ["log", "diff", "repro", "fix"],
    },
    "generic": {
        "mode": ["happy", "edge", "adversarial", "abstain"],
        "size": ["small", "medium", "large"],
        "iface": ["default", "optional-args", "required-args"],
    },
    "unify": {
        "obligation": [
            "dead_carrier",
            "handoff",
            "projector",
            "gate",
            "carrier",
            "args_interface",
            "wholeness",
            "docs",
            "member_wire",
            "phi_c",
        ],
        "surface": ["procedure", "code", "docs", "proof", "ux"],
    },
}


def atlas_path(fork: Path) -> Path:
    return fork / "forge" / "task_space" / "atlas.json"


def coords_path(fork: Path, rnd: int) -> Path:
    if rnd >= 11:
        return fork / "forge" / "outcomes" / f"r{rnd:02d}" / "task_coords.json"
    return fork / "forge" / "task_space" / "rounds" / f"r{rnd:02d}.json"


def load_atlas(fork: Path) -> dict[str, Any] | None:
    p = atlas_path(fork)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def init_atlas(fork: Path, domain: str) -> dict[str, Any]:
    axes = dict(PRESETS.get(domain, PRESETS["generic"]))
    # Always include unify axes so rounds 1–10 share one atlas.
    for k, vals in PRESETS["unify"].items():
        axes.setdefault(k, vals)
    doc = {
        "schema": SCHEMA,
        "domain": domain,
        "axes": axes,
        "min_coverage_fraction": MIN_COVERAGE_FRACTION,
        "note": (
            "Each forge round registers coordinates on these axes and a desired "
            "property phi. Novelty expands coverage of the task chart."
        ),
    }
    p = atlas_path(fork)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def _cell(coords: dict[str, str], axes: dict[str, list[str]]) -> tuple[str, ...]:
    # Stable cell key: only atlas axes that appear in coords, sorted by axis name.
    parts = []
    for a in sorted(axes):
        if a in coords and coords[a] is not None:
            parts.append(f"{a}={coords[a]}")
    return tuple(parts)


def _hamming(c1: dict[str, str], c2: dict[str, str], axes: list[str]) -> int:
    n = 0
    for a in axes:
        if c1.get(a) != c2.get(a):
            n += 1
    return n


def prior_registrations(fork: Path, upto: int) -> list[dict[str, Any]]:
    rows = []
    for r in range(1, upto):
        p = coords_path(fork, r)
        if not p.is_file():
            continue
        try:
            rows.append({"round": r, **json.loads(p.read_text(encoding="utf-8"))})
        except (OSError, ValueError):
            continue
    return rows


def register(
    fork: Path,
    rnd: int,
    coords: dict[str, str],
    phi: str,
    task_summary: str = "",
) -> dict[str, Any]:
    atlas = load_atlas(fork)
    if atlas is None:
        raise SystemExit("atlas missing: run task_space.py init-atlas --fork …")
    axes: dict[str, list[str]] = atlas["axes"]
    # Validate
    for k, v in coords.items():
        if k not in axes:
            raise SystemExit(f"unknown axis {k!r}; atlas axes: {sorted(axes)}")
        if v not in axes[k]:
            raise SystemExit(f"value {v!r} not in axis {k}: {axes[k]}")
    if rnd <= 10:
        if "obligation" not in coords:
            raise SystemExit("rounds 1–10 require coords.obligation (unify cell)")
    else:
        # Prefer domain axes present besides unify-only
        domain_axes = [a for a in coords if a not in ("obligation", "surface")]
        if not domain_axes:
            raise SystemExit("rounds ≥11 require at least one domain axis in coords")
    if not isinstance(phi, str) or len(phi.strip()) < 3:
        raise SystemExit("phi must name a desired output property (≥3 chars)")

    doc = {
        "schema": SCHEMA,
        "round": rnd,
        "coords": coords,
        "phi": phi.strip(),
        "task_summary": (task_summary or "").strip(),
        "cell": list(_cell(coords, axes)),
    }
    p = coords_path(fork, rnd)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def check(fork: Path, rnd: int) -> dict[str, Any]:
    atlas = load_atlas(fork)
    reasons: list[str] = []
    if atlas is None:
        return {
            "decision": "FAIL",
            "round": rnd,
            "reasons": ["forge/task_space/atlas.json missing — init-atlas first"],
        }
    axes: dict[str, list[str]] = atlas["axes"]
    p = coords_path(fork, rnd)
    if not p.is_file():
        return {
            "decision": "FAIL",
            "round": rnd,
            "reasons": [
                f"{p.relative_to(fork)} missing — register coords+phi for this round"
            ],
        }
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return {"decision": "FAIL", "round": rnd, "reasons": [f"unreadable coords: {e}"]}

    coords = doc.get("coords") if isinstance(doc.get("coords"), dict) else {}
    phi = doc.get("phi") if isinstance(doc.get("phi"), str) else ""
    if len(phi.strip()) < 3:
        reasons.append("phi missing/too short")
    for k, v in coords.items():
        if k not in axes:
            reasons.append(f"unknown axis {k}")
        elif v not in axes[k]:
            reasons.append(f"invalid {k}={v}")
    if rnd <= 10 and "obligation" not in coords:
        reasons.append("unify rounds need coords.obligation")
    if rnd >= 11 and not [a for a in coords if a not in ("obligation", "surface")]:
        reasons.append("outcome rounds need a domain axis in coords")

    priors = prior_registrations(fork, rnd)
    cell = _cell({str(k): str(v) for k, v in coords.items()}, axes)
    prior_cells = {
        tuple(r.get("cell") or _cell(r.get("coords") or {}, axes)) for r in priors
    }
    novel_cell = cell not in prior_cells and bool(cell)
    prior_phis = {str(r.get("phi", "")).strip() for r in priors}
    novel_phi = phi.strip() not in prior_phis

    # Atlas saturation?
    # Approximate |∏ A| can explode; use covered fraction of *seen projection*
    # Require: novel cell OR (atlas has ≥ min coverage of registered unique cells
    # relative to a soft cap) and novel phi.
    unique_prior = len(prior_cells)
    soft_cap = max(1, min(200, _soft_product(axes)))
    saturated = unique_prior >= max(
        int(atlas.get("min_coverage_fraction", MIN_COVERAGE_FRACTION) * soft_cap),
        min(soft_cap, max(8, rnd // 2)),
    )

    if not novel_cell and not (saturated and novel_phi):
        reasons.append(
            "task cell not novel vs prior rounds; after saturation you must target a new phi"
        )
    if not novel_cell and saturated and not novel_phi:
        reasons.append(f"phi {phi!r} already used; pick a new desired property")

    out = {
        "decision": "PASS" if not reasons else "FAIL",
        "round": rnd,
        "reasons": reasons,
        "cell": list(cell),
        "novel_cell": novel_cell,
        "novel_phi": novel_phi,
        "saturated": saturated,
        "prior_cells": unique_prior,
        "phi": phi.strip(),
        "coords_path": str(p.relative_to(fork)),
    }
    return out


def _soft_product(axes: dict[str, list[str]]) -> int:
    # Cap product to avoid huge numbers; prefer domain axes if present.
    keys = [k for k in axes if k not in ("obligation", "surface")] or list(axes)
    n = 1
    for k in keys[:4]:
        n *= max(1, len(axes[k]))
        if n > 500:
            return 500
    return n


def coverage(fork: Path) -> dict[str, Any]:
    atlas = load_atlas(fork)
    if atlas is None:
        return {"decision": "FAIL", "reasons": ["atlas missing"]}
    axes = atlas["axes"]
    rows = prior_registrations(fork, 51)
    cells = []
    phis = []
    for r in rows:
        c = tuple(r.get("cell") or _cell(r.get("coords") or {}, axes))
        if c:
            cells.append(c)
        if r.get("phi"):
            phis.append(str(r["phi"]).strip())
    unique_cells = sorted(set(cells))
    unique_phis = sorted(set(phis))
    soft = _soft_product(axes)
    frac = round(len(unique_cells) / soft, 4) if soft else 0.0
    min_frac = float(atlas.get("min_coverage_fraction", MIN_COVERAGE_FRACTION))
    reasons = []
    if len(rows) >= 11 and frac < min_frac and len(unique_phis) < max(8, len(rows) // 3):
        reasons.append(
            f"coverage fraction {frac} < {min_frac} and too few distinct phis ({len(unique_phis)})"
        )
    return {
        "decision": "PASS" if not reasons else "FAIL",
        "rounds_registered": len(rows),
        "unique_cells": len(unique_cells),
        "unique_phis": len(unique_phis),
        "soft_chart_size": soft,
        "coverage_fraction": frac,
        "min_coverage_fraction": min_frac,
        "phis": unique_phis,
        "reasons": reasons,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ia = sub.add_parser("init-atlas")
    ia.add_argument("--fork", type=Path, required=True)
    ia.add_argument("--domain", default="generic")

    rg = sub.add_parser("register")
    rg.add_argument("--fork", type=Path, required=True)
    rg.add_argument("--round", type=int, required=True)
    rg.add_argument("--coords", required=True, help="JSON object of axis→value")
    rg.add_argument("--phi", required=True)
    rg.add_argument("--task-summary", default="")

    ch = sub.add_parser("check")
    ch.add_argument("--fork", type=Path, required=True)
    ch.add_argument("--round", type=int, required=True)

    cv = sub.add_parser("coverage")
    cv.add_argument("--fork", type=Path, required=True)

    for p in (ia, rg, ch, cv):
        p.add_argument("--json", action="store_true")

    args = ap.parse_args()
    if args.cmd == "init-atlas":
        out = init_atlas(args.fork, args.domain)
    elif args.cmd == "register":
        try:
            coords = json.loads(args.coords)
        except ValueError as e:
            raise SystemExit(f"--coords must be JSON object: {e}") from e
        if not isinstance(coords, dict):
            raise SystemExit("--coords must be a JSON object")
        out = register(args.fork, args.round, {str(k): str(v) for k, v in coords.items()}, args.phi, args.task_summary)
    elif args.cmd == "check":
        out = check(args.fork, args.round)
    else:
        out = coverage(args.fork)

    print(json.dumps(out, indent=2))
    if args.cmd in ("check", "coverage"):
        return 0 if out.get("decision") == "PASS" else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
