"""
VOXAI Visual UI — visual_ui/boot_sequence.py

Procedural AI wake-up / boot animation state machine.

Stages (configurable total duration ≈ 3.5s):

  STAGE 0 — BLACK      (0.0–0.25s):  Pure dark screen
  STAGE 1 — SPARK      (0.25–0.7s): Tiny bright dot at centre pulses into existence
  STAGE 2 — CORE_FORM  (0.7–1.4s): Core orb grows from 0 to full radius, glow builds
  STAGE 3 — RINGS_FORM (1.4–2.1s): Orbital rings materialise arc-by-arc
  STAGE 4 — PARTICLES  (2.1–2.7s): Particles fade in and begin orbiting
  STAGE 5 — EXPAND     (2.7–3.3s): Outer energy wave expands outward
  STAGE 6 — COMPLETE   (3.3s+):    System hands off to IDLE state
"""

from __future__ import annotations
import math
import tkinter as tk
from visual_ui.effects import hex_color, blend, draw_corner_brackets


# Stage breakpoints (fraction of total duration)
_STAGES = [
    ("BLACK",      0.00),
    ("SPARK",      0.07),
    ("CORE_FORM",  0.20),
    ("RINGS_FORM", 0.40),
    ("PARTICLES",  0.60),
    ("EXPAND",     0.77),
    ("COMPLETE",   0.94),
]


def _ease_out(t: float) -> float:
    """Ease-out cubic: fast start, slow end."""
    return 1.0 - (1.0 - t) ** 3


def _ease_in_out(t: float) -> float:
    """Ease-in-out: smooth S-curve."""
    if t < 0.5:
        return 4 * t ** 3
    return 1 - (-2 * t + 2) ** 3 / 2


