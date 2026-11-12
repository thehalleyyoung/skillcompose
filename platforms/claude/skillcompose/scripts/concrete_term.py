#!/usr/bin/env python3
"""The concrete term of a package, and the theory's obligations on it (theory.md §4.2).

compose_skills.py proves its guarantees for the wiring graph it emits: abstract member and subskill
nodes. A forge then rewrites SKILL.md and adds scripts for fifty rounds, and the graph keeps passing
because nothing in it names a file. This script reads the term the package actually runs:

  components  every script SKILL.md invokes (`python3 …/X.py`, `bash …/X.sh`), in document order. A
              script that runs other package scripts (a runner) is expanded into them, depth ≤ 3.
  interface   ι(f) = (A_f, W_f, E_f): argparse options (compose_skills.script_signature), the write
              footprint from the AST, and the literal exit codes.
  roles       projector (named in the atlas, or project_manifold.py), gate (verify_dominator_gate.py),
              mutator (writes outside a declared report), observer (everything else). A package can
              pin roles in references/term_roles.json: {"scripts/x.py": "gate"}.
  graph       the documented protocol as a transition system: an edge for each adjacency in the
              document, and a repeat of a script returns to its node (the μX loop). Under T2 the host
              admits DONE only right after a passing gate, so DONE is reached only from gates.

Obligations (each failure adds 1 to the contract potential Φ_c):
  closure        every invoked script exists in the carrier                    Prop. 3.2(2)
  signature      every flag an invocation passes is declared; declared required flags are passed  T-Script
  verdicts       the gate can fail (a nonzero exit); the projector can abstain (exit 2)  §4.1 verdict maps
  gate_readonly  the gate writes nothing outside its declared report            φ_ro
  gated          every mutator can reach a read-only gate                      φ_gate
  projected      the projector pre-dominates every mutator                     φ_abs
  verify_graph   wiring_compiler.verify_graph on the concrete graph (type safety, DPI grounding, …)
  carrier        every member script the atlas carried (manifold_atlas.json `carrier`) is still there   Prop. 3.2(2)
  interface      every argument of the composed interface A_M(D) is still named in SKILL.md      Cor. 3.1
  artifact       references/concrete_term.json matches this extraction (only with --require-artifact)

Scripts in scripts/ that nothing reaches are reported as dead carrier (Prop. 3.2(3)); they add no Φ.

  concrete_term.py check --package DIR [--require-artifact] [--json]   exit 0 when Φ_c = 0, else 2
  concrete_term.py write --package DIR                                 refresh references/concrete_term.json
  concrete_term.py ratchet --repo DIR [--base REV] [--head REV] [--zero] [--require-artifact] [--json]
        Φ_c and the package Lyapunov potential Φ at base and head; exit 2 if either rose, or with --zero
        if Φ_c at head is not 0
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose_skills import script_signature  # noqa: E402
from wiring_compiler import verify_graph  # noqa: E402

ARTIFACT = "references/concrete_term.json"
INVOKE = re.compile(r"\b(?:python3?|bash|sh)\s+[\"']?([^\s`'\"|;&<>()]+?\.(?:py|sh))\b[\"']?((?:[^\n`|;&]|\\\n)*)")
PLACEHOLDER = re.compile(r"<[^>]*>|\.\.\.|…|\$\{?\w+")
WRITE_ATTRS = {"write_text", "write_bytes", "mkdir", "touch", "unlink", "rmdir", "rename", "replace", "symlink_to"}
WRITE_FUNCS = {("shutil", n) for n in ("copy", "copy2", "copyfile", "copytree", "move", "rmtree")} | {
    ("os", n) for n in ("remove", "unlink", "rename", "replace", "makedirs", "mkdir", "rmdir")}
REPORT_HINT = re.compile(r"\b(args\.(out|report|output|json_out)\w*|out_?path|report_?path|report|out)\b")


def package_scripts(pkg: Path) -> list[Path]:
    return sorted(p for p in (pkg / "scripts").rglob("*") if p.suffix in (".py", ".sh") and p.is_file()
                  and "__pycache__" not in p.parts) if (pkg / "scripts").is_dir() else []


def resolve(pkg: Path, token: str, scripts: list[Path]) -> Path | None:
    tok = token.replace("\\", "/")
    tail = tok[tok.rfind("scripts/") + len("scripts/"):] if "scripts/" in tok else tok.split("/")[-1]
    exact = pkg / "scripts" / tail
    if exact.is_file():
        return exact
    hits = [p for p in scripts if p.as_posix().endswith("/" + tail)]
    return hits[0] if len(hits) == 1 else None


def writes(path: Path) -> dict:
    """Write calls in a Python script, split into declared report writes and other writes."""
    if path.suffix != ".py":
        text = path.read_text(encoding="utf-8", errors="replace")
        n = len(re.findall(r"(?<![<>])>{1,2}\s*[\"$\w/]|\b(?:rm|mv|cp|mkdir|tee)\b", text))
        return {"report": 0, "other": n, "sites": [], "lines": []}
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"report": 0, "other": 0, "sites": ["syntax_error"], "lines": []}
    report = other = 0
    sites = []
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        hit = False
        if isinstance(fn, ast.Attribute):
            base = fn.value.id if isinstance(fn.value, ast.Name) else ""
            hit = fn.attr in WRITE_ATTRS or (base, fn.attr) in WRITE_FUNCS or (base == "json" and fn.attr == "dump")
            if fn.attr in ("replace", "rename") and base not in ("os", "shutil"):
                hit = len(node.args) == 1  # Path.replace(target); str.replace(old, new) takes two
        elif isinstance(fn, ast.Name) and fn.id == "open":
            mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
            hit = isinstance(mode, ast.Constant) and isinstance(mode.value, str) and bool(set(mode.value) & set("wax+"))
        if not hit:
            continue
        seg = ast.get_source_segment(text, node) or ""
        if REPORT_HINT.search(seg):
            report += 1
        else:
            other += 1
            sites.append(f"{path.name}:{node.lineno}")
            lines.append(node.lineno)
    return {"report": report, "other": other, "sites": sites[:5], "lines": sorted(lines)}


def callees(path: Path, pkg: Path, scripts: list[Path]) -> list[tuple[int, Path]]:
    """Package scripts a script runs, with the line where each is first used.

    A literal bound to a module-level name (PROJ = HERE / "project_manifold.py") is used where the name
    is next referenced; otherwise where the literal appears.
    """
    if path.suffix != ".py":
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    src = text.splitlines()
    found: list[tuple[int, Path]] = []
    for s in scripts:
        if s == path:
            continue
        m = re.search(r"[\"'/]" + re.escape(s.name) + r"[\"'\s]", text)
        if not m:
            continue
        line = text.count("\n", 0, m.start()) + 1
        bound = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*=", src[line - 1])
        if bound:
            name = bound.group(1)
            use = next((i + 1 for i in range(line, len(src)) if re.search(rf"\b{name}\b", src[i])), line)
            line = use
        found.append((line, s))
    return sorted(found, key=lambda x: x[0])


def roles_for(pkg: Path) -> dict[str, str]:
    try:
        r = json.loads((pkg / "references" / "term_roles.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in r.items() if isinstance(k, str) and v in ("projector", "gate", "mutator", "observer")} \
        if isinstance(r, dict) else {}


def role(rel: str, w: dict, sig: dict, pinned: dict[str, str]) -> str:
    if rel in pinned:
        return pinned[rel]
    name = rel.rsplit("/", 1)[-1]
    if name == "project_manifold.py":
        return "projector"
    if name == "verify_dominator_gate.py":
        return "gate"
    return "mutator" if w["other"] else "observer"


def flags_in(args: str) -> list[str]:
    return [f.split("=")[0] for f in re.findall(r"(?<![\w-])(--?[A-Za-z][\w-]*(?:=\S*)?)", args)]


def extract(pkg: Path) -> dict:
    pkg = pkg.resolve()
    skill = pkg / "SKILL.md"
    text = skill.read_text(encoding="utf-8", errors="replace") if skill.is_file() else ""
    scripts = package_scripts(pkg)
    pinned = roles_for(pkg)
    comps: dict[str, dict] = {}
    order: list[str] = []
    missing: list[str] = []
    calls: list[dict] = []

    def component(p: Path) -> str:
        rel = p.relative_to(pkg).as_posix()
        if rel not in comps:
            sig = script_signature(p)
            w = writes(p)
            comps[rel] = {"path": rel, "role": role(rel, w, sig, pinned), "options": sorted(set(sig["options"])),
                          "required": sorted(set(sig["required_options"])), "exit_codes": sig["exit_codes"],
                          "extraction": sig["extraction"], "writes": w, "runs": []}
            runs = callees(p, pkg, scripts)
            comps[rel]["runs"] = [c.relative_to(pkg).as_posix() for _, c in runs]
            comps[rel]["run_lines"] = [ln for ln, _ in runs]
        return rel

    def visit(p: Path, depth: int) -> None:
        rel = component(p)
        c = comps[rel]
        if not c["runs"] or depth >= 3:
            order.append(rel)
            return
        # a runner is the interleaving of the scripts it runs and its own writes, in source order
        if c["role"] == "mutator":
            c["role"] = "runner"
        events = [(ln, "run", r) for ln, r in zip(c["run_lines"], c["runs"])] + \
                 [(ln, "write", f"{rel}@{ln}") for ln in c["writes"]["lines"]]
        for ln, kind, ref in sorted(events):
            if kind == "run":
                visit(pkg / ref, depth + 1)
            else:
                comps.setdefault(ref, {"path": ref, "role": "mutator", "options": [], "required": [],
                                       "exit_codes": [], "extraction": "write_site",
                                       "writes": {"report": 0, "other": 1, "sites": [ref], "lines": [ln]},
                                       "runs": [], "run_lines": []})
                order.append(ref)

    for m in INVOKE.finditer(text):
        token, args = m.group(1), m.group(2).replace("\\\n", " ")
        p = resolve(pkg, token, scripts)
        line = text.count("\n", 0, m.start()) + 1
        if p is None:
            if "scripts/" in token or token.startswith("$"):
                missing.append(f"SKILL.md:{line} {token}")
            continue
        calls.append({"line": line, "script": p.relative_to(pkg).as_posix(), "args": args.strip()[:200]})
        visit(p, 0)

    reached = {r for r in comps if "@" not in r}
    for rel in list(reached):
        p = pkg / rel
        if p.suffix == ".py":
            src = p.read_text(encoding="utf-8", errors="replace")
            for s in scripts:
                if re.search(rf"^\s*(from|import)\s+{re.escape(s.stem)}\b", src, re.M):
                    reached.add(s.relative_to(pkg).as_posix())
    dead = [s.relative_to(pkg).as_posix() for s in scripts
            if s.relative_to(pkg).as_posix() not in reached and "/members/" not in s.as_posix()]
    return {"schema": "skillcompose.concrete_term.v1", "components": comps, "order": order, "calls": calls,
            "missing": missing, "dead_carrier": dead}


def graph_of(term: dict) -> dict:
    """The documented protocol as a trace: one node per step, in order; DONE only after a gate (T2)."""
    cls = {"projector": "manifold_projector", "gate": "oracle_gate", "mutator": "mutator", "observer": "exec_observation"}
    nodes = [{"id": "ENTRY", "operator_class": "guard_router", "reads": [], "writes": [], "exogenous_oracle": True}]
    edges, prev = [], "ENTRY"
    for i, rel in enumerate(term["order"]):
        c = term["components"][rel]
        nid = f"{i}:{rel}"
        nodes.append({"id": nid, "operator_class": cls[c["role"]], "reads": [],
                      "writes": [f"{rel}:writes"] if c["role"] == "mutator" else [],
                      "exogenous_oracle": c["role"] != "mutator"})
        edges.append({"from": prev, "to": nid, "op": "sequential_pipe"})
        if c["role"] == "gate":
            edges.append({"from": nid, "to": "DONE", "op": "dominator_join"})
        prev = nid
    nodes.append({"id": "DONE", "operator_class": "terminal", "reads": [], "writes": [], "exogenous_oracle": True})
    return {"package_name": "concrete", "nodes": nodes, "edges": edges, "parallel_groups": []}


def obligations(pkg: Path, term: dict, require_artifact: bool = False) -> list[str]:
    errs = [f"closure: {m} is invoked but not in the package" for m in term["missing"]]
    comps = term["components"]
    for call in term["calls"]:
        c = comps[call["script"]]
        if c["extraction"] != "python_ast" or not c["options"]:
            continue
        used = set(flags_in(call["args"]))
        extra = sorted(f for f in used - set(c["options"]) if f not in ("-h", "--help"))
        if extra:
            errs.append(f"signature: SKILL.md:{call['line']} passes {', '.join(extra)} to {call['script']}, "
                        f"which declares {', '.join(c['options'])}")
        if not PLACEHOLDER.search(call["args"]) and call["args"] and not call["args"].rstrip().endswith("\\"):
            lacking = sorted(set(c["required"]) - used)
            if lacking:
                errs.append(f"signature: SKILL.md:{call['line']} omits required {', '.join(lacking)} "
                            f"of {call['script']}")
    gates = [r for r, c in comps.items() if c["role"] == "gate"]
    projs = [r for r, c in comps.items() if c["role"] == "projector"]
    muts = [r for r, c in comps.items() if c["role"] == "mutator"]
    if term["order"] and not gates:
        errs.append("verdicts: the protocol runs scripts but never a gate, so DONE is unreachable under T2")
    for g in gates:
        if comps[g]["extraction"] == "python_ast" and not any(x != 0 for x in comps[g]["exit_codes"]):
            errs.append(f"verdicts: gate {g} has no nonzero exit, so it can never fail")
        if comps[g]["writes"]["other"]:
            errs.append(f"gate_readonly: gate {g} writes outside a report ({', '.join(comps[g]['writes']['sites'])})")
    for p in projs:
        if comps[p]["extraction"] == "python_ast" and 2 not in comps[p]["exit_codes"]:
            errs.append(f"verdicts: projector {p} cannot abstain (no exit 2)")
    g = graph_of(term)
    steps = [(i, comps[r]["role"], r) for i, r in enumerate(term["order"])]
    first_proj = next((i for i, ro, _ in steps if ro == "projector"), None)
    last_gate = max((i for i, ro, _ in steps if ro == "gate"), default=-1)
    flagged: set[tuple[str, str]] = set()
    for i, ro, r in steps:
        if ro != "mutator":
            continue
        if i > last_gate and ("gated", r) not in flagged:
            flagged.add(("gated", r))
            errs.append(f"gated: mutator {r} ({', '.join(comps[r]['writes']['sites'][:2])}) runs after the last gate, "
                        "so its write reaches DONE unchecked (φ_gate)")
        if (first_proj is None or i < first_proj) and ("projected", r) not in flagged:
            flagged.add(("projected", r))
            errs.append(f"projected: mutator {r} writes before any projector runs (φ_abs: no write before "
                        f"projection{'' if projs else '; the protocol has no projector'})")
    if term["order"]:
        v = verify_graph(g)
        for k in ("type_safety", "dpi_exogenous_grounding"):
            if not v["checks"].get(k, True):
                errs.append(f"verify_graph: {k} fails on the concrete graph ({'; '.join(v['reasons'])[:200]})")
    try:
        atlas = json.loads((pkg / "references" / "manifold_atlas.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        atlas = {}
    carried = atlas.get("carrier") if isinstance(atlas, dict) else None
    if isinstance(carried, dict):
        for member, files in carried.items():
            for f in files if isinstance(files, list) else []:
                dest = f.get("dest") if isinstance(f, dict) else None
                if isinstance(dest, str) and dest.startswith("scripts/") and not (pkg / dest).is_file():
                    errs.append(f"carrier: {member}'s channel {dest} was removed, so the package no longer "
                                "realizes that member's kernel")
    iface = atlas.get("argument_interface") if isinstance(atlas, dict) else None
    if isinstance(iface, dict):
        text = (pkg / "SKILL.md").read_text(encoding="utf-8", errors="replace") if (pkg / "SKILL.md").is_file() else ""
        for arg in sorted({a for k in ("take", "able") for a in iface.get(k) or [] if isinstance(a, str)}):
            if arg.lstrip("-") not in text:
                errs.append(f"interface: SKILL.md no longer names the composed argument {arg}")
    if require_artifact:
        try:
            saved = json.loads((pkg / ARTIFACT).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = None
        if not isinstance(saved, dict) or saved.get("components") != term["components"] or saved.get("order") != term["order"]:
            errs.append(f"artifact: {ARTIFACT} does not describe the package; run concrete_term.py write")
    return errs


def check(pkg: Path, require_artifact: bool = False) -> dict:
    term = extract(pkg)
    errs = obligations(pkg, term, require_artifact)
    roles: dict[str, list[str]] = {}
    for r, c in term["components"].items():
        roles.setdefault(c["role"], []).append(r)
    return {"decision": "PASS" if not errs else "FAIL", "phi": len(errs), "obligations": errs, "roles": roles,
            "order": term["order"], "dead_carrier": term["dead_carrier"]}


def lyapunov(pkg: Path) -> dict:
    """The vector Lyapunov debt Φ(pkg) by component (information_gain.package_telemetry)."""
    from information_gain import package_telemetry

    return package_telemetry(pkg)["lyapunov"]


def snapshot(repo: Path, rev: str, into: Path) -> Path:
    data = subprocess.run(["git", "-C", str(repo), "archive", rev], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=BytesIO(data)) as tf:
        tf.extractall(into)
    return into


def ratchet(repo: Path, base: str, head: str, zero: bool, require_artifact: bool = False) -> dict:
    with tempfile.TemporaryDirectory() as t:
        bdir = snapshot(repo, base, Path(t) / "base")
        hdir = snapshot(repo, head, Path(t) / "head") if head != "WORKTREE" else repo
        b, h = check(bdir), check(hdir)
        art = [o for o in check(hdir, True)["obligations"] if o.startswith("artifact:")] if require_artifact else []
        lb, lh = lyapunov(bdir), lyapunov(hdir)
    reasons = []
    # Vector descent: a weighted sum lets a paid downstream debt (evals, proof) hide an upstream
    # regression (the contract), so every component must be non-increasing.
    rose = {k: (lb["debts"].get(k, 0.0), v) for k, v in lh["debts"].items() if v > lb["debts"].get(k, 0.0) + 1e-9}
    if rose:
        reasons.append("ΔΦ > 0 in " + ", ".join(f"{k} {a:g}→{c:g}" for k, (a, c) in rose.items())
                       + " (vector Lyapunov debt must not rise in any component)")
    if h["phi"] > b["phi"]:
        new = [o for o in h["obligations"] if o not in b["obligations"]]
        reasons.append(f"ΔΦ_c = {h['phi'] - b['phi']} > 0: this change broke {'; '.join(new[:3])}")
    if zero and h["phi"]:
        reasons.append(f"Φ_c = {h['phi']} after the unify phase; it must be 0: {'; '.join(h['obligations'][:3])}")
    reasons.extend(art)
    return {"decision": "FAIL" if reasons else "PASS", "phi_before": b["phi"], "phi": h["phi"],
            "lyapunov_before": lb["phi_total"], "lyapunov": lh["phi_total"], "debts": lh["debts"],
            "reasons": reasons,
            "obligations": h["obligations"], "dead_carrier": h["dead_carrier"], "roles": h["roles"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--package", type=Path, required=True)
    c.add_argument("--require-artifact", action="store_true")
    w = sub.add_parser("write")
    w.add_argument("--package", type=Path, required=True)
    r = sub.add_parser("ratchet")
    r.add_argument("--repo", type=Path, required=True)
    r.add_argument("--base", default="HEAD~1")
    r.add_argument("--head", default="HEAD")
    r.add_argument("--zero", action="store_true", help="also require Φ_c = 0 at head")
    r.add_argument("--require-artifact", action="store_true", help="head must carry a current concrete_term.json")
    for p in (c, w, r):
        p.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.cmd == "write":
        term = extract(args.package)
        (args.package / ARTIFACT).parent.mkdir(parents=True, exist_ok=True)
        (args.package / ARTIFACT).write_text(json.dumps(term, indent=2) + "\n", encoding="utf-8")
        out = {"decision": "PASS", "wrote": str(args.package / ARTIFACT), "components": len(term["components"])}
    elif args.cmd == "check":
        out = check(args.package, args.require_artifact)
    else:
        out = ratchet(args.repo, args.base, args.head, args.zero, args.require_artifact)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
