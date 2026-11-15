"""
MuthuAI — tools/media_tools.py
Media playback control and other media-related tools.
"""

import subprocess
from utils.helpers import ok, fail
from utils.logger import get_logger

log = get_logger(__name__)


def play_music(query: str = "", source: str = "youtube") -> dict:
    """
    Play music. Default source: YouTube search.
    Can be extended to support Spotify, VLC local files, etc.
    """
    if source.lower() == "youtube":
        from tools.browser_tools import play_youtube
        return play_youtube(query)
    elif source.lower() == "spotify":
        # Try to launch Spotify with search
        try:
            spotify_url = f"spotify:search:{query}"
            import webbrowser
            webbrowser.open(spotify_url)
            return ok(f"Opened Spotify search for: {query}")
        except Exception as exc:
            return fail(str(exc))
    else:
        from tools.browser_tools import play_youtube
        return play_youtube(query)


def set_brightness(level: int = 70) -> dict:
    """Set monitor brightness (0–100) using PowerShell WMI."""
    level = max(0, min(100, level))
    try:
        cmd = (
            f"(Get-WmiObject -Namespace root/WMI -Class "
            f"WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
        )
        subprocess.run(["powershell", "-Command", cmd], timeout=5, check=True)
        return ok(f"Brightness set to {level}%.")
    except Exception as exc:
        return fail(f"Brightness control failed: {exc}")


def next_track() -> dict:
    """Send next-track media key."""
    try:
        import pyautogui  # type: ignore
        pyautogui.press("nexttrack")
        return ok("Next track.")
    except Exception as exc:
        return fail(str(exc))


def previous_track() -> dict:
    """Send previous-track media key."""
    try:
        import pyautogui  # type: ignore
        pyautogui.press("prevtrack")
        return ok("Previous track.")
    except Exception as exc:
        return fail(str(exc))
