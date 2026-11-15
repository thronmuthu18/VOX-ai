"""
VOXAI Visual UI — visual_ui/config.py

Reads all VISUAL_* configuration from .env.
All settings have sensible defaults and are optional.

Variables:
    VISUAL_UI_ENABLED          — master enable switch
    VISUAL_UI_OPACITY          — window opacity (0.0–1.0)
    VISUAL_UI_ALWAYS_ON_TOP    — keep window above other apps
    VISUAL_UI_INTENSITY        — glow/particle intensity scale (0.0–1.0)
    VISUAL_UI_THEME            — colour theme (blue_pink_violet|golden|teal|neon|red)
    VISUAL_UI_BOOT_DURATION    — procedural boot animation duration (seconds)

    VISUAL_WAKE_FULLSCREEN         — show fullscreen on boot
    VISUAL_TASK_COMPACT            — go compact when task processing starts
    VISUAL_RETURN_FULLSCREEN_AFTER_TASK — return to fullscreen after task ends
    VISUAL_RETURN_FULLSCREEN_ON_WAKE — go fullscreen on next wake word
    VISUAL_CONFIRMATION_FULLSCREEN — keep confirmation dialogs in fullscreen
    VISUAL_COMPACT_POSITION        — compact edge position (right|left|bottom|etc.)
    VISUAL_COMPACT_WIDTH           — compact window width  (px)
    VISUAL_COMPACT_HEIGHT          — compact window height (px)
    VISUAL_FULLSCREEN_FPS          — FPS while in fullscreen mode
    VISUAL_COMPACT_FPS             — FPS while in compact mode
    VISUAL_TRANSITION_DURATION     — fullscreen↔compact animation duration (s)
    VISUAL_BLINK                   — enable/disable blinking (default: False)
    VISUAL_AGGRESSIVE_PULSE        — enable/disable aggressive pulsing (default: False)
"""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=False)


def _b(key: str, default: bool) -> bool:
    val = os.getenv(key, "").strip().lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no"):
        return False
    return default


def _i(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _f(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _s(key: str, default: str) -> str:
    return os.getenv(key, default).strip()


# ── Master flag ───────────────────────────────────────────────────────────────
VISUAL_UI_ENABLED: bool = _b("VISUAL_UI_ENABLED", True)

# ── Legacy compact-only geometry (kept for backward compat) ──────────────────
VISUAL_UI_WIDTH:    int = _i("VISUAL_UI_WIDTH",  520)
VISUAL_UI_HEIGHT:   int = _i("VISUAL_UI_HEIGHT", 520)
VISUAL_UI_POSITION: str = _s("VISUAL_UI_POSITION", "bottom-right")

# ── Display options ───────────────────────────────────────────────────────────
VISUAL_UI_OPACITY:       float = _f("VISUAL_UI_OPACITY",       0.95)
VISUAL_UI_ALWAYS_ON_TOP: bool  = _b("VISUAL_UI_ALWAYS_ON_TOP", True)

# ── Aesthetics & Color Theme ──────────────────────────────────────────────────
VISUAL_UI_INTENSITY:    float = _f("VISUAL_UI_INTENSITY",    1.0)
VISUAL_UI_THEME:        str   = _s("VISUAL_UI_THEME",        "blue_pink_violet")
VISUAL_THEME:           str   = _s("VISUAL_THEME",           VISUAL_UI_THEME)
VISUAL_UI_BOOT_DURATION:float = _f("VISUAL_UI_BOOT_DURATION",3.5)
VISUAL_BLINK:           bool  = _b("VISUAL_BLINK",           False)
VISUAL_AGGRESSIVE_PULSE:bool  = _b("VISUAL_AGGRESSIVE_PULSE",False)

# ── Dual-Mode Behaviour ───────────────────────────────────────────────────────
# Show fullscreen on VOXAI boot/wake
VISUAL_WAKE_FULLSCREEN: bool = _b("VISUAL_WAKE_FULLSCREEN", True)
VISUAL_FULLSCREEN_ON_START: bool = _b("VISUAL_FULLSCREEN_ON_START", VISUAL_WAKE_FULLSCREEN)

# Automatically go compact when VOXAI starts actively executing a real task
VISUAL_TASK_COMPACT: bool = _b("VISUAL_TASK_COMPACT", True)

# Expand back to fullscreen when a task completes or fails
VISUAL_RETURN_FULLSCREEN_AFTER_TASK: bool = _b("VISUAL_RETURN_FULLSCREEN_AFTER_TASK", True)

# Expand back to fullscreen when the wake word is detected again
VISUAL_RETURN_FULLSCREEN_ON_WAKE: bool = _b("VISUAL_RETURN_FULLSCREEN_ON_WAKE", True)

# Confirmation must always be fullscreen
VISUAL_CONFIRMATION_FULLSCREEN: bool = _b("VISUAL_CONFIRMATION_FULLSCREEN", True)

# ── 3D Visual & Dynamics ──────────────────────────────────────────────────────
VISUAL_3D_DEPTH:         float = _f("VISUAL_3D_DEPTH",         1.0)
VISUAL_AUDIO_REACTIVITY: float = _f("VISUAL_AUDIO_REACTIVITY", 1.0)
VISUAL_PARTICLE_COUNT:   int   = _i("VISUAL_PARTICLE_COUNT",   48)

# ── Compact window ────────────────────────────────────────────────────────────
# position: right|left|top|bottom|top-right|top-left|bottom-right|bottom-left|center
VISUAL_COMPACT_POSITION: str = _s("VISUAL_COMPACT_POSITION", "right")
VISUAL_COMPACT_WIDTH:    int = _i("VISUAL_COMPACT_WIDTH",  200)
VISUAL_COMPACT_HEIGHT:   int = _i("VISUAL_COMPACT_HEIGHT", 200)

# ── Per-mode FPS ──────────────────────────────────────────────────────────────
VISUAL_FULLSCREEN_FPS: int = _i("VISUAL_FULLSCREEN_FPS", 60)
VISUAL_COMPACT_FPS:    int = _i("VISUAL_COMPACT_FPS",    30)

# ── Transition ────────────────────────────────────────────────────────────────
# Duration of fullscreen ↔ compact animation in seconds (600ms - 1200ms)
VISUAL_TRANSITION_DURATION: float = _f("VISUAL_TRANSITION_DURATION", 0.8)

# ── Derived constants ─────────────────────────────────────────────────────────
FS_FRAME_MS:      int = max(8,  1000 // max(10, VISUAL_FULLSCREEN_FPS))
COMPACT_FRAME_MS: int = max(16, 1000 // max(10, VISUAL_COMPACT_FPS))
FRAME_INTERVAL_MS: int = FS_FRAME_MS
