#!/usr/bin/env python3
"""7-Family `agy` + Sonnet 5.5 Blind-Judge Benchmark Runner for `/skillcompose`.

Protocol:
  1. Materializes 7 concrete task families x 3 regimes (`concat`, `union`, `manifold`) = 21 isolated workspaces.
  2. Calls `agy` EXACTLY ONCE per (task_family, regime) in its isolated workspace (`cwd=workspace`).
  3. Evaluates deterministic exogenous `oracle.py` checks on each completed workspace.
  4. Strips `.agents/` skill metadata and constructs a blind, deterministically shuffled judge packet
     (`Candidate_Alpha`, `Candidate_Beta`, `Candidate_Gamma`) per task family so the judge never sees
     which regime (`concat`, `union`, `manifold`) produced which workspace.
  5. Calls `agy` with `--model claude-sonnet-5-5` (Sonnet 5.5) as blind judge once per family,
     de-anonymizes verdicts, and writes full JSON + Markdown scorecards.

Subcommands:
  - `run`           : End-to-end local execution via `agy` CLI (21 solver calls + 7 Sonnet 5.5 judge calls).
  - `prepare-judge` : Run exogenous oracles on 21 workspaces and emit blind judge packets (without `.agents/`).
  - `finalize`      : De-anonymize 7 blind judge JSON files + oracle scores into `summary.json` & `RESULTS.md`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from build_benchmark import REGIMES, materialize_all, prepare_isolated_run_tree  # noqa: E402

BLIND_LABELS: tuple[str, ...] = ("Candidate_Alpha", "Candidate_Beta", "Candidate_Gamma")

BINARY_OR_SKIP_EXTS = {".db", ".sqlite", ".sqlite3", ".pyc", ".png", ".jpg", ".pdf"}


def collect_workspace_snapshot(ws: Path, max_chars_per_file: int = 3800) -> dict[str, str]:
    """Snapshot solver-visible workspace artifacts while stripping `.agents/` skill directories."""
    snap: dict[str, str] = {}
    for p in sorted(ws.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ws)
        if (
            rel.parts[0] in {".agents", "__pycache__", ".git", "spec", "review", "state", ".pytest_cache"}
            or "__pycache__" in rel.parts
            or rel.name == "TASK_PROMPT.md"
        ):
            continue
        rel_s = str(rel)
        if p.suffix.lower() in BINARY_OR_SKIP_EXTS:
            snap[rel_s] = f"<binary file: {p.stat().st_size} bytes, sha256={hashlib.sha256(p.read_bytes()).hexdigest()[:16]}>"
        else:
            txt = p.read_text(encoding="utf-8", errors="replace")
            txt = re.sub(
                r"(?i)\b(Lawvere[-–]Amari\s+manifold\s+landmarks|manifold\s+landmarks|manifold\s+synthesis|Stage\s+1\s+manifold\s+projector|union\s+router)\b",
                "skill specification",
                txt,
            )
            if len(txt) > max_chars_per_file:
                txt = txt[:max_chars_per_file] + f"\n... <truncated {len(txt) - max_chars_per_file} chars>"
            snap[rel_s] = txt
    return snap


def run_oracle(oracle_py: Path, ws: Path) -> dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(oracle_py), str(ws)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    try:
        return json.loads((p.stdout or "").strip().splitlines()[-1])
    except Exception:
        return {
            "passed": False,
            "score": 0.0,
            "checks": {},
            "raw_error": ((p.stdout or "") + (p.stderr or ""))[:500],
        }


def build_blind_judge_packets(
    suite_dir: Path,
    run_root: Path,
    packets_dir: Path,
    seed: str = "skillcompose-sonnet55-blind",
) -> dict[str, Any]:
    """Run exogenous oracles and build 7 blind, shuffled judge prompts + secret mapping keys."""
    manifest = json.loads((suite_dir / "manifest.json").read_text(encoding="utf-8"))
    if packets_dir.exists():
        shutil.rmtree(packets_dir)
    packets_dir.mkdir(parents=True, exist_ok=True)

    secret_map: dict[str, Any] = {}
    for fam in manifest["families"]:
        fid = fam["id"]
        oracle_py = Path(fam["oracle_script"])
        prompt_txt = Path(fam["prompt_file"]).read_text(encoding="utf-8")

        rng = random.Random(f"{seed}:{fid}")
        shuffled_regimes = list(REGIMES)
        rng.shuffle(shuffled_regimes)

        label_to_regime: dict[str, str] = {}
        oracle_by_regime: dict[str, Any] = {}
        candidate_blocks: list[str] = []

        for label, reg in zip(BLIND_LABELS, shuffled_regimes):
            ws = run_root / fid / reg
            label_to_regime[label] = reg
            ora = run_oracle(oracle_py, ws)
            oracle_by_regime[reg] = ora
            files_snap = collect_workspace_snapshot(ws)

            file_sections = []
            for fname, content in files_snap.items():
                file_sections.append(f"#### File: `{fname}`\n```\n{content}\n```")
            files_str = "\n\n".join(file_sections) if file_sections else "*(no files created)*"

            candidate_blocks.append(
                f"## {label}\n\n"
                f"### Exogenous Functional & Invariant Check Telemetry\n"
                f"```json\n{json.dumps(ora, indent=2)}\n```\n\n"
                f"### Produced Workspace Files (`.agents/` stripped for blind review)\n"
                f"{files_str}\n"
            )

        judge_prompt = f"""You are an impartial, rigorous senior Staff Engineer & Mathematical Logic Judge evaluating three anonymous agent runs (`Candidate_Alpha`, `Candidate_Beta`, `Candidate_Gamma`) on Task Family `{fid}` (`{fam['title']}`).

