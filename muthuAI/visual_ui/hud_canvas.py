"""
VOXAI Visual UI — visual_ui/hud_canvas.py

Dual-Mode VOXAI HUD Canvas — Fullscreen Wake + Compact Edge.

A SINGLE tkinter window morphs between:
    FULLSCREEN  — covers the entire screen, large cinematic 3D AI core
    COMPACT     — small edge-docked assistant (right/left/top/bottom)

The transition is a smooth animated geometry interpolation driven by
TransitionController: same window, same canvas, same AI core — just scaled.

Scale-Aware Rendering:
    All radii, sizes, and fonts are multiplied by `draw_scale`.
    draw_scale = current_canvas_height / DESIGN_SIZE (520px baseline)
    Fullscreen on 1080p → draw_scale ≈ 2.08
    Compact at 200px    → draw_scale ≈ 0.38

Components:
    ParticleSystem, OrbitalRingSystem, FrequencyWaveform, BootSequence, effects.*

Keyboard:
    ESC  — hide window (toggle off)
    F8   — toggle show/hide
    F11  — toggle fullscreen/compact manually
"""

from __future__ import annotations
import math
import time
import tkinter as tk
from typing import Any

from visual_ui.hud_bridge    import HUDBridge, DisplayModeEvent
from visual_ui.hud_state     import (
    HUDState, HUDEvent, STATE_PARAMS,
    TRANSIENT_STATES, TRANSIENT_DURATION,
)
from visual_ui.display_mode  import DisplayMode, TransitionController
from visual_ui.effects       import (
    hex_color, blend,
    draw_vignette, draw_hex_grid, draw_scanlines,
    draw_glow_orb, draw_volumetric_core, draw_radial_lines, draw_corner_brackets,
    draw_success_flash, draw_error_flash,
)
from visual_ui.particles     import ParticleSystem
from visual_ui.rings         import OrbitalRingSystem
from visual_ui.waveform      import FrequencyWaveform
from visual_ui.boot_sequence import BootSequence
from visual_ui.config import (
    VISUAL_UI_OPACITY,
    VISUAL_UI_ALWAYS_ON_TOP,
    VISUAL_UI_INTENSITY,
    VISUAL_UI_BOOT_DURATION,
    VISUAL_WAKE_FULLSCREEN,
    VISUAL_TASK_COMPACT,
    VISUAL_RETURN_FULLSCREEN_ON_WAKE,
    VISUAL_COMPACT_POSITION,
    VISUAL_COMPACT_WIDTH,
    VISUAL_COMPACT_HEIGHT,
    VISUAL_TRANSITION_DURATION,
    FS_FRAME_MS,
    COMPACT_FRAME_MS,
)

# Base design canvas size (all coordinates designed at this resolution)
DESIGN_SIZE = 520.0
# Base radii (at DESIGN_SIZE scale = 1.0) — calm, mild breathing
R_CORE_MIN   = 38.0
R_CORE_MAX   = 42.0
R_ORB1_BASE  = 130.0
R_ORB2_BASE  = 180.0
R_ORB3_BASE  = 95.0
R_WAVE_INNER = 200.0
R_WAVE_OUTER = 240.0
R_PARTICLE_MIN = 65.0
R_PARTICLE_MAX = 150.0


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


