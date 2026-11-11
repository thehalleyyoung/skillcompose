#!/usr/bin/env python3
"""Information-Theoretic MDL / Lempel-Ziv Novelty, Context-SNR, and Lyapunov Debt Analyzer.

Prevents Goodhart specification gaming of raw `chars_changed >= 1000` by measuring:
  1. Conditional Lempel-Ziv / DEFLATE Complexity Gain:
         Delta_C = C(Tree_prev || Patch) - C(Tree_prev)
     Copy-pasted prose or whitespace padding compresses to ~0 new bytes (`info_density -> 0`),
     whereas genuine executable code, schemas, and distinct test cases carry high LZ novelty.
  2. Exogenous Grounding Ratio:
     Fraction of package bytes living in deterministic executable checks (`scripts/`, `evals/`,
     JSON schemas) vs ungrounded natural-language prompt text.
  3. Attention Channel SNR & Progressive Disclosure Score:
     Measures how effectively `SKILL.md` acts as a compact Kleisli interface while hiding
     implementation detail in `scripts/` and `references/` (Parnas Information Hiding).
  4. Vector Lyapunov Potential Phi(pkg):
     Non-negative debt across 5 DAG-ordered engineering invariants; forge rounds must drive
     Phi(x_r) monotonically toward 0 without violating Control Barrier ratchets.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zlib
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".claude", ".cursor", ".codex", ".gemini"}
EXCLUDED_FILES = {"usefulness_forge.jsonl", "USEFULNESS_FORGE.md"}


def _iter_pkg_files(pkg: Path) -> list[Path]:
    out: list[Path] = []
    if not pkg.is_dir():
        return out
    for p in sorted(pkg.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(pkg)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if p.name in EXCLUDED_FILES:
            continue
        out.append(p)
    return out


def compressed_size(data: bytes) -> int:
    return len(zlib.compress(data, level=9))


def commit_mdl_novelty(repo: Path, commit: str = "HEAD") -> dict[str, Any]:
    """Compute conditional compression novelty C(parent || added_lines) - C(parent) for a git commit."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", commit, "--format=", "--"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr.strip()}

    added_lines: list[str] = []
    skip = False
    for line in proc.stdout.splitlines():
        if line.startswith("diff --git "):
            target = line.split(" ")[-1]
            skip = any(f in target for f in EXCLUDED_FILES)
            continue
        if skip or line.startswith(("+++ ", "--- ", "@@")):
            continue
        if line.startswith("+"):
            added_lines.append(line[1:])

    added_blob = "\n".join(added_lines).encode("utf-8", errors="replace")
    raw_added = len(added_blob)
    if raw_added == 0:
        return {
            "ok": True,
            "raw_added_bytes": 0,
            "standalone_compressed_bytes": 0,
            "conditional_lz_bytes": 0,
            "info_density": 0.0,
            "anti_padding_pass": False,
        }

    # Build corpus of parent tree (or current files minus diff) to measure conditional novelty
    parent_proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{commit}~1"],
        capture_output=True,
        text=True,
    )
    prior_chunks: list[bytes] = []
    if parent_proc.returncode == 0:
        ls_proc = subprocess.run(
            ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", f"{commit}~1"],
            capture_output=True,
            text=True,
        )
        for fname in (ls_proc.stdout or "").splitlines()[:80]:
            if any(f in fname for f in EXCLUDED_FILES):
                continue
            blob_p = subprocess.run(
                ["git", "-C", str(repo), "show", f"{commit}~1:{fname}"],
                capture_output=True,
            )
            if blob_p.returncode == 0:
                prior_chunks.append(blob_p.stdout[:32768])

    prior_blob = b"\n".join(prior_chunks)
    c_prior = compressed_size(prior_blob) if prior_blob else 0
    c_joint = compressed_size(prior_blob + b"\n" + added_blob) if prior_blob else compressed_size(added_blob)
    delta_c = max(0, c_joint - c_prior)
    standalone_c = compressed_size(added_blob)
    density = delta_c / max(1, raw_added)

    return {
        "ok": True,
        "raw_added_bytes": raw_added,
        "standalone_compressed_bytes": standalone_c,
        "conditional_lz_bytes": delta_c,
        "info_density": round(density, 4),
        # Repetitive copy-paste / whitespace spam falls below 0.08
        "anti_padding_pass": density >= 0.10 and delta_c >= 80,
    }