## Original Task Prompt Given to Each Agent
```
{prompt_txt.strip()}
```

## Blind Candidate Submissions
{chr(10).join(candidate_blocks)}

## Blind Evaluation Rubric (Score 0–100 on each dimension per candidate)
1. `functional_correctness` (0–100): Does the code/artifact accurately solve the task and pass deterministic edge cases?
2. `conflict_and_invariant_resolution` (0–100): Did the candidate cleanly resolve competing constraints (e.g. streaming + atomic DB transaction, precedence + 3-valued Kleene `UNKNOWN`, security hardening + backward compatibility, Simpson's stratification vs crude pooling, watermark reordering + zero-sum ledger, close-POV epistemic isolation, or clean off-domain refusal) without dropping soundness invariants?
3. `recombinant_completeness` (0–100): Did the solution synthesize all required multi-stage facets rather than only implementing a single narrow sub-skill?
4. `sheaf_cross_file_consistency` (0–100): Do coupled output artifacts (`api_contract.json` <-> `migration_manifest.json`, `ast_spec.json` <-> `eval_report.json`, `security_advisory.json` <-> `patch_manifest.json`, `stat_summary.json` <-> `evidence_ledger.json`, `balances.json` <-> `audit_summary.json`, `continuity_ledger.json` <-> `canon_state.json`) satisfy exact cross-file schema, digest, and key agreement?
5. `code_and_artifact_craft` (0–100): Cleanliness, determinism, idempotency, absence of `eval()`/slop/hallucinated files.

Compute `overall_score` (0–100, weighted: 35% functional_correctness, 25% conflict_and_invariant_resolution, 15% recombinant_completeness, 15% sheaf_cross_file_consistency, 10% code_and_artifact_craft) for each candidate, rank all three from best to worst (`ranking`: list of labels, ties broken by craft & sheaf discipline), and provide a concise technical `rationale`.

Output **ONLY** valid JSON matching this exact schema:
```json
{{
  "family_id": "{fid}",
  "scores": {{
    "Candidate_Alpha": {{
      "functional_correctness": 0,
      "conflict_and_invariant_resolution": 0,
      "recombinant_completeness": 0,
      "sheaf_cross_file_consistency": 0,
      "code_and_artifact_craft": 0,
      "overall_score": 0.0
    }},
    "Candidate_Beta": {{
      "functional_correctness": 0,
      "conflict_and_invariant_resolution": 0,
      "recombinant_completeness": 0,
      "sheaf_cross_file_consistency": 0,
      "code_and_artifact_craft": 0,
      "overall_score": 0.0
    }},
    "Candidate_Gamma": {{
      "functional_correctness": 0,
      "conflict_and_invariant_resolution": 0,
      "recombinant_completeness": 0,
      "sheaf_cross_file_consistency": 0,
      "code_and_artifact_craft": 0,
      "overall_score": 0.0
    }}
  }},
  "winner": "Candidate_Alpha",
  "ranking": ["Candidate_Alpha", "Candidate_Beta", "Candidate_Gamma"],
  "rationale": "..."
}}
```
"""
        (packets_dir / f"{fid}_judge_prompt.md").write_text(judge_prompt, encoding="utf-8")
        secret_map[fid] = {
            "title": fam["title"],
            "domain": fam["domain"],
            "label_to_regime": label_to_regime,
            "oracle_by_regime": oracle_by_regime,
            "manifold_telemetry": fam["manifold_telemetry"],
        }

    (packets_dir / "blind_key.json").write_text(json.dumps(secret_map, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "packets_dir": str(packets_dir), "families": list(secret_map.keys())}


def _extract_json_obj(raw: str) -> dict[str, Any]:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    candidate = m.group(1) if m else raw[raw.find("{") : raw.rfind("}") + 1]
    return json.loads(candidate)


def finalize_benchmark_report(
    packets_dir: Path,
    verdicts_dir: Path,
    out_json: Path,
    out_md: Path,
    *,
    execution_backend: str,
    judge_model_label: str,
) -> dict[str, Any]:
    """De-anonymize blind judge JSON verdicts + exogenous oracle results into a final scorecard."""
    blind_key = json.loads((packets_dir / "blind_key.json").read_text(encoding="utf-8"))

    per_family = []
    regime_judge_totals = {r: [] for r in REGIMES}
    regime_oracle_totals = {r: [] for r in REGIMES}
    regime_oracle_passes = {r: 0 for r in REGIMES}
    regime_wins = {r: 0 for r in REGIMES}

    for fid, meta in blind_key.items():
        vfile = verdicts_dir / f"{fid}_verdict.json"
        verdict = _extract_json_obj(vfile.read_text(encoding="utf-8"))
        l2r: dict[str, str] = meta["label_to_regime"]

        deanonymized_scores: dict[str, Any] = {}
        for label, reg in l2r.items():
            sc = verdict["scores"][label]
            deanonymized_scores[reg] = sc
            regime_judge_totals[reg].append(float(sc["overall_score"]))
            ora = meta["oracle_by_regime"][reg]
            regime_oracle_totals[reg].append(float(ora["score"]) * 100.0)
            if ora.get("passed"):
                regime_oracle_passes[reg] += 1

        winner_label = verdict["winner"]
        winner_regime = l2r[winner_label]
        regime_wins[winner_regime] += 1
        ranking_regimes = [l2r[lbl] for lbl in verdict["ranking"]]

        per_family.append(
            {
                "family_id": fid,
                "title": meta["title"],
                "domain": meta["domain"],
                "blind_assignment": l2r,
                "winner_regime": winner_regime,
                "ranking_regimes": ranking_regimes,
                "judge_scores_by_regime": deanonymized_scores,
                "oracle_by_regime": meta["oracle_by_regime"],
                "manifold_telemetry": meta["manifold_telemetry"],
                "judge_rationale": verdict["rationale"],
            }
        )

    n_fam = max(1, len(per_family))
    aggregate = {}
    for r in REGIMES:
        aggregate[r] = {
            "mean_blind_judge_score": round(sum(regime_judge_totals[r]) / n_fam, 2),
            "mean_exogenous_oracle_pct": round(sum(regime_oracle_totals[r]) / n_fam, 2),
            "exogenous_full_pass_families": f"{regime_oracle_passes[r]}/{n_fam}",
            "blind_judge_first_place_wins": regime_wins[r],
        }

    report = {
        "schema": "skillcompose.7family_results.v1",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "execution_backend": execution_backend,
        "judge_model": judge_model_label,
        "n_families": len(per_family),
        "solver_calls_per_task_per_regime": 1,
        "total_solver_calls": len(per_family) * len(REGIMES),
        "aggregate_by_regime": aggregate,
        "families": per_family,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Render clean Markdown report
    lines = [
        "# 7-Family Empirical Benchmark: Concatenation ($\\bigwedge_i s_i$) vs Union ($\\bigcup_i s_i$) vs Lawvere–Amari Manifold ($\\mathfrak{G}_{\\mathcal{M}}$)",
        "",
        f"- **Solver Invocation Protocol:** `1` isolated fresh agent call per `(task_family, regime)` (`7 × 3 = 21` solver runs, identical 4 upstream skills per family)",
        f"- **Execution Backend:** `{execution_backend}`",
        f"- **Blind Judge Protocol:** `{judge_model_label}` over shuffled anonymous labels (`Candidate_Alpha`, `Candidate_Beta`, `Candidate_Gamma`) with `.agents/` stripped",
        "",
        "## Aggregate Scorecard Across All 7 Task Families",
        "",
        "| Composition Regime | Mean Blind Judge Score (`/100`) | Mean Exogenous Oracle Score (`%`) | Exogenous Full-Pass Families | Blind Judge 1st-Place Wins |",
        "|---|---|---|---|---|",
    ]
    labels_pretty = {
        "concat": "`concat` (Prompt Concatenation $\\bigwedge_i s_i$)",
        "union": "`union` (Skill Union Router $\\bigcup_i s_i$)",
        "manifold": "**`manifold` (Lawvere–Amari Manifold $\\mathfrak{G}_{\\mathcal{M}}$)**",
    }
    for r in REGIMES:
        ag = aggregate[r]
        lines.append(
            f"| {labels_pretty[r]} | `{ag['mean_blind_judge_score']:.2f}` | `{ag['mean_exogenous_oracle_pct']:.2f}%` | `{ag['exogenous_full_pass_families']}` | `{ag['blind_judge_first_place_wins']}/{len(per_family)}` |"
        )

    lines += [
        "",
        "## Per-Family Breakdown",
        "",
        "| Family | Domain | `concat` (Judge / Oracle) | `union` (Judge / Oracle) | `manifold` (Judge / Oracle) | Blind Judge Winner |",
        "|---|---|---|---|---|---|",
    ]
    for f in per_family:
        js = f["judge_scores_by_regime"]
        ob = f["oracle_by_regime"]
        c_s = f"`{js['concat']['overall_score']:.1f}` / `{ob['concat']['score']*100:.0f}%`"
        u_s = f"`{js['union']['overall_score']:.1f}` / `{ob['union']['score']*100:.0f}%`"
        m_s = f"**`{js['manifold']['overall_score']:.1f}` / `{ob['manifold']['score']*100:.0f}%`**"
        lines.append(
            f"| `{f['family_id']}` | `{f['domain']}` | {c_s} | {u_s} | {m_s} | **`{f['winner_regime']}`** |"
        )

    lines += ["", "## Detailed Blind Judge Rationales", ""]
    for f in per_family:
        lines += [
            f"### `{f['family_id']}` — {f['title']}",
            f"- **Blind Mapping:** `{json.dumps(f['blind_assignment'])}`",
            f"- **Ranking:** `{' > '.join(f['ranking_regimes'])}`",
            f"- **Judge Rationale:** {f['judge_rationale']}",
            "",
        ]

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def invoke_agy_cli(
    agy_bin: str,
    prompt: str,
    cwd: Path,
    *,
    model: str | None = None,
    cmd_template: str | None = None,
    timeout_sec: int = 420,
) -> tuple[int, str]:
    """Invoke `agy` once in `cwd`. Supports custom `AGY_CMD_TEMPLATE` or standard `agy` flags."""
    prompt_file = cwd / ".agy_prompt_input.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    try:
        if cmd_template:
            # Template placeholders: {agy}, {model_flag}, {prompt_file}, {cwd}
            mflag = f"--model {model}" if model else ""
            cmd_str = cmd_template.format(
                agy=agy_bin,
                model=model or "",
                model_flag=mflag,
                prompt_file=str(prompt_file),
                cwd=str(cwd),
            )
            proc = subprocess.run(cmd_str, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
            return proc.returncode, (proc.stdout or "") + (proc.stderr or "")

        cmd = [agy_bin]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["-p", prompt])
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    finally:
        if prompt_file.exists():
            prompt_file.unlink()


def cmd_run(args: argparse.Namespace) -> int:
    agy_path = shutil.which(args.agy_bin)
    if not agy_path and not args.cmd_template:
        sys.stderr.write(
            f"ERROR: `{args.agy_bin}` binary not found on PATH.\n"
            f"Run this script on a host with `agy` installed, or pass `--agy-bin /path/to/agy` "
            f"or `--cmd-template '... {{prompt_file}} ...'`.\n"
        )
        return 2

    suite_dir = args.work_dir / "suite"
    runs_dir = args.work_dir / "runs"
    packets_dir = args.work_dir / "judge_packets"
    verdicts_dir = args.work_dir / "verdicts"
    verdicts_dir.mkdir(parents=True, exist_ok=True)

    manifest = materialize_all(suite_dir)
    prepare_isolated_run_tree(suite_dir, runs_dir)

    # 1. Execute `agy` ONCE per task family per regime (7 x 3 = 21 calls)
    for fam in manifest["families"]:
        fid = fam["id"]
        sname = fam["skill_name"]
        task_prompt = Path(fam["prompt_file"]).read_text(encoding="utf-8")
        for reg in REGIMES:
            ws = runs_dir / fid / reg
            solver_prompt = (
                f"Read `.agents/skills/{sname}/SKILL.md` first and follow its workflow faithfully.\n\n"
                f"{task_prompt}"
            )
            print(f"[agy solver] family={fid} regime={reg} ...", flush=True)
            t0 = time.time()
            code, out = invoke_agy_cli(
                args.agy_bin,
                solver_prompt,
                ws,
                model=args.solver_model or None,
                cmd_template=args.cmd_template or os.environ.get("AGY_CMD_TEMPLATE"),
                timeout_sec=args.timeout,
            )
            print(f"  -> exit={code} in {time.time() - t0:.1f}s", flush=True)

    # 2. Build blind judge packets (runs deterministic exogenous oracles + strips `.agents/`)
    build_blind_judge_packets(suite_dir, runs_dir, packets_dir)

    # 3. Call `agy` with Sonnet 5.5 as blind judge ONCE per family (7 calls)
    judge_tmp = args.work_dir / "judge_scratch"
    judge_tmp.mkdir(parents=True, exist_ok=True)
    for fam in manifest["families"]:
        fid = fam["id"]
        j_prompt = (packets_dir / f"{fid}_judge_prompt.md").read_text(encoding="utf-8")
        print(f"[agy judge ({args.judge_model})] family={fid} ...", flush=True)
        code, out = invoke_agy_cli(
            args.agy_bin,
            j_prompt,
            judge_tmp,
            model=args.judge_model,
            cmd_template=args.judge_cmd_template or args.cmd_template or os.environ.get("AGY_JUDGE_CMD_TEMPLATE"),
            timeout_sec=args.timeout,
        )
        verdict_obj = _extract_json_obj(out)
        (verdicts_dir / f"{fid}_verdict.json").write_text(
            json.dumps(verdict_obj, indent=2) + "\n", encoding="utf-8"
        )

    rep = finalize_benchmark_report(
        packets_dir,
        verdicts_dir,
        args.out_json,
        args.out_md,
        execution_backend=f"{args.agy_bin} CLI (1 call / task / regime)",
        judge_model_label=args.judge_model,
    )
    print(json.dumps(rep["aggregate_by_regime"], indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="subcmd", required=True)

    r = sub.add_parser("run", help="Run full 21-solver + 7-Sonnet-5.5-judge benchmark via `agy` CLI")
    r.add_argument("--agy-bin", default=os.environ.get("AGY_BIN", "agy"))
    r.add_argument("--solver-model", default=os.environ.get("AGY_SOLVER_MODEL", ""))
    r.add_argument("--judge-model", default=os.environ.get("AGY_JUDGE_MODEL", "claude-sonnet-5-5"))
    r.add_argument("--cmd-template", default=None, help="Optional shell template, e.g. '{agy} {model_flag} -p \"$(cat {prompt_file})\"'")
    r.add_argument("--judge-cmd-template", default=None)
    r.add_argument("--work-dir", type=Path, default=Path("/tmp/skillcompose_agy_7family"))
    r.add_argument("--timeout", type=int, default=420)
    r.add_argument("--out-json", type=Path, default=HERE / "results" / "agy_sonnet55_report.json")
    r.add_argument("--out-md", type=Path, default=HERE / "RESULTS_AGY_SONNET55.md")

    pj = sub.add_parser("prepare-judge", help="Evaluate exogenous oracles and build blind judge packets")
    pj.add_argument("--suite-dir", type=Path, required=True)
    pj.add_argument("--runs-dir", type=Path, required=True)
    pj.add_argument("--packets-dir", type=Path, required=True)

    fn = sub.add_parser("finalize", help="De-anonymize blind judge JSON verdicts into summary report")
    fn.add_argument("--packets-dir", type=Path, required=True)
    fn.add_argument("--verdicts-dir", type=Path, required=True)
    fn.add_argument("--backend", default="Antigravity isolated subagents (1 call / task / regime)")
    fn.add_argument("--judge-label", default="Blind Subagent Judge (Antigravity VM)")
    fn.add_argument("--out-json", type=Path, default=HERE / "results" / "vm_live_report.json")
    fn.add_argument("--out-md", type=Path, default=HERE / "RESULTS.md")

    args = ap.parse_args()
    if args.subcmd == "run":
        return cmd_run(args)
    if args.subcmd == "prepare-judge":
        res = build_blind_judge_packets(args.suite_dir, args.runs_dir, args.packets_dir)
        print(json.dumps(res, indent=2))
        return 0
    rep = finalize_benchmark_report(
        args.packets_dir,
        args.verdicts_dir,
        args.out_json,
        args.out_md,
        execution_backend=args.backend,
        judge_model_label=args.judge_label,
    )
    print(json.dumps(rep["aggregate_by_regime"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
