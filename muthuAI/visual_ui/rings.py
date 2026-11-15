"""
VOXAI Visual UI — visual_ui/rings.py

3D Perspective Orbital Ring System for the Living AI HUD Core.

Layers:
  1. Innermost Nucleus Shield Ring (r3: ~95px)
  2. Perspective Tilted 3D Ring A (pitch=28°, roll=15°)
  3. Perspective Tilted 3D Ring B (pitch=-25°, roll=-35°)
  4. Primary Counter-Rotating Segmented Ring 1 (r1: ~130px)
  5. Primary Segmented Ring 2 with Data Nodes (r2: ~180px)
  6. Outer Technical Arc Ring with Radial Tick Marks (r4: ~210px)
  7. Outer Coordinate Perimeter Ring with Telemetry Hashes (r5: ~245px)
  8. Rotating Radar-Style Scanning Sweep (in PROCESSING)

All methods accept a tkinter Canvas and render directly with sub-pixel quality.
"""

from __future__ import annotations
import math
import tkinter as tk
from visual_ui.effects import hex_color, blend, draw_3d_ellipse


class OrbitalRingSystem:
    """
    Manages multi-layer 3D-perspective orbital ring geometries,
    counter-rotating segments, technical ticks, and indicator data nodes.
    """

    def __init__(
        self,
        cx: int,
        cy: int,
        r1: float = 130.0,   # inner primary ring
        r2: float = 180.0,   # outer primary ring
        r3: float = 95.0,    # innermost shield ring
        r4: float = 215.0,   # technical tick ring
        r5: float = 250.0,   # outer perimeter ring
    ) -> None:
        self.cx = cx
        self.cy = cy
        self.r1 = r1
        self.r2 = r2
        self.r3 = r3
        self.r4 = r4
        self.r5 = r5

        self._angle1: float = 0.0
        self._angle2: float = 0.0
        self._angle3: float = 0.0
        self._angle4: float = 0.0
        self._tilt_phase: float = 0.0

    def update(self, dt: float, rpm1: float, rpm2: float) -> None:
        """Advance ring rotation angles based on dt and state RPMs."""
        self._angle1 += dt * rpm1 * 5.0       # rpm1 → deg/s (calm speed)
        self._angle2 += dt * rpm2 * 5.0       # rpm2 (counter-rotating)
        self._angle3 += dt * (rpm1 * 1.2) * 5.0
        self._angle4 += dt * (rpm2 * 0.6) * 5.0
        self._tilt_phase += dt * 0.4          # calm, smooth 3D precession

    def draw(
        self,
        canvas: tk.Canvas,
        color1: str,
        color2: str,
        glow_intensity: float,
        ring_width: int,
        processing_scan: bool = False,
        scan_angle: float = 0.0,
        draw_scale: float = 1.0,
        amplitude: float = 0.0,
    ) -> None:
        """Draw all 3D orbital rings, perspective tilts, and technical markers."""
        cx, cy = self.cx, self.cy
        s = draw_scale
        amp_exp = 1.0 + 0.12 * amplitude

        r1 = self.r1 * s * amp_exp
        r2 = self.r2 * s * amp_exp
        r3 = self.r3 * s * amp_exp
        r4 = self.r4 * s * amp_exp
        r5 = self.r5 * s * amp_exp

        # ── 1. Volumetric Glow Halos ──────────────────────────────────────────
        if glow_intensity > 0.1:
            glow1 = hex_color(color1, glow_intensity * 0.16)
            glow2 = hex_color(color2, glow_intensity * 0.14)
            canvas.create_oval(
                cx - r1 - 6, cy - r1 - 6,
                cx + r1 + 6, cy + r1 + 6,
                outline=glow1, width=int(8 * s),
            )
            canvas.create_oval(
                cx - r2 - 6, cy - r2 - 6,
                cx + r2 + 6, cy + r2 + 6,
                outline=glow2, width=int(8 * s),
            )

        # ── 2. Innermost Shield Ring (r3) ─────────────────────────────────────
        accent_col = hex_color(color1, 0.45)
        canvas.create_oval(
            cx - r3, cy - r3,
            cx + r3, cy + r3,
            outline=accent_col, width=max(1, int(1 * s)),
        )

        # ── 3. 3D Perspective-Tilted Elliptical Rings ─────────────────────────
        # Ring 3D-A: pitch tilted + rotating precession
        tilt_a = math.radians(24.0 + 6.0 * math.sin(self._tilt_phase))
        rx_a = (self.r1 * 1.15) * s
        ry_a = rx_a * 0.42   # flattened perspective
        draw_3d_ellipse(
            canvas, cx, cy, rx_a, ry_a,
            tilt_rad=tilt_a + math.radians(self._angle3 * 0.2),
            color=hex_color(color1, 0.35 * glow_intensity),
            width=max(1, int(1.5 * s)),
            dash=(6, 4),
        )

        # Ring 3D-B: counter-tilt
        tilt_b = math.radians(-32.0 - 5.0 * math.cos(self._tilt_phase * 0.8))
        rx_b = (self.r2 * 0.92) * s
        ry_b = rx_b * 0.38
        draw_3d_ellipse(
            canvas, cx, cy, rx_b, ry_b,
            tilt_rad=tilt_b + math.radians(self._angle4 * 0.2),
            color=hex_color(color2, 0.30 * glow_intensity),
            width=max(1, int(1.2 * s)),
            dash=(4, 6),
        )

        # ── 4. Primary Counter-Rotating Segmented Rings (r1, r2) ───────────────
        self._draw_segmented_ring(
            canvas, cx, cy, r1, color1, self._angle1, 24, 0.30, max(1, int(ring_width * s))
        )
        self._draw_segmented_ring(
            canvas, cx, cy, r2, color2, self._angle2, 18, 0.40, max(1, int(ring_width * s))
        )

        # ── 5. Orbital Indicator Data Nodes (r1: 3 nodes, r2: 4 nodes) ────────
        for k in range(3):
            a = math.radians(self._angle1 + k * 120)
            ix = cx + r1 * math.cos(a)
            iy = cy + r1 * math.sin(a)
            dot_r = max(2.0, 4.5 * s)
            canvas.create_oval(
                ix - dot_r, iy - dot_r,
                ix + dot_r, iy + dot_r,
                fill=color1,
                outline=hex_color(color1, 0.4),
                width=1,
            )

        for k in range(4):
            a = math.radians(self._angle2 + k * 90)
            ix = cx + r2 * math.cos(a)
            iy = cy + r2 * math.sin(a)
            dot_r = max(1.5, 3.5 * s)
            canvas.create_oval(
                ix - dot_r, iy - dot_r,
                ix + dot_r, iy + dot_r,
                fill=color2,
                outline=hex_color(color2, 0.4),
                width=1,
            )

        # ── 6. Outer Technical Arc Ring with Radial Tick Marks (r4) ────────────
        self._draw_tick_ring(
            canvas, cx, cy, r4, hex_color(color1, 0.35), n_ticks=36, tick_len=max(3.0, 6.0 * s)
        )

        # ── 7. Outer Telemetry Perimeter Ring (r5) ────────────────────────────
        self._draw_segmented_ring(
            canvas, cx, cy, r5, hex_color(color2, 0.22), self._angle4, 12, 0.65, max(1, int(1 * s))
        )

        # ── 8. PROCESSING: Radar Scanning Arc ──────────────────────────────────
        if processing_scan:
            self._draw_scan_arc(canvas, cx, cy, r2 + 16 * s, scan_angle, color1, s)

    def _draw_segmented_ring(
        self,
        canvas:     tk.Canvas,
        cx:         float,
        cy:         float,
        r:          float,
        color:      str,
        start_deg:  float,
        segments:   int,
        gap_frac:   float,
        width:      int,
    ) -> None:
        """Draw a ring as arc segments with gaps (technical dashed look)."""
        seg_deg  = 360.0 / segments
        draw_deg = seg_deg * (1.0 - gap_frac)
        for i in range(segments):
            a = start_deg + i * seg_deg
            canvas.create_arc(
                cx - r, cy - r,
                cx + r, cy + r,
                start=a,
                extent=draw_deg,
                outline=color,
                style=tk.ARC,
                width=width,
            )

    def _draw_tick_ring(
        self,
        canvas:   tk.Canvas,
        cx:       float,
        cy:       float,
        r:        float,
        color:    str,
        n_ticks:  int = 36,
        tick_len: float = 6.0,
    ) -> None:
        """Draw radial technical tick marks around radius r."""
        for i in range(n_ticks):
            angle = (i / n_ticks) * 2 * math.pi
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            x1 = cx + r * cos_a
            y1 = cy + r * sin_a
            x2 = cx + (r + tick_len) * cos_a
            y2 = cy + (r + tick_len) * sin_a
            canvas.create_line(x1, y1, x2, y2, fill=color, width=1)

    def _draw_scan_arc(
        self,
        canvas:     tk.Canvas,
        cx:         float,
        cy:         float,
        r:          float,
        scan_angle: float,
        color:      str,
        scale:      float,
    ) -> None:
        """Draw a rotating radar sweep arc with trailing glow."""
        # Bright leading arc
        canvas.create_arc(
            cx - r, cy - r,
            cx + r, cy + r,
            start=scan_angle,
            extent=35.0,
            outline=color,
            style=tk.ARC,
            width=max(2, int(3 * scale)),
        )
        # Dimmer trailing arc
        tail_col = hex_color(color, 0.35)
        canvas.create_arc(
            cx - r, cy - r,
            cx + r, cy + r,
            start=scan_angle - 40.0,
            extent=40.0,
            outline=tail_col,
            style=tk.ARC,
            width=max(1, int(2 * scale)),
        )