class HUDCanvas:
    """
    Dual-mode HUD renderer. Single tkinter window that morphs between
    fullscreen and compact via TransitionController.
    """

    def __init__(
        self,
        root:        tk.Tk,
        bridge:      HUDBridge,
        screen_w:    int,
        screen_h:    int,
    ) -> None:
        self.root     = root
        self.bridge   = bridge
        self.screen_w = screen_w
        self.screen_h = screen_h

        # ── Global clock ──────────────────────────────────────────────────────
        self._t0         = time.perf_counter()
        self._last_frame = time.perf_counter()

        # ── AI state ──────────────────────────────────────────────────────────
        self._state         = HUDState.BOOTING
        self._state_enter_t = time.perf_counter()
        self._amplitude     = 0.0
        self._subtitle      = ""
        self._visible       = True

        # Smooth parameter interpolation
        self._params: dict[str, Any] = dict(STATE_PARAMS[HUDState.BOOTING])
        self._target: dict[str, Any] = dict(STATE_PARAMS[HUDState.BOOTING])

        # ── Display mode controller ───────────────────────────────────────────
        self._transition = TransitionController(
            screen_w=screen_w,
            screen_h=screen_h,
            compact_w=VISUAL_COMPACT_WIDTH,
            compact_h=VISUAL_COMPACT_HEIGHT,
            compact_position=VISUAL_COMPACT_POSITION,
            transition_dur=VISUAL_TRANSITION_DURATION,
            wake_fullscreen=VISUAL_WAKE_FULLSCREEN,
        )

        # ── Animation values ──────────────────────────────────────────────────
        self._pulse_phase: float = 0.0
        self._scan_angle:  float = 0.0

        # ── Components (recreated when scale changes significantly) ───────────
        self._particles = ParticleSystem(
            count=max(8, int(24 * VISUAL_UI_INTENSITY)),
            min_radius=R_PARTICLE_MIN,
            max_radius=R_PARTICLE_MAX,
        )
        self._rings    = OrbitalRingSystem(
            cx=0, cy=0,   # updated each frame via draw_scale
            r1=R_ORB1_BASE,
            r2=R_ORB2_BASE,
            r3=R_ORB3_BASE,
        )
        self._waveform = FrequencyWaveform(
            cx=0, cy=0,
            r_inner=R_WAVE_INNER,
            r_max=R_WAVE_OUTER,
            n_bars=40,
            span_deg=170.0,
        )
        self._boot = BootSequence(
            cx=screen_w // 2,
            cy=screen_h // 2,
            total_duration=VISUAL_UI_BOOT_DURATION,
        )

        # Task status panel for compact mode
        from visual_ui.task_hud_panel import TaskHUDPanel
        self._task_panel = TaskHUDPanel()

        # ── Drag support ──────────────────────────────────────────────────────
        self._drag_x = 0
        self._drag_y = 0

        # ── Window + Canvas setup ─────────────────────────────────────────────
        self._setup_window()
        self.canvas = tk.Canvas(
            root,
            bg="#050A14",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._bind_events()

        # Apply initial geometry
        self._apply_geometry()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.root.title("VOX AI")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", VISUAL_UI_ALWAYS_ON_TOP)
        self.root.attributes("-alpha",   VISUAL_UI_OPACITY)
        self.root.resizable(False, False)
        self.root.configure(bg="#030712")

    def _apply_geometry(self) -> None:
        x, y, w, h = self._transition.get_geometry()
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas.config(width=w, height=h)

    # ── Bindings ──────────────────────────────────────────────────────────────

    def _bind_events(self) -> None:
        c = self.canvas
        c.bind("<ButtonPress-1>",   self._drag_start)
        c.bind("<B1-Motion>",       self._drag_move)
        c.bind("<Button-3>",        lambda e: self._toggle_visible())

        self.root.bind("<Escape>",  self._hide)
        self.root.bind("<F8>",      self._toggle_visible)
        self.root.bind("<F11>",     self._toggle_display_mode)

    def _drag_start(self, e: Any) -> None:
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _drag_move(self, e: Any) -> None:
        self.root.geometry(
            f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}"
        )

    def _hide(self, e: Any = None) -> None:
        self._visible = False
        self.root.withdraw()

    def _toggle_visible(self, e: Any = None) -> None:
        if self._visible:
            self._hide()
        else:
            self._visible = True
            self.root.deiconify()

    def _toggle_display_mode(self, e: Any = None) -> None:
        mode = self._transition.current_mode
        if mode in (DisplayMode.FULLSCREEN, DisplayMode.TO_FULL):
            self._transition.go_compact()
        else:
            self._transition.go_fullscreen()

    # ── Public ────────────────────────────────────────────────────────────────

    def start(self) -> None:
        self.root.after(FS_FRAME_MS, self._frame)

    # ── Main render loop ──────────────────────────────────────────────────────

    def _frame(self) -> None:
        now = time.perf_counter()
        dt  = min(now - self._last_frame, 0.10)
        self._last_frame = now
        t   = now - self._t0

        # ── Consume bridge events ─────────────────────────────────────────────
        while True:
            ev = self.bridge.get_event()
            if ev is None:
                break
            if isinstance(ev, DisplayModeEvent):
                if ev.mode == DisplayMode.COMPACT:
                    self._transition.go_compact()
                else:
                    self._transition.go_fullscreen()
            elif isinstance(ev, HUDEvent):
                if ev.state != self._state:
                    self._state         = ev.state
                    self._state_enter_t = now
                    self._target        = dict(STATE_PARAMS[ev.state])
                self._amplitude = ev.amplitude
                self._subtitle  = ev.text
                # Update task panel for executing/verifying states
                if ev.state in (HUDState.EXECUTING, HUDState.VERIFYING, HUDState.PROCESSING):
                    self._task_panel.update_task(
                        current_step=ev.text,
                        state_label=ev.state.value,
                    )
                elif ev.state in (HUDState.SUCCESS, HUDState.IDLE, HUDState.ERROR):
                    self._task_panel.reset()

        # ── Auto-return transient states ──────────────────────────────────────
        if self._state in TRANSIENT_STATES:
            if now - self._state_enter_t >= TRANSIENT_DURATION.get(self._state, 1.5):
                self._state         = HUDState.IDLE
                self._state_enter_t = now
                self._target        = dict(STATE_PARAMS[HUDState.IDLE])

        # ── Boot sequence ─────────────────────────────────────────────────────
        if self._state == HUDState.BOOTING:
            self._boot.update(dt)
            if self._boot.is_complete:
                self._state         = HUDState.IDLE
                self._state_enter_t = now
                self._target        = dict(STATE_PARAMS[HUDState.IDLE])
                self.bridge.post_event(HUDState.IDLE, text="READY")

        # ── Transition update + geometry apply ────────────────────────────────
        self._transition.update(dt)
        self._apply_geometry()

        # ── Smooth param lerp ─────────────────────────────────────────────────
        lr = min(1.0, dt / 0.28)
        for k in ("core_pulse_hz", "orbital1_rpm", "orbital2_rpm",
                  "particle_speed", "particle_alpha", "glow_intensity"):
            cur_v = float(self._params[k])
            tgt_v = float(self._target[k]) if k in self._target else cur_v
            self._params[k] = _lerp(cur_v, tgt_v, lr)

        for k in ("core_color", "ring1_color", "ring2_color", "particle_color", "label_color"):
            cur_c = str(self._params[k])
            tgt_c = str(self._target[k]) if k in self._target else cur_c
            self._params[k] = blend(cur_c, tgt_c, lr)

        # ── Current window dimensions ─────────────────────────────────────────
        _, _, W, H = self._transition.get_geometry()
        W = max(80, W)
        H = max(80, H)
        ds = self._transition.get_draw_scale()    # draw scale
        cx, cy = W / 2.0, H / 2.0

        # ── Advance animation values ──────────────────────────────────────────
        hz  = float(self._params["core_pulse_hz"])
        self._pulse_phase += dt * hz * 2 * math.pi

        rpm1 = float(self._params["orbital1_rpm"])
        rpm2 = float(self._params["orbital2_rpm"])
        self._rings.update(dt, rpm1, rpm2)

        sp = float(self._params["particle_speed"])
        self._particles.update(dt, sp, state_str=self._state.value, amplitude=self._amplitude)

        if self._state == HUDState.PROCESSING:
            self._scan_angle += dt * 110

        self._waveform.update(dt, self._state.value, self._amplitude, t)

        # ── Determine FPS for next frame ──────────────────────────────────────
        mode = self._transition.current_mode
        if mode == DisplayMode.COMPACT:
            next_ms = COMPACT_FRAME_MS
        else:
            next_ms = FS_FRAME_MS

        # ── Render ────────────────────────────────────────────────────────────
        c = self.canvas
        c.delete("all")

        if self._state == HUDState.BOOTING:
            self._draw_bg(c, cx, cy, W, H, t, ds)
            core_col  = str(STATE_PARAMS[HUDState.IDLE]["core_color"])
            ring1_col = str(STATE_PARAMS[HUDState.IDLE]["ring1_color"])
            ring2_col = str(STATE_PARAMS[HUDState.IDLE]["ring2_color"])
            # Scale boot sequence to current window
            self._draw_boot(c, cx, cy, W, H, ds, core_col, ring1_col, ring2_col, t)
        else:
            self._draw_bg(c, cx, cy, W, H, t, ds)
            self._draw_hex_grid(c, W, H, ds)
            self._draw_scanlines(c, W, H, t)
            self._draw_rings(c, cx, cy, ds)
            self._draw_particles(c, cx, cy, ds)
            self._draw_waveform(c, cx, cy, ds)
            self._draw_core(c, cx, cy, ds, t)
            self._draw_labels(c, cx, cy, W, H, ds, t)
            self._draw_overlays(c, W, H, t)

        self.root.after(next_ms, self._frame)

    # ── Rendering helpers (all scale-aware) ───────────────────────────────────

    def _draw_bg(self, c, cx, cy, W, H, t, ds):
        c.create_rectangle(0, 0, W, H, fill="#030712", outline="")
        # Fullscreen gets extra atmospheric rings
        if self._transition.is_fullscreen or self._transition.is_transitioning:
            # Wide radial vignette for fullscreen feel
            draw_vignette(c, int(cx), int(cy), W, H,
                          str(self._params["core_color"]), layers=24)
            # Atmosphere: very faint outer concentric rings
            r_atm = min(W, H) * 0.45
            for k in range(3):
                ri = r_atm * (0.6 + k * 0.2)
                col = hex_color(str(self._params["ring1_color"]), 0.04 - k * 0.01)
                c.create_oval(cx-ri, cy-ri, cx+ri, cy+ri, outline=col, width=1)
        else:
            draw_vignette(c, int(cx), int(cy), W, H,
                          str(self._params["core_color"]), layers=16)

    def _draw_hex_grid(self, c, W, H, ds):
        spacing = max(20, int(42 * ds))
        draw_hex_grid(c, W, H, spacing=spacing)

    def _draw_scanlines(self, c, W, H, t):
        draw_scanlines(c, W, H, t, spacing=max(4, 7))

    def _draw_rings(self, c, cx, cy, ds):
        self._rings.cx = int(cx)
        self._rings.cy = int(cy)
        self._rings.r1 = R_ORB1_BASE
        self._rings.r2 = R_ORB2_BASE
        self._rings.r3 = R_ORB3_BASE

        processing = (self._state == HUDState.PROCESSING)
        rw = max(1, int(float(self._params.get("ring_width", 2))))
        self._rings.draw(
            c,
            color1=str(self._params["ring1_color"]),
            color2=str(self._params["ring2_color"]),
            glow_intensity=float(self._params["glow_intensity"]) * VISUAL_UI_INTENSITY,
            ring_width=rw,
            processing_scan=processing,
            scan_angle=self._scan_angle,
            draw_scale=ds,
            amplitude=self._amplitude,
        )

        if self._state == HUDState.PROCESSING:
            col = hex_color(str(self._params["ring1_color"]), 0.12)
            draw_radial_lines(c, int(cx), int(cy),
                              55 * ds, 135 * ds, 16, col,
                              self._scan_angle * 0.3)

    def _draw_particles(self, c, cx, cy, ds):
        self._particles.draw_to_canvas(
            c, int(cx), int(cy),
            color=str(self._params["particle_color"]),
            alpha=float(self._params["particle_alpha"]) * VISUAL_UI_INTENSITY,
            scale=ds,
        )

    def _draw_waveform(self, c, cx, cy, ds):
        self._waveform.cx     = int(cx)
        self._waveform.cy     = int(cy)
        self._waveform.r_inner = R_WAVE_INNER
        self._waveform.r_max   = R_WAVE_OUTER
        r1c = str(self._params["ring1_color"])
        r2c = str(self._params["ring2_color"])
        self._waveform.draw_to_canvas(c, r1c, r2c, scale=ds, amplitude=self._amplitude)

    def _draw_core(self, c, cx, cy, ds, t):
        pulse  = 0.5 + 0.5 * math.sin(self._pulse_phase)
        r_core = (R_CORE_MIN + (R_CORE_MAX - R_CORE_MIN) * pulse) * ds
        col    = str(self._params["core_color"])
        inten  = float(self._params["glow_intensity"]) * VISUAL_UI_INTENSITY
        draw_volumetric_core(c, cx, cy, r_core, col, pulse, inten, state_str=self._state.value, t=t)

    def _draw_labels(self, c, cx, cy, W, H, ds, t):
        lc  = str(self._params["label_color"])
        dim = hex_color(lc, 0.45)

        # Only show labels if window is large enough
        min_dim = min(W, H)
        if min_dim < 120:
            return

        font_size_brand = max(7, int(11 * ds))
        font_size_sub   = max(5, int(7  * ds))
        font_size_state = max(6, int(10 * ds))

        # Brand text
        if min_dim > 150:
            c.create_text(int(cx), int(cy) - int(60 * ds),
                          text="V O X   A I", fill=lc,
                          font=("Courier", font_size_brand, "bold"),
                          anchor="center")
            if min_dim > 200:
                c.create_text(int(cx), int(cy) - int(45 * ds),
                              text="VOX AI PERSONAL ASSISTANT",
                              fill=hex_color(lc, 0.35),
                              font=("Courier", font_size_sub),
                              anchor="center")

        # State name
        state_name = self._state.value
        if self._state in (HUDState.LISTENING, HUDState.PROCESSING, HUDState.EXECUTING, HUDState.VERIFYING):
            if int(t * 3) % 2 == 0:
                state_name += " ▌"

        y_state = int(cy) + int(68 * ds)
        if y_state < H - 10:
            c.create_text(int(cx), y_state,
                          text=state_name, fill=lc,
                          font=("Courier", font_size_state, "bold"),
                          anchor="center")

        # Subtitle
        if self._subtitle and min_dim > 160:
            sub = (self._subtitle[:40] + "…") if len(self._subtitle) > 40 else self._subtitle
            y_sub = int(cy) + int(84 * ds)
            if y_sub < H - 6:
                c.create_text(int(cx), y_sub, text=sub,
                              fill=hex_color(lc, 0.5),
                              font=("Courier", font_size_sub),
                              anchor="center")

        # Fullscreen: bottom status bar + corner brackets
        if min_dim > 250:
            c.create_text(int(cx), H - 12,
                          text="● VOX AI ONLINE  |  NEURAL CORE  |  VOICE ACTIVE",
                          fill=hex_color(lc, 0.30),
                          font=("Courier", font_size_sub),
                          anchor="center")

        blen = max(10, int(20 * min(1.0, ds)))
        brg  = hex_color(lc, 0.40)
        draw_corner_brackets(c, W, H, brg, length=blen, margin=10, width=max(1, int(2 * min(1.0, ds))))

        # Compact mode: task status panel
        if self._transition.is_compact and min_dim >= 100:
            # Corner indicator dot
            c.create_text(W - 6, 6,
                          text="◉", fill=hex_color(lc, 0.5),
                          font=("Courier", max(7, int(9 * ds))),
                          anchor="ne")
            # Draw full task panel
            self._task_panel.draw(
                canvas=c,
                W=W, H=H,
                cx=cx, cy=cy,
                draw_scale=ds,
                label_color=lc,
                core_color=str(self._params["core_color"]),
                state_label=self._state.value,
                subtitle=self._subtitle,
            )

        # Tick counter
        if min_dim > 200:
            tick = int(t * 10) % 100
            c.create_text(W - 14, 12, text=f"{tick:02d}",
                          fill=hex_color(lc, 0.30),
                          font=("Courier", font_size_sub), anchor="e")

    def _draw_overlays(self, c, W, H, t):
        elapsed = t - (self._state_enter_t - self._t0)
        if self._state == HUDState.SUCCESS:
            draw_success_flash(c, W, H, elapsed)
        elif self._state == HUDState.ERROR:
            draw_error_flash(c, W, H, elapsed)

        # Transition overlay: subtle vignette pulse during morph
        if self._transition.is_transitioning:
            prog = self._transition.transition_progress
            pulse_a = 0.06 * math.sin(prog * math.pi)
            col = hex_color(str(self._params["core_color"]), pulse_a)
            c.create_rectangle(0, 0, W, H, fill=col, outline="")

    def _draw_boot(self, c, cx, cy, W, H, ds, core_col, ring1_col, ring2_col, t):
        """Render boot sequence scaled to current window size."""
        # Update boot sequence's cx/cy for current window dimensions
        self._boot.cx = int(cx)
        self._boot.cy = int(cy)
        self._boot._elapsed = self._boot._elapsed   # keep time
        self._boot.draw_to_canvas(c, W, H, core_col, ring1_col, ring2_col)
