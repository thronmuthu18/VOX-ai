"""
VOXAI Visual UI — visual_ui/waveform.py

Multi-Layer Audio-Reactive Frequency & Spatial Wave System for the Living AI HUD Core.

Features:
  1. Primary Semicircular Frequency Analyzer (40 bars with Blue → Violet → Pink gradients)
  2. Inner Circular Audio Plasma Wave (oscillating radial perimeter around core)
  3. Expanding 3D Spatial Energy Ripple Waves (propagate outward on audio surges)
  4. Full reactivity to microphone amplitude (LISTENING) and TTS audio playback (SPEAKING)
"""

from __future__ import annotations
import math
import tkinter as tk
from visual_ui.effects import hex_color, blend


class SpatialRipple:
    """An expanding 3D circular energy wave triggered by audio peaks."""
    def __init__(self, r0: float, speed: float, color: str, max_r: float) -> None:
        self.r = r0
        self.speed = speed
        self.color = color
        self.max_r = max_r
        self.alpha = 1.0
        self.alive = True

    def update(self, dt: float) -> None:
        self.r += self.speed * dt
        progress = self.r / self.max_r
        self.alpha = max(0.0, 1.0 - progress)
        if self.r >= self.max_r or self.alpha <= 0.01:
            self.alive = False


class FrequencyWaveform:
    """
    Multi-layer frequency analyzer and spatial acoustic wave renderer.
    """

    def __init__(
        self,
        cx: int,
        cy: int,
        r_inner: float = 195.0,
        r_max: float = 245.0,
        n_bars: int = 40,
        span_deg: float = 175.0,
    ) -> None:
        self.cx = cx
        self.cy = cy
        self.r_inner = r_inner
        self.r_max = r_max
        self.n_bars = n_bars
        self.span = span_deg

        # Per-bar smoothed amplitude [0.0–1.0]
        self._bars: list[float] = [0.0] * n_bars
        self._plasma_phase: float = 0.0
        self._ripples: list[SpatialRipple] = []
        self._last_surge_time: float = 0.0

    def update(
        self,
        dt: float,
        state_name: str,
        amplitude: float,
        t: float,
    ) -> None:
        """
        Update frequency bars, inner plasma oscillation, and spatial ripples.
        """
        self._plasma_phase += dt * (1.8 + 4.0 * amplitude)

        # Trigger spatial wave ripple on audio surges (calm propagation)
        if amplitude > 0.45 and (t - self._last_surge_time) > 0.40:
            self._last_surge_time = t
            surge_color = "#00F0FF" if state_name == "LISTENING" else ("#EC4899" if state_name == "SPEAKING" else "#8A2BE2")
            self._ripples.append(
                SpatialRipple(
                    r0=self.r_inner * 0.45,
                    speed=150.0 + amplitude * 90.0,
                    color=surge_color,
                    max_r=self.r_max * 1.25,
                )
            )

        # Update ripples
        for rip in self._ripples:
            rip.update(dt)
        self._ripples = [r for r in self._ripples if r.alive]

        # Update frequency bars
        for i in range(self.n_bars):
            frac = i / (self.n_bars - 1)
            phase = frac * 2.0 * math.pi

            if state_name == "PROCESSING":
                sweep_pos = (t * 0.9) % 1.0
                dist = abs(frac - sweep_pos)
                if dist > 0.5:
                    dist = 1.0 - dist
                wave = max(0.0, 1.0 - dist * 3.5)
                target = 0.10 + 0.55 * wave + 0.10 * abs(math.sin(t * 4.0 + phase))

            elif state_name in ("LISTENING", "SPEAKING"):
                bar_amp = amplitude * (0.60 + 0.40 * abs(math.sin(t * 3.5 + phase * 2.0)))
                centre_env = 0.55 + 0.45 * math.cos((frac - 0.5) * math.pi)
                target = bar_amp * centre_env + 0.04

            elif state_name == "SUCCESS":
                burst = max(0.0, 1.0 - t * 1.8) if t < 0.8 else 0.0
                target = burst * (0.70 + 0.30 * abs(math.sin(phase * 3)))

            elif state_name == "ERROR":
                stutter = 0.30 if int(t * 8) % 3 == 0 else 0.05
                target = stutter * abs(math.sin(phase))

            else:  # IDLE, BOOTING, CONFIRMATION
                breathe = 0.03 + 0.03 * abs(math.sin(t * 0.7 + phase * 0.5))
                target = breathe

            target = max(0.01, min(1.0, target))
            prev = self._bars[i]
            alpha_sm = 0.38 if target > prev else 0.18
            self._bars[i] = prev * (1.0 - alpha_sm) + target * alpha_sm

    def draw_to_canvas(
        self,
        canvas: tk.Canvas,
        color_dim: str,
        color_bright: str,
        scale: float = 1.0,
        amplitude: float = 0.0,
    ) -> None:
        """
        Draw all frequency bars with Blue → Violet → Pink gradient, inner plasma ring, and spatial ripple waves.
        """
        cx, cy = self.cx, self.cy
        r_in = self.r_inner * scale
        r_out = self.r_max * scale

        # ── 1. Spatial Ripple Waves ───────────────────────────────────────────
        for rip in self._ripples:
            rip_r = rip.r * scale
            rip_col = hex_color(rip.color, rip.alpha * 0.35)
            canvas.create_oval(
                cx - rip_r, cy - rip_r,
                cx + rip_r, cy + rip_r,
                outline=rip_col, width=max(1, int(2.0 * scale)),
            )

        # ── 2. Inner Circular Audio Plasma Wave ───────────────────────────────
        plasma_r = (self.r_inner * 0.55) * scale
        plasma_pts: list[float] = []
        steps = 32
        for s in range(steps + 1):
            ang = (s / steps) * 2 * math.pi
            disp = (2.5 * scale + amplitude * 9.0 * scale) * math.sin(ang * 4.0 + self._plasma_phase)
            cur_r = plasma_r + disp
            plasma_pts.extend([cx + cur_r * math.cos(ang), cy + cur_r * math.sin(ang)])

        plasma_glow_col = blend(color_bright, "#EC4899", 0.35)
        canvas.create_polygon(
            plasma_pts,
            outline=hex_color(plasma_glow_col, 0.40 + 0.30 * amplitude),
            fill="",
            width=max(1, int(1.5 * scale)),
            smooth=True,
        )

        # ── 3. Outer Semicircular Frequency Analyzer Bars (Blue → Violet → Pink) ──
        start_deg = -90.0 - self.span / 2.0

        for i, bar_val in enumerate(self._bars):
            frac = i / (self.n_bars - 1)
            angle = math.radians(start_deg + frac * self.span)

            bar_len = bar_val * (r_out - r_in)
            r_tip = r_in + bar_len

            ix = cx + r_in * math.cos(angle)
            iy = cy + r_in * math.sin(angle)
            ox = cx + r_tip * math.cos(angle)
            oy = cy + r_tip * math.sin(angle)

            # Harmonic gradient: Blue (#00D2FF) → Violet (#8A2BE2) → Pink (#EC4899)
            if frac < 0.5:
                base_c = blend("#00D2FF", "#8A2BE2", frac * 2.0)
            else:
                base_c = blend("#8A2BE2", "#EC4899", (frac - 0.5) * 2.0)

            bar_col = blend(
                hex_color(base_c, 0.35),
                base_c,
                min(1.0, bar_val * 1.35),
            )

            bw = max(1.2, (3.2 * bar_val + 1.0) * scale)
            canvas.create_line(
                ix, iy, ox, oy,
                fill=bar_col,
                width=bw,
                capstyle="round",
            )
