"""
VOX AI — launcher.py

Production Application Launcher for Windows Desktop AI Personal Agent.
Serves as the main entry point for standalone execution or PyInstaller EXE packaging.
"""

from __future__ import annotations
import sys
import os
import warnings
from pathlib import Path

# Ignore unnecessary deprecation/user warnings for clean user interface
warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def launch() -> None:
    print("=" * 60)
    print("   VOX AI — Windows AI Personal Agent v1.0")
    print("   VOX AI PERSONAL ASSISTANT")
    print("=" * 60)

    # 1. Run system diagnostics
    from diagnostics import run_diagnostics
    print("\nRunning pre-flight system diagnostics...")
    healthy = run_diagnostics()

    if not healthy:
        print("\n⚠️ System diagnostics identified configuration warnings.")
        print("Starting VOX AI application anyway...\n")

    # 2. Launch main entry point
    from app.main import main
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as exc:
        print(f"\n❌ Fatal Application Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    launch()
