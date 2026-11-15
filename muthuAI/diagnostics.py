"""
VOX AI — diagnostics.py

System diagnostics tool to verify system readiness.
"""

from __future__ import annotations
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def check_python() -> bool:
    print("Checking Python version...")
    print(f"  Version: {sys.version}")
    if sys.version_info < (3, 10):
        print("  ❌ Python 3.10+ is required.")
        return False
    print("  ✓ Python version OK.")
    return True


def check_os() -> bool:
    print("Checking OS Platform...")
    print(f"  Platform: {sys.platform}")
    if sys.platform != "win32":
        print("  ⚠️ VOX AI is designed for Windows (win32). Some features may be disabled.")
        return True
    print("  ✓ OS Platform OK.")
    return True


def check_microphone() -> bool:
    print("Checking Microphone devices...")
    try:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        print(f"  Microphones found: {len(mics)}")
        for i, mic in enumerate(mics[:3]):
            print(f"    [{i}] {mic}")
        if len(mics) > 3:
            print(f"    ... and {len(mics) - 3} more")
        if not mics:
            print("  ❌ No microphones detected. Speech-to-text will fail.")
            return False
        print("  ✓ Microphone check OK.")
        return True
    except Exception as exc:
        print(f"  ❌ Microphone check error: {exc}")
        return False


def check_speaker() -> bool:
    print("Checking Audio Speaker (pygame mixer)...")
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
        print("  ✓ Speaker check OK.")
        return True
    except Exception as exc:
        print(f"  ❌ Speaker check error: {exc}")
        return False


def check_gemini() -> bool:
    print("Checking Gemini API configuration...")
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=True)
        key = os.getenv("GEMINI_API_KEY")
        if not key or key == "your_gemini_api_key_here":
            print("  ❌ GEMINI_API_KEY is not configured in .env file.")
            return False
        from google import genai
        client = genai.Client(api_key=key)
        print("  ✓ Gemini API Key configured.")
        return True
    except Exception as exc:
        print(f"  ❌ Gemini check error: {exc}")
        return False


def check_packages() -> bool:
    print("Checking critical packages...")
    packages = {
        "google.genai": "google-genai",
        "speech_recognition": "SpeechRecognition",
        "edge_tts": "edge-tts",
        "pygame": "pygame",
        "playwright": "playwright",
        "openpyxl": "openpyxl",
        "docx": "python-docx",
        "pptx": "python-pptx",
        "reportlab": "reportlab",
        "pandas": "pandas",
        "chromadb": "chromadb",
        "sentence_transformers": "sentence-transformers",
        "fitz": "pymupdf",
    }
    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {name} installed.")
        except ImportError:
            print(f"  ❌ {name} is NOT installed.")
            all_ok = False
    return all_ok


def check_directories() -> bool:
    print("Checking required workspace directories...")
    dirs = [
        ROOT / "data" / "memory",
        ROOT / "data" / "documents",
        ROOT / "data" / "chroma_db",
        ROOT / "data" / "logs",
        ROOT / "data" / "cache",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Directory verified: {d.relative_to(ROOT)}")
    return True


def run_diagnostics() -> bool:
    print("=" * 60)
    print("            VOX AI STARTUP DIAGNOSTICS")
    print("            VOX AI PERSONAL ASSISTANT")
    print("=" * 60)
    
    python_ok = check_python()
    os_ok = check_os()
    mic_ok = check_microphone()
    speaker_ok = check_speaker()
    gemini_ok = check_gemini()
    packages_ok = check_packages()
    dirs_ok = check_directories()

    overall = python_ok and os_ok and mic_ok and speaker_ok and gemini_ok and packages_ok and dirs_ok
    
    print("=" * 60)
    if overall:
        print("🎉 DIAGNOSTICS STATUS: ALL SYSTEM CHECKS PASSED!")
    else:
        print("⚠️  DIAGNOSTICS STATUS: SOME CHECKS FAILED.")
        print("   Please check the logs above to resolve warnings or errors.")
    print("=" * 60)
    return overall


if __name__ == "__main__":
    run_diagnostics()