class BootSequence:
    """
    Manages the procedural boot animation.
    Call update() each frame with elapsed time, then draw_to_canvas().
    Returns is_complete = True when animation is done.
    """

    def __init__(self, cx: int, cy: int, total_duration: float = 3.5) -> None:
        self.cx = cx
        self.cy = cy
        self.total_duration = total_duration
        self.is_complete = False
        self._elapsed: float = 0.0
        self._stage:   str   = "BLACK"
        self._stage_t: float = 0.0   # fractional progress within current stage

        # Expansion wave state
        self._wave_r: float = 0.0

    def update(self, dt: float) -> None:
        """Advance the boot animation by dt seconds."""
        if self.is_complete:
            return
        self._elapsed += dt
        frac = min(1.0, self._elapsed / self.total_duration)

        # Find current stage
        self._stage   = "COMPLETE"
        self._stage_t = 1.0
        for i, (name, start) in enumerate(_STAGES):
            next_start = _STAGES[i + 1][1] if i + 1 < len(_STAGES) else 1.0
            if frac < next_start:
                self._stage   = name
                self._stage_t = (frac - start) / max(1e-6, next_start - start)
                self._stage_t = max(0.0, min(1.0, self._stage_t))
                break

        if self._stage == "COMPLETE" or frac >= 1.0:
            self.is_complete = True

    def draw_to_canvas(
        self,
        canvas: tk.Canvas,
        w:      int,
        h:      int,
        core_color:  str = "#00D2FF",
        ring1_color: str = "#8A2BE2",
        ring2_color: str = "#EC4899",
    ) -> None:
        """Render the current boot frame onto the canvas."""
        stage = self._stage
        t     = self._stage_t   # 0.0 → 1.0 within stage

        if stage == "BLACK":
            return   # pure dark background already drawn

        if stage == "SPARK":
            # Tiny bright dot pulses into existence
            alpha = _ease_out(t)
            r     = 3 + 8 * _ease_out(t)
            col   = blend("#030712", core_color, alpha * 0.9)
            glow  = hex_color(core_color, alpha * 0.4)
            # Glow halo
            for gl in range(6, 0, -1):
                gr   = r + gl * 5
                gc   = hex_color(core_color, alpha * 0.04 * (1 - gl / 6))
                canvas.create_oval(
                    self.cx - gr, self.cy - gr,
                    self.cx + gr, self.cy + gr,
                    fill=gc, outline="",
                )
            canvas.create_oval(
                self.cx - r, self.cy - r,
                self.cx + r, self.cy + r,
                fill=col, outline="",
            )
            return

        if stage in ("CORE_FORM", "RINGS_FORM", "PARTICLES", "EXPAND", "COMPLETE"):
            # Base: draw the spark regardless
            self._draw_core(canvas, stage, t, core_color)

        if stage in ("RINGS_FORM", "PARTICLES", "EXPAND", "COMPLETE"):
            self._draw_rings(canvas, stage, t, ring1_color, ring2_color, core_color)

        if stage in ("PARTICLES", "EXPAND", "COMPLETE"):
            self._draw_particles_boot(canvas, stage, t, core_color)

        if stage in ("EXPAND", "COMPLETE"):
            self._draw_expansion_wave(canvas, stage, t, core_color)

        # Corner brackets fade in during EXPAND
        if stage in ("EXPAND", "COMPLETE"):
            alpha = _ease_out(t if stage == "EXPAND" else 1.0)
            col   = hex_color("#38BDF8", alpha * 0.5)
            draw_corner_brackets(canvas, w, h, col, length=20, margin=12, width=2)

        # Status text
        self._draw_boot_text(canvas, w, h, stage, t, ring1_color)

    def _draw_core(
        self,
        canvas:     tk.Canvas,
        stage:      str,
        t:          float,
        core_color: str,
    ) -> None:
        """Draw the growing core orb."""
        R_FINAL = 44

        if stage == "CORE_FORM":
            r     = R_FINAL * _ease_out(t)
            alpha = _ease_in_out(t)
        else:
            r     = R_FINAL
            alpha = 1.0

        if r < 1:
            return

        # Glow layers
        for layer in range(8, 0, -1):
            glow_r = r + layer * 9
            ga     = alpha * 0.06 * (1 - layer / 8)
            gc     = hex_color(core_color, ga)
            canvas.create_oval(
                self.cx - glow_r, self.cy - glow_r,
                self.cx + glow_r, self.cy + glow_r,
                fill=gc, outline="",
            )

        # Body layers
        for layer in range(5, 0, -1):
            lr  = r * (layer / 5)
            col = blend("#030712", core_color, (layer / 5) * alpha * 0.9)
            canvas.create_oval(
                self.cx - lr, self.cy - lr,
                self.cx + lr, self.cy + lr,
                fill=col, outline="",
            )

        # Rim
        canvas.create_oval(
            self.cx - r - 2, self.cy - r - 2,
            self.cx + r + 2, self.cy + r + 2,
            outline=hex_color(core_color, alpha), width=2,
        )

    def _draw_rings(
        self,
        canvas:      tk.Canvas,
        stage:       str,
        t:           float,
        ring1_color: str,
        ring2_color: str,
        core_color:  str,
    ) -> None:
        """Rings materialise progressively."""
        R1, R2 = 130, 178

        if stage == "RINGS_FORM":
            # Ring 1 appears first (first half of stage), ring 2 second
            if t < 0.5:
                r1_alpha = _ease_out(t * 2)
                r2_alpha = 0.0
            else:
                r1_alpha = 1.0
                r2_alpha = _ease_out((t - 0.5) * 2)
        else:
            r1_alpha = r2_alpha = 1.0

        # Ring 1
        if r1_alpha > 0.01:
            canvas.create_oval(
                self.cx - R1, self.cy - R1,
                self.cx + R1, self.cy + R1,
                outline=hex_color(ring1_color, r1_alpha * 0.7),
                width=2,
            )
        # Ring 2
        if r2_alpha > 0.01:
            canvas.create_oval(
                self.cx - R2, self.cy - R2,
                self.cx + R2, self.cy + R2,
                outline=hex_color(ring2_color, r2_alpha * 0.6),
                width=2,
            )

    def _draw_particles_boot(
        self,
        canvas:     tk.Canvas,
        stage:      str,
        t:          float,
        core_color: str,
    ) -> None:
        """8 particles fade in and spread out."""
        if stage == "PARTICLES":
            p_alpha = _ease_out(t)
            r       = 80 + 40 * _ease_out(t)
        else:
            p_alpha = 1.0
            r       = 120

        for k in range(8):
            angle = (k / 8) * 2 * math.pi + self._elapsed * 0.5
            px    = self.cx + r * math.cos(angle)
            py    = self.cy + r * math.sin(angle)
            col   = hex_color(core_color, p_alpha * 0.65)
            canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill=col, outline="")

    def _draw_expansion_wave(
        self,
        canvas:     tk.Canvas,
        stage:      str,
        t:          float,
        core_color: str,
    ) -> None:
        """Expanding energy ring that propagates outward."""
        if stage == "EXPAND":
            max_r = 240
            r     = 48 + (max_r - 48) * _ease_out(t)
            alpha = (1.0 - t) * 0.55
        else:
            return

        col = hex_color(core_color, alpha)
        canvas.create_oval(
            self.cx - r, self.cy - r,
            self.cx + r, self.cy + r,
            outline=col, width=3,
        )
        # Second fainter ring slightly behind
        r2    = r * 0.85
        col2  = hex_color(core_color, alpha * 0.4)
        canvas.create_oval(
            self.cx - r2, self.cy - r2,
            self.cx + r2, self.cy + r2,
            outline=col2, width=1,
        )

    def _draw_boot_text(
        self,
        canvas: tk.Canvas,
        w:      int,
        h:      int,
        stage:  str,
        t:      float,
        color:  str,
    ) -> None:
        """Minimal boot status text."""
        msgs = {
            "SPARK":      "INITIALISING...",
            "CORE_FORM":  "CORE ONLINE",
            "RINGS_FORM": "SYSTEMS NOMINAL",
            "PARTICLES":  "AI AWAKENING",
            "EXPAND":     "VOX AI ONLINE",
            "COMPLETE":   "READY",
        }
        msg   = msgs.get(stage, "")
        alpha = min(1.0, t * 2.5)
        col   = hex_color(color, alpha * 0.6)

        canvas.create_text(
            w // 2, h // 2 + 80,
            text=msg,
            fill=col,
            font=("Courier", 10, "bold"),
            anchor="center",
        )
