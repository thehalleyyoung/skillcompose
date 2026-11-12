#!/usr/bin/env python3
"""Legacy wrapper: check_themes.py → check_phases.py (T1–T5 removed)."""
from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "check_phases.py"), run_name="__main__")
