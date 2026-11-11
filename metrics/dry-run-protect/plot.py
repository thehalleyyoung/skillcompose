#!/usr/bin/env python3
"""Plot history.jsonl → chart.svg (no external deps)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIST = ROOT / "history.jsonl"
OUT = ROOT / "chart.svg"


def load_points():
    if not HIST.is_file():
        return []
    pts = []
    for line in HIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        vals = row.get("values") or {}
        y = vals.get("structure_score")
        if y is None:
            # fallback: first numeric
            for v in vals.values():
                if isinstance(v, (int, float)):
                    y = float(v)
                    break
        if y is None:
            continue
        pts.append((row.get("at") or "", float(y)))
    return pts


def main() -> None:
    pts = load_points()
    w, h = 640, 240
    pad = 40
    if len(pts) < 1:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><text x="20" y="40">No data — run measure.py</text></svg>'
        OUT.write_text(svg, encoding="utf-8")
        print(json.dumps({"ok": True, "points": 0, "chart": str(OUT)}))
        return
    ys = [p[1] for p in pts]
    ymin, ymax = min(ys), max(ys)
    if ymin == ymax:
        ymin -= 1
        ymax += 1
    coords = []
    for i, (_t, y) in enumerate(pts):
        x = pad + (w - 2 * pad) * (i / max(1, len(pts) - 1))
        yy = h - pad - (h - 2 * pad) * ((y - ymin) / (ymax - ymin))
        coords.append(f"{x:.1f},{yy:.1f}")
    poly = " ".join(coords)
    title = 'dry_run --fast protect full stamp'
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="#fff"/>
  <text x="{pad}" y="24" font-family="sans-serif" font-size="14">{title}</text>
  <text x="{pad}" y="{h - 8}" font-family="sans-serif" font-size="10">n={len(pts)} · y={ymin:.2f}..{ymax:.2f}</text>
  <polyline fill="none" stroke="#0F766E" stroke-width="2" points="{poly}"/>
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(json.dumps({"ok": True, "points": len(pts), "chart": str(OUT)}))


if __name__ == "__main__":
    main()
