"""
CHAMP Visual UI — visual_ui/display_mode.py

Display mode system: separates AI state from window presentation mode.

DisplayMode:
    FULLSCREEN   — window covers full screen (wake-up, listening on boot)
    COMPACT      — small edge-docked assistant (task execution, passive)
    TO_COMPACT   — animating from FULLSCREEN → COMPACT
    TO_FULL      — animating from COMPACT → FULLSCREEN

TransitionController:
    Manages the smooth lerp of window geometry (x, y, width, height)
    and the draw_scale factor used by the canvas renderer.
    Must be updated every frame.
"""

from __future__ import annotations
import math
from enum import Enum


class DisplayMode(Enum):
    FULLSCREEN = "FULLSCREEN"
    COMPACT    = "COMPACT"
    TO_COMPACT = "TO_COMPACT"   # transitioning → compact
    TO_FULL    = "TO_FULL"      # transitioning → fullscreen


def _ease_in_out(t: float) -> float:
    """Smooth S-curve easing (cubic)."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4 * t ** 3
    return 1 - (-2 * t + 2) ** 3 / 2


def _compact_xy(
    screen_w: int,
    screen_h: int,
    cw:       int,
    ch:       int,
    position: str,
    margin:   int = 18,
) -> tuple[int, int]:
    """
    Calculate the (x, y) top-left position for the compact window
    given a position string:
        right | left | top | bottom
        top-right | top-left | bottom-right | bottom-left | center
    """
    pos = position.strip().lower()
    if pos == "right":
        return screen_w - cw - margin, (screen_h - ch) // 2
    if pos == "left":
        return margin, (screen_h - ch) // 2
    if pos == "top":
        return (screen_w - cw) // 2, margin
    if pos == "bottom":
        return (screen_w - cw) // 2, screen_h - ch - margin
    if pos == "top-right":
        return screen_w - cw - margin, margin
    if pos == "top-left":
        return margin, margin
    if pos == "bottom-right":
        return screen_w - cw - margin, screen_h - ch - margin * 3
    if pos == "bottom-left":
        return margin, screen_h - ch - margin * 3
    if pos == "center":
        return (screen_w - cw) // 2, (screen_h - ch) // 2
    # Custom "x,y" coordinate
    if "," in pos:
        try:
            parts = pos.split(",")
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            pass
    # Default: bottom-right
    return screen_w - cw - margin, screen_h - ch - margin * 3


class TransitionController:
    """
    Controls smooth animated transitions between FULLSCREEN and COMPACT display modes.

    Each frame, call update(dt). Then read:
      - get_geometry()     → (x, y, w, h) for root.geometry()
      - get_draw_scale()   → float used by canvas to scale all radii/sizes
      - get_cx_cy(w, h)    → (cx, cy) canvas centre
      - current_mode       → current DisplayMode
    """

    # Design canvas size (base coordinate space)
    DESIGN_SIZE = 520.0

    def __init__(
        self,
        screen_w:          int,
        screen_h:          int,
        compact_w:         int,
        compact_h:         int,
        compact_position:  str,
        transition_dur:    float,
        wake_fullscreen:   bool,
    ) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.compact_w = compact_w
        self.compact_h = compact_h
        self.compact_position = compact_position
        self.transition_dur   = max(0.1, transition_dur)

        # Fullscreen window geometry
        self._fs_x = 0
        self._fs_y = 0
        self._fs_w = screen_w
        self._fs_h = screen_h

        # Compact window geometry
        cx, cy = _compact_xy(screen_w, screen_h, compact_w, compact_h, compact_position)
        self._cp_x = cx
        self._cp_y = cy
        self._cp_w = compact_w
        self._cp_h = compact_h

        # Draw-scale: FULLSCREEN maps canvas_size → screen_h (tall axis)
        self._fs_draw_scale = screen_h / self.DESIGN_SIZE
        self._cp_draw_scale = min(compact_w, compact_h) / self.DESIGN_SIZE

        # Initial mode
        if wake_fullscreen:
            self._mode = DisplayMode.FULLSCREEN
            self._cur_x   = float(self._fs_x)
            self._cur_y   = float(self._fs_y)
            self._cur_w   = float(self._fs_w)
            self._cur_h   = float(self._fs_h)
            self._cur_scale = self._fs_draw_scale
        else:
            self._mode = DisplayMode.COMPACT
            self._cur_x   = float(self._cp_x)
            self._cur_y   = float(self._cp_y)
            self._cur_w   = float(self._cp_w)
            self._cur_h   = float(self._cp_h)
            self._cur_scale = self._cp_draw_scale

        # Transition tracking
        self._progress: float    = 1.0   # 1.0 = done
        self._from_x   = self._cur_x
        self._from_y   = self._cur_y
        self._from_w   = self._cur_w
        self._from_h   = self._cur_h
        self._from_scale = self._cur_scale
        self._to_x     = self._cur_x
        self._to_y     = self._cur_y
        self._to_w     = self._cur_w
        self._to_h     = self._cur_h
        self._to_scale = self._cur_scale

        self._pending_mode: DisplayMode | None = None

    # ── Trigger transitions ────────────────────────────────────────────────────

    def go_compact(self) -> None:
        """Request transition to COMPACT mode."""
        if self._mode in (DisplayMode.COMPACT, DisplayMode.TO_COMPACT):
            return
        self._start_transition(DisplayMode.COMPACT)

    def go_fullscreen(self) -> None:
        """Request transition to FULLSCREEN mode."""
        if self._mode in (DisplayMode.FULLSCREEN, DisplayMode.TO_FULL):
            return
        self._start_transition(DisplayMode.FULLSCREEN)

    def _start_transition(self, target: DisplayMode) -> None:
        self._from_x     = self._cur_x
        self._from_y     = self._cur_y
        self._from_w     = self._cur_w
        self._from_h     = self._cur_h
        self._from_scale = self._cur_scale
        self._progress   = 0.0

        if target == DisplayMode.COMPACT:
            self._to_x     = float(self._cp_x)
            self._to_y     = float(self._cp_y)
            self._to_w     = float(self._cp_w)
            self._to_h     = float(self._cp_h)
            self._to_scale = self._cp_draw_scale
            self._mode     = DisplayMode.TO_COMPACT
        else:
            self._to_x     = float(self._fs_x)
            self._to_y     = float(self._fs_y)
            self._to_w     = float(self._fs_w)
            self._to_h     = float(self._fs_h)
            self._to_scale = self._fs_draw_scale
            self._mode     = DisplayMode.TO_FULL

    # ── Per-frame update ──────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Advance transition by dt seconds."""
        if self._mode not in (DisplayMode.TO_COMPACT, DisplayMode.TO_FULL):
            return

        self._progress = min(1.0, self._progress + dt / self.transition_dur)
        t = _ease_in_out(self._progress)

        def lerp(a: float, b: float) -> float:
            return a + (b - a) * t

        self._cur_x     = lerp(self._from_x,     self._to_x)
        self._cur_y     = lerp(self._from_y,      self._to_y)
        self._cur_w     = lerp(self._from_w,      self._to_w)
        self._cur_h     = lerp(self._from_h,      self._to_h)
        self._cur_scale = lerp(self._from_scale,  self._to_scale)

        if self._progress >= 1.0:
            if self._mode == DisplayMode.TO_COMPACT:
                self._mode = DisplayMode.COMPACT
            else:
                self._mode = DisplayMode.FULLSCREEN

    # ── Accessors ─────────────────────────────────────────────────────────────

    @property
    def current_mode(self) -> DisplayMode:
        return self._mode

    @property
    def is_transitioning(self) -> bool:
        return self._mode in (DisplayMode.TO_COMPACT, DisplayMode.TO_FULL)

    def get_geometry(self) -> tuple[int, int, int, int]:
        """Return (x, y, w, h) for tkinter geometry string."""
        return (
            int(self._cur_x),
            int(self._cur_y),
            max(80, int(self._cur_w)),
            max(80, int(self._cur_h)),
        )

    def get_draw_scale(self) -> float:
        """Return the scale factor for all canvas drawing coordinates."""
        return max(0.05, self._cur_scale)

    def get_cx_cy(self, w: int, h: int) -> tuple[float, float]:
        """Return canvas centre point for current window size."""
        return w / 2.0, h / 2.0

    @property
    def is_fullscreen(self) -> bool:
        return self._mode == DisplayMode.FULLSCREEN

    @property
    def is_compact(self) -> bool:
        return self._mode == DisplayMode.COMPACT

    @property
    def transition_progress(self) -> float:
        """0.0 = start of transition, 1.0 = complete."""
        return self._progress
