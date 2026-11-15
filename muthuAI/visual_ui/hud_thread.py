"""
VOXAI Visual UI — visual_ui/hud_thread.py

Launches the complete dual-mode HUD (Fullscreen + Compact) in a daemon thread.

  1. Creates tkinter root → gets screen dimensions
  2. Instantiates HUDCanvas with screen_w, screen_h
  3. Starts AudioAmplitudeEngine
  4. Runs tkinter mainloop()

Non-fatal: if it fails, VOXAI continues with voice/agent/TTS fully intact.
"""

from __future__ import annotations
import threading
import warnings
from typing import Optional

from visual_ui.hud_bridge import HUDBridge
from visual_ui.hud_state  import HUDState
from visual_ui.config     import VISUAL_UI_ENABLED

from utils.logger import get_logger

log = get_logger("muthuai.hud_thread")


def _run_hud(
    bridge:      HUDBridge,
    ready_event: threading.Event,
    audio_ref:   list,
) -> None:
    """Daemon thread target: initialise and run the HUD."""
    try:
        import tkinter as tk
        from visual_ui.hud_canvas import HUDCanvas

        root     = tk.Tk()
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        log.info("HUD: screen resolution detected as %dx%d", screen_w, screen_h)

        canvas = HUDCanvas(root, bridge, screen_w, screen_h)
        canvas.start()

        # Non-fatal audio amplitude engine
        try:
            from visual_ui.audio_reactive import AudioAmplitudeEngine
            engine = AudioAmplitudeEngine()
            engine.start()
            audio_ref.append(engine)
            log.info("HUD AudioAmplitudeEngine started.")
        except Exception as ae:
            log.debug("HUD audio engine unavailable (non-fatal): %s", ae)

        ready_event.set()
        log.info("VOXAI Dual-Mode HUD active (%dx%d).", screen_w, screen_h)
        root.mainloop()

    except Exception as exc:
        log.warning("VOXAI HUD failed to start (non-fatal): %s", exc)
        warnings.warn(f"VOXAI HUD failed: {exc}", RuntimeWarning, stacklevel=2)
        ready_event.set()
    finally:
        for eng in audio_ref:
            try:
                eng.stop()
            except Exception:
                pass


def start_hud(wait_timeout: float = 5.0) -> HUDBridge:
    """
    Launch the VOXAI dual-mode HUD in a daemon thread.

    Returns:
        HUDBridge with request_compact() and request_fullscreen() methods.
        Always safe to use; events are silently dropped if HUD failed.
    """
    bridge     = HUDBridge()
    ready      = threading.Event()
    audio_ref: list = []

    thread = threading.Thread(
        target=_run_hud,
        args=(bridge, ready, audio_ref),
        name="VOXAI-HUD",
        daemon=True,
    )
    thread.start()
    ready.wait(timeout=wait_timeout)
    return bridge


__all__ = ["start_hud", "HUDState", "HUDBridge", "VISUAL_UI_ENABLED"]
