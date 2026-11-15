"""
VOXAI Visual UI — visual_ui/hud_state.py

State definitions for the VOXAI Living 3D AI HUD.
Maps directly to the VOXAI voice pipeline lifecycle states.

States:
    BOOTING      — AI wake-up boot animation sequence
    IDLE         — Alive and calm, subtle breathing, gentle orbital drift
    LISTENING    — Microphone waveform reactive (blue/violet)
    PROCESSING   — Mild vortex energy flow (pink/violet/blue)
    CONFIRMATION — Holographic confirmation prompt (violet/blue)
    SPEAKING     — Synchronized blue → violet → pink waveform & spatial waves
    SUCCESS      — Soft cyan-emerald expansion, then smooth return to IDLE
    ERROR        — Calm rose-crimson alert, then smooth return to IDLE
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HUDState(Enum):
    BOOTING      = "BOOTING"
    IDLE         = "IDLE"
    LISTENING    = "LISTENING"
    PROCESSING   = "PROCESSING"
    CONFIRMATION = "CONFIRMATION"
    EXECUTING    = "EXECUTING"
    VERIFYING    = "VERIFYING"
    SPEAKING     = "SPEAKING"
    SUCCESS      = "SUCCESS"
    ERROR        = "ERROR"


@dataclass
class HUDEvent:
    """
    An event posted to the HUD bridge.

    Attributes:
        state:        Target HUD visual state.
        amplitude:    Audio amplitude [0.0–1.0] for waveform reactivity.
        text:         Optional subtitle text displayed below the core.
        auto_return:  If True, HUD returns to IDLE automatically after a short flash.
    """
    state:       HUDState = HUDState.IDLE
    amplitude:   float    = 0.0
    text:        str      = ""
    auto_return: bool     = False


# ── Per-state animation parameters (Blue → Violet → Pink Theme) ───────────────
STATE_PARAMS: dict[HUDState, dict[str, Any]] = {
    HUDState.BOOTING: {
        "core_pulse_hz":    0.25,
        "orbital1_rpm":     0.12,
        "orbital2_rpm":    -0.10,
        "particle_speed":   0.25,
        "particle_alpha":   0.35,
        "core_color":       "#00D2FF",  # Soft azure blue
        "ring1_color":      "#8A2BE2",  # Soft violet
        "ring2_color":      "#EC4899",  # Soft pink
        "particle_color":   "#00D2FF",
        "label_color":      "#38BDF8",
        "glow_intensity":   0.40,
        "ring_width":       1,
    },
    HUDState.IDLE: {
        "core_pulse_hz":    0.35,  # Very slow, calm breathing
        "orbital1_rpm":     0.25,
        "orbital2_rpm":    -0.18,
        "particle_speed":   0.30,
        "particle_alpha":   0.50,
        "core_color":       "#00B4D8",  # Azure blue
        "ring1_color":      "#7928CA",  # Rich violet
        "ring2_color":      "#F43F5E",  # Rose-pink
        "particle_color":   "#38BDF8",
        "label_color":      "#7DD3FC",
        "glow_intensity":   0.50,
        "ring_width":       2,
    },
    HUDState.LISTENING: {
        "core_pulse_hz":    0.65,
        "orbital1_rpm":     0.45,
        "orbital2_rpm":    -0.35,
        "particle_speed":   0.55,
        "particle_alpha":   0.75,
        "core_color":       "#00F0FF",  # Bright electric cyan-blue
        "ring1_color":      "#A855F7",  # Bright violet
        "ring2_color":      "#EC4899",  # Vivid pink
        "particle_color":   "#00F0FF",
        "label_color":      "#38BDF8",
        "glow_intensity":   0.80,
        "ring_width":       2,
    },
    HUDState.PROCESSING: {
        "core_pulse_hz":    0.90,
        "orbital1_rpm":     0.95,
        "orbital2_rpm":    -0.80,
        "particle_speed":   0.85,
        "particle_alpha":   0.90,
        "core_color":       "#EC4899",  # Radiant pink
        "ring1_color":      "#9D4EDD",  # Electric violet
        "ring2_color":      "#00D2FF",  # Azure blue
        "particle_color":   "#F43F5E",
        "label_color":      "#F472B6",
        "glow_intensity":   0.95,
        "ring_width":       2,
    },
    HUDState.CONFIRMATION: {
        "core_pulse_hz":    0.45,
        "orbital1_rpm":     0.30,
        "orbital2_rpm":    -0.25,
        "particle_speed":   0.40,
        "particle_alpha":   0.70,
        "core_color":       "#8B5CF6",  # Violet
        "ring1_color":      "#00D2FF",  # Blue
        "ring2_color":      "#EC4899",  # Pink
        "particle_color":   "#A78BFA",
        "label_color":      "#C4B5FD",
        "glow_intensity":   0.75,
        "ring_width":       2,
    },
    HUDState.EXECUTING: {
        "core_pulse_hz":    0.80,
        "orbital1_rpm":     0.85,
        "orbital2_rpm":    -0.70,
        "particle_speed":   0.80,
        "particle_alpha":   0.85,
        "core_color":       "#00D2FF",  # Electric blue
        "ring1_color":      "#EC4899",  # Vivid pink
        "ring2_color":      "#9D4EDD",  # Violet
        "particle_color":   "#00D2FF",
        "label_color":      "#38BDF8",
        "glow_intensity":   0.90,
        "ring_width":       2,
    },
    HUDState.VERIFYING: {
        "core_pulse_hz":    0.70,
        "orbital1_rpm":     0.50,
        "orbital2_rpm":    -0.50,
        "particle_speed":   0.60,
        "particle_alpha":   0.80,
        "core_color":       "#A855F7",  # Bright violet
        "ring1_color":      "#00D2FF",  # Cyan-blue
        "ring2_color":      "#34D399",  # Mint
        "particle_color":   "#A855F7",
        "label_color":      "#C084FC",
        "glow_intensity":   0.85,
        "ring_width":       2,
    },
    HUDState.SPEAKING: {
        "core_pulse_hz":    0.60,
        "orbital1_rpm":     0.60,
        "orbital2_rpm":    -0.50,
        "particle_speed":   0.65,
        "particle_alpha":   0.85,
        "core_color":       "#00D2FF",  # Electric blue
        "ring1_color":      "#A855F7",  # Neon violet
        "ring2_color":      "#FF2A85",  # Neon pink
        "particle_color":   "#EC4899",
        "label_color":      "#E879F9",
        "glow_intensity":   0.90,
        "ring_width":       2,
    },
    HUDState.SUCCESS: {
        "core_pulse_hz":    1.10,
        "orbital1_rpm":     1.00,
        "orbital2_rpm":    -1.00,
        "particle_speed":   1.10,
        "particle_alpha":   0.95,
        "core_color":       "#00FFCC",  # Neon cyan-emerald
        "ring1_color":      "#10B981",  # Emerald
        "ring2_color":      "#06B6D4",  # Cyan
        "particle_color":   "#00FFCC",
        "label_color":      "#34D399",
        "glow_intensity":   0.95,
        "ring_width":       2,
    },
    HUDState.ERROR: {
        "core_pulse_hz":    0.50,
        "orbital1_rpm":     0.20,
        "orbital2_rpm":    -0.15,
        "particle_speed":   0.30,
        "particle_alpha":   0.65,
        "core_color":       "#F43F5E",  # Rose-crimson
        "ring1_color":      "#E11D48",
        "ring2_color":      "#9F1239",
        "particle_color":   "#FB7185",
        "label_color":      "#F43F5E",
        "glow_intensity":   0.75,
        "ring_width":       2,
    },
}

# States that auto-return to IDLE after their animation plays out
TRANSIENT_STATES = {HUDState.SUCCESS, HUDState.ERROR}
TRANSIENT_DURATION: dict[HUDState, float] = {
    HUDState.SUCCESS: 1.6,
    HUDState.ERROR:   2.0,
}
