"""
VOXAI Visual UI — visual_ui/hud_bridge.py

Thread-safe event bridge: VOXAI backend → HUD canvas.

Carries two kinds of events:
  StateEvent       — HUDState + amplitude + text
  DisplayModeEvent — request to switch DisplayMode (fullscreen / compact)

Both are placed on a single queue consumed by the canvas render loop.
"""

from __future__ import annotations
import queue
import threading
from dataclasses import dataclass
from typing import Union
from visual_ui.hud_state    import HUDState, HUDEvent
from visual_ui.display_mode import DisplayMode


@dataclass
class DisplayModeEvent:
    """Request the canvas to change its display mode."""
    mode: DisplayMode


# Combined event type
BridgeEvent = Union[HUDEvent, DisplayModeEvent]


class HUDBridge:
    """
    Thread-safe unidirectional event bus: backend → HUD canvas.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[BridgeEvent] = queue.Queue(maxsize=128)
        self._lock = threading.Lock()
        self._current_state     = HUDState.BOOTING
        self._current_amplitude = 0.0
        self._current_text      = ""
        self._current_mode      = DisplayMode.FULLSCREEN

    # ── State event producer ──────────────────────────────────────────────────

    def post_event(
        self,
        state:       HUDState,
        amplitude:   float = 0.0,
        text:        str   = "",
        auto_return: bool  = False,
    ) -> None:
        """Post a state-change event (non-blocking, drops oldest if full)."""
        amplitude = max(0.0, min(1.0, amplitude))
        with self._lock:
            self._current_state     = state
            self._current_amplitude = amplitude
            self._current_text      = text

        self._put(HUDEvent(state=state, amplitude=amplitude,
                           text=text, auto_return=auto_return))

    def post_amplitude(self, amplitude: float) -> None:
        """Update amplitude only (keeps current state, used for waveform reactivity)."""
        amplitude = max(0.0, min(1.0, amplitude))
        with self._lock:
            self._current_amplitude = amplitude
            state = self._current_state
            text  = self._current_text
        self.post_event(state, amplitude, text)

    # ── Display mode producer ─────────────────────────────────────────────────

    def request_compact(self) -> None:
        """Request the canvas to animate to COMPACT mode."""
        with self._lock:
            self._current_mode = DisplayMode.COMPACT
        self._put(DisplayModeEvent(mode=DisplayMode.COMPACT))

    def request_fullscreen(self) -> None:
        """Request the canvas to animate to FULLSCREEN mode."""
        with self._lock:
            self._current_mode = DisplayMode.FULLSCREEN
        self._put(DisplayModeEvent(mode=DisplayMode.FULLSCREEN))

    # ── Consumer (canvas thread) ──────────────────────────────────────────────

    def get_event(self) -> BridgeEvent | None:
        """Non-blocking poll. Returns HUDEvent, DisplayModeEvent, or None."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    # ── Snapshot accessors ────────────────────────────────────────────────────

    @property
    def current_state(self) -> HUDState:
        with self._lock:
            return self._current_state

    @property
    def current_amplitude(self) -> float:
        with self._lock:
            return self._current_amplitude

    @property
    def current_text(self) -> str:
        with self._lock:
            return self._current_text

    @property
    def current_display_mode(self) -> DisplayMode:
        with self._lock:
            return self._current_mode

    # ── Internal ──────────────────────────────────────────────────────────────

    def _put(self, event: BridgeEvent) -> None:
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(event)
            except queue.Full:
                pass
