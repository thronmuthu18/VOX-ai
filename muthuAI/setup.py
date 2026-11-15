"""
MuthuAI — setup.py
One-click setup script: checks environment, installs dependencies,
installs Playwright, and creates the .env file if missing.
Run: python setup.py
"""

import sys
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str], desc: str) -> bool:
    print(f"\n⚙️  {desc}…")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"  ❌ Failed: {' '.join(cmd)}")
        return False
    print(f"  ✓ Done.")
    return True


def check_python_version() -> None:
    if sys.version_info < (3, 10):
        print(f"❌ Python 3.10+ required. Current: {sys.version}")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]}")


def install_dependencies() -> None:
    req = ROOT / "requirements.txt"
    if not req.exists():
        print("❌ requirements.txt not found.")
        sys.exit(1)
    run([sys.executable, "-m", "pip", "install", "-r", str(req)], "Installing Python packages")


def install_playwright() -> None:
    run([sys.executable, "-m", "playwright", "install", "chromium"], "Installing Playwright Chromium")


def create_env_file() -> None:
    env_file = ROOT / ".env"
    example_file = ROOT / ".env.example"
    if env_file.exists():
        print("✓ .env already exists.")
        return
    if example_file.exists():
        env_file.write_text(example_file.read_text(encoding="utf-8"), encoding="utf-8")
        print("✓ .env created from .env.example")
        print("\n⚠️  IMPORTANT: Open .env and set your GEMINI_API_KEY before running!")
    else:
        print("⚠️  .env.example not found — creating minimal .env")
        env_file.write_text("GEMINI_API_KEY=your_gemini_api_key_here\n", encoding="utf-8")


def create_data_dirs() -> None:
    dirs = [
        ROOT / "data" / "memory",
        ROOT / "data" / "documents",
        ROOT / "data" / "chroma_db",
        ROOT / "data" / "cache" / "tts",
        ROOT / "data" / "logs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("✓ Data directories created.")


def print_summary() -> None:
    print("""
╔══════════════════════════════════════════════════════════╗
║              MuthuAI Setup Complete!                     ║
╚══════════════════════════════════════════════════════════╝

Next steps:
  1. Open .env and set: GEMINI_API_KEY=your_key_here
  2. (Optional) Copy documents to data/documents/ for RAG
  3. Run: python app/main.py
  4. Press Enter to speak — enjoy MuthuAI!

For help: see README.md
""")


if __name__ == "__main__":
    print("\n🚀 MuthuAI Setup Script\n" + "=" * 40)
    check_python_version()
    create_data_dirs()
    install_dependencies()
    install_playwright()
    create_env_file()
    print_summary()
