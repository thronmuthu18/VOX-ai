"""
VOX AI Visual UI — visual_ui/task_hud_panel.py

TaskHUDPanel: Renders a floating task status overlay inside the compact window.

Shows:
  - Current executing step name
  - Step progress (● done / ○ pending / ▶ current)
  - State label (EXECUTING / VERIFYING / SUCCESS / ERROR)
  - Animated progress bar

Used by hud_canvas._draw_compact_task_panel() when in COMPACT mode.
"""

from __future__ import annotations
import math
import time
from visual_ui.effects import hex_color


class TaskHUDPanel:
    """
    Stateful task panel renderer for compact mode.
    Push updates via update_task().
    """

    def __init__(self) -> None:
        self._steps: list[dict] = []          # list of {name, status} where status in pending|running|done|failed
        self._current_step: str = ""
        self._total_steps: int = 0
        self._completed: int = 0
        self._state_label: str = "READY"
        self._t_start = time.perf_counter()

    def update_task(
        self,
        steps: list[dict] | None = None,
        current_step: str = "",
        state_label: str = "EXECUTING",
    ) -> None:
        """Update task progress data."""
        if steps is not None:
            self._steps = steps
            self._total_steps = len(steps)
            self._completed = sum(1 for s in steps if s.get("status") == "done")
        self._current_step = current_step
        self._state_label = state_label

    def reset(self) -> None:
        self._steps = []
        self._total_steps = 0
        self._completed = 0
        self._current_step = ""
        self._state_label = "READY"

    def draw(
        self,
        canvas,
        W: int,
        H: int,
        cx: float,
        cy: float,
        draw_scale: float,
        label_color: str,
        core_color: str,
        state_label: str,
        subtitle: str,
    ) -> None:
        """Draw the compact task status panel onto canvas."""
        ds = min(1.0, draw_scale)
        t = time.perf_counter() - self._t_start

        # --- Bottom status strip ---
        strip_h = max(24, int(28 * ds))
        strip_y = H - strip_h - 2
        bg_col = hex_color(core_color, 0.10)
        border_col = hex_color(label_color, 0.20)

        canvas.create_rectangle(
            3, strip_y, W - 3, H - 2,
            fill=bg_col, outline=border_col, width=1
        )

        # State label with blink cursor
        blink = int(t * 2) % 2 == 0
        lbl = state_label + (" ▌" if blink and state_label in ("EXECUTING", "VERIFYING", "PROCESSING") else "")
        fs = max(6, int(7 * ds))
        canvas.create_text(
            W // 2, strip_y + strip_h // 2 - 2,
            text=lbl, fill=label_color,
            font=("Courier", fs, "bold"), anchor="center"
        )

        # --- Subtitle / current step ---
        if subtitle:
            sub = (subtitle[:26] + "…") if len(subtitle) > 26 else subtitle
            y_sub = int(cy) + int(70 * ds)
            if 0 < y_sub < strip_y - 4:
                canvas.create_text(
                    int(cx), y_sub, text=sub,
                    fill=hex_color(label_color, 0.55),
                    font=("Courier", max(5, int(6 * ds))),
                    anchor="center"
                )

        # --- Step dots (up to 5 steps) ---
        if self._total_steps > 0 and self._total_steps <= 10:
            steps_to_show = self._steps[:5]
            dot_r = max(3, int(4 * ds))
            spacing = max(14, int(16 * ds))
            n = len(steps_to_show)
            start_x = cx - (n - 1) * spacing / 2
            y_dots = int(cy) + int(50 * ds)

            if 0 < y_dots < strip_y - 8:
                for i, step in enumerate(steps_to_show):
                    sx = int(start_x + i * spacing)
                    status = step.get("status", "pending")
                    if status == "done":
                        col = "#00FFCC"
                        canvas.create_oval(sx - dot_r, y_dots - dot_r,
                                           sx + dot_r, y_dots + dot_r,
                                           fill=col, outline="")
                        canvas.create_text(sx, y_dots, text="●",
                                           fill=col, font=("Courier", dot_r + 2),
                                           anchor="center")
                    elif status == "running":
                        # Pulsing dot
                        pulse = 0.5 + 0.5 * math.sin(t * 4)
                        r2 = dot_r + int(2 * pulse)
                        col = hex_color(label_color, 0.9)
                        canvas.create_oval(sx - r2, y_dots - r2,
                                           sx + r2, y_dots + r2,
                                           fill=col, outline="")
                    elif status == "failed":
                        col = "#F43F5E"
                        canvas.create_oval(sx - dot_r, y_dots - dot_r,
                                           sx + dot_r, y_dots + dot_r,
                                           fill=col, outline="")
                    else:
                        # Pending: outline only
                        col = hex_color(label_color, 0.25)
                        canvas.create_oval(sx - dot_r, y_dots - dot_r,
                                           sx + dot_r, y_dots + dot_r,
                                           fill="", outline=col, width=1)
