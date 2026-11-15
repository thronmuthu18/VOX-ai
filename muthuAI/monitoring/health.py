"""
MuthuAI Phase 6 — monitoring/health.py

System Health Check Component.
Checks Gemini API key, microphone device, internet connectivity, and disk storage.
"""

from __future__ import annotations
import urllib.request
from pathlib import Path
from config.settings import GEMINI_API_KEY
from utils.logger import get_logger

log = get_logger("muthuai.monitoring.health")


class HealthChecker:
    """
    Performs startup and runtime health diagnostics.
    """

    def check_all(self) -> dict:
        """
        Run full diagnostic check.
        Returns dict: {"healthy": bool, "checks": dict}
        """
        api_ok = self.check_api_key()
        net_ok = self.check_internet()
        storage_ok = self.check_storage()
        mic_ok = self.check_microphone()

        all_ok = api_ok and net_ok and storage_ok and mic_ok

        log.info("System Health Check: healthy=%s (API=%s, Internet=%s, Storage=%s, Mic=%s)",
                 all_ok, api_ok, net_ok, storage_ok, mic_ok)

        return {
            "healthy": all_ok,
            "checks": {
                "gemini_api_key": api_ok,
                "internet_connection": net_ok,
                "disk_storage": storage_ok,
                "microphone_device": mic_ok
            }
        }

    def check_api_key(self) -> bool:
        return bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")

    def check_internet(self) -> bool:
        try:
            urllib.request.urlopen("https://www.google.com", timeout=3)
            return True
        except Exception:
            return False

    def check_storage(self) -> bool:
        try:
            data_dir = Path("data").resolve()
            data_dir.mkdir(parents=True, exist_ok=True)
            test_file = data_dir / ".health_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
            return True
        except Exception:
            return False

    def check_microphone(self) -> bool:
        try:
            import speech_recognition as sr
            mics = sr.Microphone.list_microphone_names()
            return len(mics) > 0
        except Exception:
            return False
