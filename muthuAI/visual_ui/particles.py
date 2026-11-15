"""
VOXAI Visual UI — visual_ui/particles.py

3D Volumetric Particle Field for the Living AI HUD Core.

Features:
  - 3 Depth Layers: Background (z < -40), Midground (-40 <= z <= 40), Foreground (z > 40)
  - 3D perspective projection via project_3d()
  - State-Driven Dynamics:
      IDLE:       Slow serene 3D spherical drift
      LISTENING:  Attraction vector pulling particles inward toward core
      PROCESSING: Smooth swirling 3D vortex data stream
      SPEAKING:   Radial vibration and pulsing reacting to audio
      SUCCESS:    Radiant outward expansion burst
      ERROR:      Gentle angular jitter and chromatic distortion
  - Dynamic fading trails based on 3D depth and velocity
"""

from __future__ import annotations
import math
import random
import tkinter as tk
from visual_ui.effects import hex_color, blend, project_3d, rotate_3d


class Particle3D:
    """A single particle in 3D spherical coordinate space."""
    def __init__(
        self,
        base_radius: float,
        theta: float,
        phi: float,
        size: float,
        speed_factor: float,
        depth_layer: int,  # -1 = bg, 0 = mid, 1 = fg
        trail_len: int = 3,
    ) -> None:
        self.base_radius = base_radius
        self.radius = base_radius
        self.theta = theta
        self.phi = phi
        self.size = size
        self.speed_factor = speed_factor
        self.depth_layer = depth_layer
        self.trail_len = trail_len
        self.history: list[tuple[float, float, float]] = []


class ParticleSystem:
    """
    Volumetric 3D particle field orbiting the AI core.
    """

    def __init__(
        self,
        count: int = 48,
        min_radius: float = 65.0,
        max_radius: float = 185.0,
        min_size: float = 1.2,
        max_size: float = 4.2,
        max_trail: int = 4,
    ) -> None:
        self._count = count
        self._particles: list[Particle3D] = []
        self._phases: list[float] = []
        self._burst_timer: float = 0.0

        random.seed(42)   # Deterministic placement
        for i in range(count):
            frac = i / count
            radius = min_radius + (max_radius - min_radius) * (frac ** 0.65)
            theta = frac * 2 * math.pi + random.uniform(-0.15, 0.15)
            phi = random.uniform(-math.pi / 3.5, math.pi / 3.5)  # spherical latitude
            size = min_size + (max_size - min_size) * ((i % 6) / 5.0)
            speed_f = 0.70 + 0.50 * random.random()
            layer = -1 if i % 3 == 0 else (1 if i % 3 == 1 else 0)
            trail = random.randint(2, max_trail)

            p = Particle3D(
                base_radius=radius,
                theta=theta,
                phi=phi,
                size=size,
                speed_factor=speed_f,
                depth_layer=layer,
                trail_len=trail,
            )
            self._particles.append(p)
            self._phases.append(theta)

    def update(
        self,
        dt: float,
        speed: float,
        state_str: str = "IDLE",
        amplitude: float = 0.0,
    ) -> None:
        """
        Advance particle positions and state-reactive behaviors with calm dynamics.
        """
        for i, p in enumerate(self._particles):
            # Speed scaling based on state (calm, damped motion)
            if state_str == "PROCESSING":
                ang_speed = speed * p.speed_factor * 1.8
                # Vortex inward swirl
                p.radius = max(48.0, p.base_radius * (0.80 + 0.20 * math.sin(p.theta * 1.5)))
            elif state_str == "LISTENING":
                ang_speed = speed * p.speed_factor * 1.2
                # Inward pull
                p.radius = max(52.0, p.base_radius * 0.90)
            elif state_str == "SPEAKING":
                ang_speed = speed * p.speed_factor * 1.3
                # Audio vibration
                p.radius = p.base_radius + amplitude * 16.0 * math.sin(p.theta * 3.0)
            elif state_str == "SUCCESS":
                ang_speed = speed * p.speed_factor * 1.5
                # Outward burst
                p.radius = p.base_radius * 1.25
            elif state_str == "ERROR":
                # Mild jitter
                ang_speed = speed * (1.0 + 0.4 * random.uniform(-1.0, 1.0))
                p.radius = p.base_radius + random.uniform(-4.0, 4.0)
            else:  # IDLE, BOOTING, CONFIRMATION
                ang_speed = speed * p.speed_factor * 0.85
                p.radius = p.base_radius + 3.0 * math.sin(p.theta * 1.2)

            p.theta += dt * ang_speed
            self._phases[i] = p.theta

            # Calculate 3D Cartesian coordinates from spherical
            x3d = p.radius * math.cos(p.phi) * math.cos(p.theta)
            y3d = p.radius * math.sin(p.phi) * 0.65 + p.radius * math.cos(p.phi) * math.sin(p.theta) * 0.45
            z3d = p.radius * math.sin(p.phi) * 1.2

            # Store in trail history (keep last N points)
            p.history.append((x3d, y3d, z3d))
            if len(p.history) > p.trail_len:
                p.history.pop(0)

    def draw_to_canvas(
        self,
        canvas: tk.Canvas,
        cx: int,
        cy: int,
        color: str,
        alpha: float,
        scale: float = 1.0,
        depth_factor: float = 1.0,
    ) -> None:
        """
        Render all 3D projected particles with depth shading and trailing nodes.
        """
        for i, p in enumerate(self._particles):
            if not p.history:
                continue

            x3d, y3d, z3d = p.history[-1]
            sx, sy, z_depth = project_3d(x3d, y3d, z3d, cx, cy, focal=500.0, scale=scale)

            # Chromatic layer coloring: foreground gets soft pink/white, midground azure, background violet
            if p.depth_layer == 1:
                p_col_base = blend(color, "#EC4899", 0.40)
            elif p.depth_layer == -1:
                p_col_base = blend(color, "#8A2BE2", 0.50)
            else:
                p_col_base = color

            # Shading by 3D depth
            layer_brightness = alpha * max(0.20, min(1.0, z_depth * 0.95))
            col = hex_color(p_col_base, layer_brightness)
            p_size = max(0.8, p.size * scale * z_depth)

            # Draw particle core
            canvas.create_oval(
                sx - p_size, sy - p_size,
                sx + p_size, sy + p_size,
                fill=col, outline="",
            )

            # Draw trails
            if len(p.history) > 1 and scale > 0.4:
                for tr_idx, (tx, ty, tz) in enumerate(p.history[:-1]):
                    tsx, tsy, tz_depth = project_3d(tx, ty, tz, cx, cy, focal=500.0, scale=scale)
                    tr_alpha = layer_brightness * ((tr_idx + 1) / len(p.history)) * 0.40
                    tr_col = hex_color(p_col_base, tr_alpha)
                    tr_size = max(0.5, p_size * 0.55)
                    canvas.create_oval(
                        tsx - tr_size, tsy - tr_size,
                        tsx + tr_size, tsy + tr_size,
                        fill=tr_col, outline="",
                    )