def package_telemetry(pkg: Path) -> dict[str, Any]:
    """Measure Context-SNR, Exogenous Grounding Ratio, and Vector Lyapunov Debt Phi(pkg)."""
    files = _iter_pkg_files(pkg)
    skill_md = pkg / "SKILL.md"
    skill_bytes = skill_md.stat().st_size if skill_md.is_file() else 0

    exec_bytes = 0
    ref_bytes = 0
    doc_bytes = 0
    all_blobs: list[bytes] = []

    for f in files:
        rel = f.relative_to(pkg)
        b = f.read_bytes()
        all_blobs.append(b)
        top = rel.parts[0] if len(rel.parts) > 1 else ""
        if f.suffix in {".py", ".sh", ".mjs", ".js"} or top == "evals" or "schema" in f.name.lower():
            exec_bytes += len(b)
        elif top in {"references", "subskills", "skills"}:
            ref_bytes += len(b)
        else:
            doc_bytes += len(b)

    total_bytes = max(1, exec_bytes + ref_bytes + doc_bytes)
    joined = b"\n".join(all_blobs)
    lz_total = compressed_size(joined) if joined else 0

    grounding_ratio = exec_bytes / total_bytes
    encapsulation_ratio = (exec_bytes + ref_bytes) / max(1, skill_bytes + exec_bytes + ref_bytes)

    # Optimal SKILL.md interface window: 1.5KB .. 18KB (high SNR, low lost-in-the-middle dilution)
    if skill_bytes == 0:
        snr_score = 0.0
    elif skill_bytes <= 18000:
        snr_score = min(1.0, 0.55 + 0.45 * encapsulation_ratio)
    else:
        over = (skill_bytes - 18000) / 30000.0
        snr_score = max(0.15, (0.55 + 0.45 * encapsulation_ratio) - over)

    # DAG-ordered Lyapunov Debt Phi(x) >= 0 (0.0 = verified fixpoint)
    has_wiring = (pkg / "forge" / "wiring_graph.json").is_file() or (pkg / "WIRING_CONTRACT.md").is_file()
    has_exec_verify = any(
        "verify" in f.name.lower() and f.suffix in {".py", ".sh"} for f in files
    )
    has_evals = (pkg / "evals").is_dir() and any((pkg / "evals").iterdir())
    has_metrics = (pkg / "METRICS.md").is_file()
    has_awesome = (pkg / "AWESOME_PROOF.md").is_file()

    debts = {
        "d1_interface_and_wiring": 0.0 if (skill_bytes >= 800 and has_wiring) else (0.5 if skill_bytes >= 800 else 1.0),
        "d2_exogenous_grounding": round(max(0.0, 0.22 - grounding_ratio) / 0.22, 4) if not has_exec_verify else 0.0,
        "d3_context_snr_encapsulation": round(max(0.0, 0.70 - snr_score) / 0.70, 4),
        "d4_reproducible_evals_metrics": 0.0 if (has_evals and has_metrics) else (0.4 if has_evals else 1.0),
        "d5_awesome_world_proof": 0.0 if has_awesome else 1.0,
    }
    # Upstream DAG weights > downstream weights
    weights = {
        "d1_interface_and_wiring": 3.0,
        "d2_exogenous_grounding": 2.5,
        "d3_context_snr_encapsulation": 1.8,
        "d4_reproducible_evals_metrics": 1.4,
        "d5_awesome_world_proof": 1.0,
    }
    phi_total = sum(weights[k] * debts[k] for k in debts)
    next_priority = next((k for k in debts if debts[k] > 0.0), "FIXPOINT_REACHED")

    return {
        "package": str(pkg),
        "total_product_bytes": total_bytes,
        "total_lz_compressed_bytes": lz_total,
        "mdl_compression_ratio": round(lz_total / total_bytes, 4),
        "skill_md_bytes": skill_bytes,
        "executable_bytes": exec_bytes,
        "encapsulated_module_bytes": ref_bytes,
        "exogenous_grounding_ratio": round(grounding_ratio, 4),
        "parnas_encapsulation_ratio": round(encapsulation_ratio, 4),
        "attention_snr_score": round(snr_score, 4),
        "lyapunov": {
            "phi_total": round(phi_total, 4),
            "debts": debts,
            "next_upstream_target": next_priority,
            "at_fixpoint": phi_total == 0.0,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("commit", help="Compute conditional LZ novelty for a git commit")
    c.add_argument("--repo", type=Path, required=True)
    c.add_argument("--commit", default="HEAD")
    c.add_argument("--json", action="store_true")

    p = sub.add_parser("package", help="Compute MDL, Context-SNR, and Lyapunov Phi for a package")
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--json", action="store_true")

    args = ap.parse_args()
    if args.cmd == "commit":
        out = commit_mdl_novelty(args.repo, args.commit)
        print(json.dumps(out, indent=2) if args.json else out)
        return 0 if out.get("ok") else 2

    out = package_telemetry(args.package)
    print(json.dumps(out, indent=2) if args.json else out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
