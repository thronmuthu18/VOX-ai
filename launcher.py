"""
VOX AI / CHAMP — Root Launcher Relay
Routes execution into muthuAI/launcher.py with appropriate working directory and sys.path.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

# Add muthuAI directory to sys.path and switch working directory
_MUTHU_AI_DIR = Path(__file__).resolve().parent / "muthuAI"
if str(_MUTHU_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_MUTHU_AI_DIR))

try:
    os.chdir(str(_MUTHU_AI_DIR))
except Exception:
    pass

if __name__ == "__main__":
    from launcher import launch
    launch()
