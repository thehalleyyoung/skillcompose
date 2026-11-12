#!/usr/bin/env python3
"""License gate — allow fork/republish only for permissive licenses."""
from __future__ import annotations

import argparse
import json
import sys

ALLOW = {
    "mit",
    "apache-2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "isc",
    "0bsd",
    "unlicense",
    "cc0-1.0",
    "mpl-2.0",
}
DENY = {"gpl-3.0", "gpl-2.0", "agpl-3.0", "lgpl-3.0", "lgpl-2.1", "sspl-1.0", "busl-1.1", "proprietary", "other"}


def normalize(lic: str | None) -> str:
    if not lic:
        return ""
    return lic.strip().lower().replace(" ", "-")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--license", default=None)
    ap.add_argument("--chosen", default=None, help="Path to chosen.json")
    ap.add_argument("--allow-unknown", action="store_true", help="PASS with warning if license missing")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    lic = args.license
    if args.chosen:
        data = json.loads(open(args.chosen, encoding="utf-8").read())
        lic = data.get("license") or lic

    key = normalize(lic)
    reasons = []
    decision = "PASS"
    if not key:
        if args.allow_unknown:
            decision = "PASS"
            reasons.append("license unknown — proceed with caution; verify UPSTREAM.md attribution")
        else:
            decision = "FAIL"
            reasons.append("license missing — enrich via enrich_github.py or set manually")
    elif key in DENY or key.startswith("gpl") or key.startswith("agpl"):
        decision = "FAIL"
        reasons.append(f"license {key!r} forbids or complicates republish — pick another candidate")
    elif key in ALLOW:
        decision = "PASS"
    else:
        if args.allow_unknown:
            decision = "PASS"
            reasons.append(f"license {key!r} not in allowlist — manual review required")
        else:
            decision = "FAIL"
            reasons.append(f"license {key!r} not in allowlist {sorted(ALLOW)}")

    out = {"decision": decision, "license": key or None, "reasons": reasons}
    print(json.dumps(out, indent=2) if args.json else out)
    return 0 if decision == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
