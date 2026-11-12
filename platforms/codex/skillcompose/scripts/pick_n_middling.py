#!/usr/bin/env python3
"""Legacy alias for pick_n_eligible.py (adoption floor; highly popular allowed)."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.argv[0] = str(Path(__file__).with_name("pick_n_eligible.py"))
    runpy.run_path(str(Path(__file__).with_name("pick_n_eligible.py")), run_name="__main__")
