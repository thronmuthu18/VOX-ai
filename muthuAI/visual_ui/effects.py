"""
VOXAI Visual UI — visual_ui/effects.py

Shared colour utilities and glow/flash effects for the HUD canvas.

Functions:
    hex_color(base_hex, alpha)  — blend colour toward black
    blend(col1, col2, t)        — interpolate two colours
    draw_glow_orb(...)          — draw multi-layer radial glow
    draw_radial_lines(...)      — draw thin technical lines from centre
    draw_hex_grid(...)          — draw faint hex grid overlay
    draw_scanlines(...)         — draw animated horizontal scanlines
    draw_vignette(...)          — draw radial dark vignette
"""

from __future__ import annotations
import math
from typing import Any
import tkinter as tk


# ── Colour utilities ──────────────────────────────────────────────────────────

def hex_color(base_hex: str, alpha: float) -> str:
    """Blend a #rrggbb colour toward black by alpha [0.0–1.0]."""
    alpha = max(0.0, min(1.0, alpha))
    r = int(int(base_hex[1:3], 16) * alpha)
    g = int(int(base_hex[3:5], 16) * alpha)
    b = int(int(base_hex[5:7], 16) * alpha)
    return f"#{r:02x}{g:02x}{b:02x}"


def blend(col1: str, col2: str, t: float) -> str:
    """
    Linear interpolation between two #rrggbb colours.
    t=0 → col1, t=1 → col2.
    """
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(col1[1:3], 16), int(col1[3:5], 16), int(col1[5:7], 16)
    r2, g2, b2 = int(col2[1:3], 16), int(col2[3:5], 16), int(col2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Background effects ────────────────────────────────────────────────────────

def draw_vignette(
    canvas: tk.Canvas,
    cx: int,
    cy: int,
    w: int,
    h: int,
    core_color: str,
    layers: int = 20,
) -> None:
    """
    Radial vignette: layered ovals blending dark background toward
    a faint ambient glow near the centre.
    """
    for i in range(layers):
        frac  = i / layers                  # 0 = outer, 1 = inner
        r     = int(max(w, h) * 0.76 * (1 - frac * 0.78))
        amb   = hex_color(core_color, 0.08 * frac * frac)
        bg    = blend("#030712", amb, frac * 0.45)
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=bg, outline="")


def draw_hex_grid(canvas: tk.Canvas, w: int, h: int, spacing: int = 42) -> None:
    """
    Draw a faint hexagonal grid over the entire canvas (holographic feel).
    """
    dim  = "#081224"
    r_h  = spacing // 2 - 3
    row_h = int(spacing * 0.866)

    for row in range(-1, h // row_h + 2):
        for col in range(-1, w // spacing + 2):
            cx_h = col * spacing + (spacing // 2 if row % 2 else 0)
            cy_h = row * row_h
            pts  = []
            for k in range(6):
                angle = math.radians(60 * k - 30)
                pts.append(cx_h + r_h * math.cos(angle))
                pts.append(cy_h + r_h * math.sin(angle))
            canvas.create_polygon(pts, outline=dim, fill="", width=1)


def draw_scanlines(canvas: tk.Canvas, w: int, h: int, t: float, spacing: int = 7) -> None:
    """Animated horizontal scanlines that scroll downward slowly."""
    offset = int(t * 14) % spacing
    col    = "#050C1A"
    for y in range(offset, h, spacing):
        canvas.create_line(0, y, w, y, fill=col, width=1)


# ── Core glow ────────────────────────────────────────────────────────────────

def draw_glow_orb(
    canvas:    tk.Canvas,
    cx:        int,
    cy:        int,
    r_core:    float,
    color:     str,
    pulse:     float,     # 0.0–1.0 pulse phase value
    intensity: float,     # 0.0–1.0 glow intensity
    layers:    int = 9,
) -> None:
    """
    Draw a pulsing AI core orb with multi-layer glow halo.
    """
    # Outer glow halo layers
    for layer in range(layers, 0, -1):
        glow_r = r_core + layer * 10
        alpha  = intensity * 0.08 * (1 - layer / layers) * (0.65 + 0.35 * pulse)
        col    = hex_color(color, alpha)
        canvas.create_oval(
            cx - glow_r, cy - glow_r,
            cx + glow_r, cy + glow_r,
            fill=col, outline="",
        )

    # Core body: dark centre → bright rim (5 layers)
    for layer in range(5, 0, -1):
        layer_r = r_core * (layer / 5)
        frac    = layer / 5
        col     = blend("#030712", color, frac * (0.70 + 0.30 * pulse))
        canvas.create_oval(
            cx - layer_r, cy - layer_r,
            cx + layer_r, cy + layer_r,
            fill=col, outline="",
        )

    # Bright specular highlight
    h_r      = max(3.5, r_core * 0.28)
    h_offset = r_core * 0.24
    h_col    = blend(color, "#FFFFFF", 0.60 + 0.40 * pulse)
    canvas.create_oval(
        cx - h_offset - h_r, cy - h_offset - h_r,
        cx - h_offset + h_r, cy - h_offset + h_r,
        fill=h_col, outline="",
    )

    # Inner rim ring
    canvas.create_oval(
        cx - r_core - 2, cy - r_core - 2,
        cx + r_core + 2, cy + r_core + 2,
        outline=color, width=2,
    )
    canvas.create_oval(
        cx - r_core - 9, cy - r_core - 9,
        cx + r_core + 9, cy + r_core + 9,
        outline=hex_color(color, 0.22), width=5,
    )


# ── 3D Projection & Geometry Utilities ────────────────────────────────────────

def project_3d(
    x: float,
    y: float,
    z: float,
    cx: float,
    cy: float,
    focal: float = 600.0,
    scale: float = 1.0,
) -> tuple[float, float, float]:
    """
    Project 3D point (x, y, z) onto 2D screen at centre (cx, cy).
    Returns (screen_x, screen_y, depth_factor).
    depth_factor > 1.0 is foreground (closer), < 1.0 is background (farther).
    """
    z_clamped = max(-focal + 20.0, z)
    depth_factor = focal / (focal + z_clamped)
    sx = cx + x * depth_factor * scale
    sy = cy + y * depth_factor * scale
    return sx, sy, depth_factor


def rotate_3d(
    x: float,
    y: float,
    z: float,
    pitch: float = 0.0,  # X-axis rotation (radians)
    yaw:   float = 0.0,  # Y-axis rotation (radians)
    roll:  float = 0.0,  # Z-axis rotation (radians)
) -> tuple[float, float, float]:
    """Rotate 3D point around pitch, yaw, and roll axes."""
    # Pitch (around X)
    if pitch != 0.0:
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)
        y, z = y * cos_p - z * sin_p, y * sin_p + z * cos_p

    # Yaw (around Y)
    if yaw != 0.0:
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y

    # Roll (around Z)
    if roll != 0.0:
        cos_r, sin_r = math.cos(roll), math.sin(roll)
        x, y = x * cos_r - y * sin_r, x * sin_r + y * cos_r

    return x, y, z


def draw_3d_ellipse(
    canvas:     tk.Canvas,
    cx:         float,
    cy:         float,
    rx:         float,
    ry:         float,
    tilt_rad:   float,
    color:      str,
    width:      int = 1,
    dash:       tuple[int, ...] | None = None,
    segments:   int = 36,
) -> None:
    """Draw a rotated 3D-perspective ellipse wireframe using smoothed polygon."""
    pts: list[float] = []
    cos_t, sin_t = math.cos(tilt_rad), math.sin(tilt_rad)
    for i in range(segments + 1):
        theta = (i / segments) * 2 * math.pi
        ex = rx * math.cos(theta)
        ey = ry * math.sin(theta)
        # Apply 2D tilt rotation
        rot_x = ex * cos_t - ey * sin_t
        rot_y = ex * sin_t + ey * cos_t
        pts.extend([cx + rot_x, cy + rot_y])

    kwargs: dict[str, Any] = {"outline": color, "fill": "", "width": width, "smooth": True}
    if dash:
        kwargs["dash"] = dash
    canvas.create_polygon(pts, **kwargs)


# ── Technical line detail ────────────────────────────────────────────────────

def draw_radial_lines(
    canvas: tk.Canvas,
    cx:     int,
    cy:     int,
    r_min:  float,
    r_max:  float,
    count:  int,
    color:  str,
    angle_offset: float = 0.0,
) -> None:
    """Draw thin radial technical lines from r_min to r_max."""
    for k in range(count):
        angle = angle_offset + (k / count) * 2 * math.pi
        x1 = cx + r_min * math.cos(angle)
        y1 = cy + r_min * math.sin(angle)
        x2 = cx + r_max * math.cos(angle)
        y2 = cy + r_max * math.sin(angle)
        canvas.create_line(x1, y1, x2, y2, fill=color, width=1)


# ── Volumetric Core Glow ──────────────────────────────────────────────────────

def draw_volumetric_core(
    canvas:    tk.Canvas,
    cx:        float,
    cy:        float,
    r_core:    float,
    color:     str,
    pulse:     float,     # 0.0–1.0 pulse phase value
    intensity: float,     # 0.0–1.0 glow intensity
    state_str: str = "IDLE",
    t:         float = 0.0,
) -> None:
    """
    Multi-layered 3D holographic plasma core with Blue → Violet → Pink harmonics.
    Renders inner nucleus, volumetric corona, chromatic halo, and specular highlight.
    """
    layers = 12
    # 1. Outer Volumetric Corona
    for layer in range(layers, 0, -1):
        glow_r = r_core + layer * (r_core * 0.16)
        alpha = intensity * 0.08 * (1.0 - layer / layers) * (0.65 + 0.35 * pulse)
        # Gradient outward towards violet/pink
        halo_col = blend(color, "#8A2BE2", (layer / layers) * 0.5)
        col = hex_color(halo_col, alpha)
        canvas.create_oval(
            cx - glow_r, cy - glow_r,
            cx + glow_r, cy + glow_r,
            fill=col, outline="",
        )

    # 2. Chromatic Secondary Glow Rings (Pink-Violet accent)
    chroma_r = r_core * (1.12 + 0.06 * pulse)
    chroma_col = hex_color(blend(color, "#EC4899", 0.45), intensity * 0.28)
    canvas.create_oval(
        cx - chroma_r, cy - chroma_r,
        cx + chroma_r, cy + chroma_r,
        outline=chroma_col, width=2,
    )

    # 3. Dense Plasma Body (Spherical Shading from deep navy to vibrant blue-violet)
    core_steps = 7
    for step in range(core_steps, 0, -1):
        frac = step / core_steps
        step_r = r_core * frac
        layer_col = blend("#030712", color, (1.0 - frac * 0.5) * (0.75 + 0.25 * pulse))
        canvas.create_oval(
            cx - step_r, cy - step_r,
            cx + step_r, cy + step_r,
            fill=layer_col, outline="",
        )

    # 4. Inner Nucleus (Luminous white-blue with subtle pink tint)
    nucleus_r = max(4.0, r_core * (0.30 + 0.05 * math.sin(t * 2.5)))
    nucleus_col = blend(color, "#FFFFFF", 0.75 + 0.25 * pulse)
    canvas.create_oval(
        cx - nucleus_r, cy - nucleus_r,
        cx + nucleus_r, cy + nucleus_r,
        fill=nucleus_col, outline="",
    )

    # 5. Specular Holographic Glint
    spec_offset_x = -r_core * 0.26
    spec_offset_y = -r_core * 0.26
    spec_r = max(3.0, r_core * 0.18)
    canvas.create_oval(
        cx + spec_offset_x - spec_r, cy + spec_offset_y - spec_r,
        cx + spec_offset_x + spec_r, cy + spec_offset_y + spec_r,
        fill="#FFFFFF", outline="",
    )


# ── Flash effects ─────────────────────────────────────────────────────────────

def draw_success_flash(canvas: tk.Canvas, w: int, h: int, elapsed: float) -> None:
    """Green energy burst flash that fades over 1.2s."""
    alpha = max(0.0, 1.0 - elapsed * 0.9)
    if alpha > 0.01:
        col = hex_color("#00FF88", alpha * 0.22)
        canvas.create_rectangle(0, 0, w, h, fill=col, outline="")


def draw_error_flash(canvas: tk.Canvas, w: int, h: int, elapsed: float) -> None:
    """Red stutter flash — brief pulse every 0.55s."""
    phase = elapsed % 0.55
    if phase < 0.09:
        col = hex_color("#FF2244", 0.16)
        canvas.create_rectangle(0, 0, w, h, fill=col, outline="")


# ── Corner brackets & Reticles ───────────────────────────────────────────────

def draw_corner_brackets(
    canvas: tk.Canvas,
    w: int,
    h: int,
    color:  str,
    length: int = 24,
    margin: int = 14,
    width:  int = 2,
) -> None:
    """Four-corner HUD bracket markers with technical dots."""
    m, ln = margin, length
    c = color
    bw = width

    # Top-left
    canvas.create_line(m,     m,     m+ln, m,     fill=c, width=bw)
    canvas.create_line(m,     m,     m,    m+ln,  fill=c, width=bw)
    canvas.create_oval(m+ln+2, m-2, m+ln+6, m+2, fill=c, outline="")

    # Top-right
    canvas.create_line(w-m,   m,     w-m-ln, m,   fill=c, width=bw)
    canvas.create_line(w-m,   m,     w-m,  m+ln,  fill=c, width=bw)
    canvas.create_oval(w-m-ln-6, m-2, w-m-ln-2, m+2, fill=c, outline="")

    # Bottom-left
    canvas.create_line(m,     h-m,   m+ln, h-m,   fill=c, width=bw)
    canvas.create_line(m,     h-m,   m,    h-m-ln,fill=c, width=bw)
    canvas.create_oval(m+ln+2, h-m-2, m+ln+6, h-m+2, fill=c, outline="")

    # Bottom-right
    canvas.create_line(w-m,   h-m,   w-m-ln, h-m, fill=c, width=bw)
    canvas.create_line(w-m,   h-m,   w-m,  h-m-ln,fill=c, width=bw)
    canvas.create_oval(w-m-ln-6, h-m-2, w-m-ln-2, h-m+2, fill=c, outline="")
