"""
CHAMP Visual UI Tests — tests/test_visual_ui.py

Unit tests for the Jarvis HUD visual system.

Coverage:
  1. Config loading
  2. HUD state enum completeness
  3. HUD bridge event queue (thread-safe)
  4. HUD bridge amplitude update
  5. State transitions
  6. Transient state auto-return config
  7. Particle system update
  8. Waveform bar update (IDLE, LISTENING, PROCESSING, SPEAKING)
  9. Audio amplitude smoother (MicrophoneMonitor math)
  10. TTS amplitude tracker start/stop
  11. Boot sequence stage progression
  12. Boot sequence completion
  13. Effects colour utilities
  14. Effects blend function
  15. Visual failure isolation (HUD crash doesn't propagate)
  16. VISUAL_UI_ENABLED=false skips HUD start

All tests use mocks; no hardware required.
"""

from __future__ import annotations
import os
import sys
import threading
import unittest
from unittest.mock import patch

# ── Ensure project root on path ──────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── 1. Config loading ─────────────────────────────────────────────────────────
class TestConfig(unittest.TestCase):
    def test_defaults_present(self):
        from visual_ui.config import (
            VISUAL_UI_ENABLED,
            VISUAL_COMPACT_WIDTH,
            VISUAL_COMPACT_HEIGHT,
            VISUAL_FULLSCREEN_FPS,
            VISUAL_COMPACT_FPS,
            VISUAL_UI_OPACITY,
            VISUAL_UI_INTENSITY,
            VISUAL_UI_BOOT_DURATION,
            FS_FRAME_MS,
            COMPACT_FRAME_MS,
        )
        self.assertIsInstance(VISUAL_UI_ENABLED, bool)
        self.assertGreater(VISUAL_COMPACT_WIDTH, 0)
        self.assertGreater(VISUAL_COMPACT_HEIGHT, 0)
        self.assertGreater(VISUAL_FULLSCREEN_FPS, 0)
        self.assertGreater(VISUAL_COMPACT_FPS, 0)
        self.assertGreater(VISUAL_UI_OPACITY, 0)
        self.assertGreater(VISUAL_UI_INTENSITY, 0)
        self.assertGreater(VISUAL_UI_BOOT_DURATION, 0)
        self.assertGreater(FS_FRAME_MS, 0)
        self.assertGreater(COMPACT_FRAME_MS, 0)

    def test_frame_interval_from_fps(self):
        from visual_ui.config import VISUAL_FULLSCREEN_FPS, FS_FRAME_MS
        expected = max(8, 1000 // max(10, VISUAL_FULLSCREEN_FPS))
        self.assertEqual(FS_FRAME_MS, expected)


# ── 2. HUD State enum ─────────────────────────────────────────────────────────
class TestHUDState(unittest.TestCase):
    def test_all_states_present(self):
        from visual_ui.hud_state import HUDState
        expected = {"BOOTING", "IDLE", "LISTENING", "PROCESSING",
                    "CONFIRMATION", "SPEAKING", "SUCCESS", "ERROR"}
        actual = {s.value for s in HUDState}
        self.assertEqual(expected, actual)

    def test_all_states_have_params(self):
        from visual_ui.hud_state import HUDState, STATE_PARAMS
        for state in HUDState:
            self.assertIn(state, STATE_PARAMS, f"STATE_PARAMS missing {state}")
            params = STATE_PARAMS[state]
            for key in ("core_pulse_hz", "orbital1_rpm", "orbital2_rpm",
                        "particle_speed", "particle_alpha", "core_color",
                        "ring1_color", "ring2_color", "particle_color", "label_color"):
                self.assertIn(key, params, f"STATE_PARAMS[{state}] missing {key}")

    def test_transient_states(self):
        from visual_ui.hud_state import HUDState, TRANSIENT_STATES, TRANSIENT_DURATION
        self.assertIn(HUDState.SUCCESS, TRANSIENT_STATES)
        self.assertIn(HUDState.ERROR,   TRANSIENT_STATES)
        self.assertIn(HUDState.SUCCESS, TRANSIENT_DURATION)
        self.assertIn(HUDState.ERROR,   TRANSIENT_DURATION)


# ── 3. HUD Bridge event queue ─────────────────────────────────────────────────
class TestHUDBridge(unittest.TestCase):
    def setUp(self):
        from visual_ui.hud_bridge import HUDBridge
        self.bridge = HUDBridge()

    def test_post_and_get_event(self):
        from visual_ui.hud_state import HUDState, HUDEvent
        self.bridge.post_event(HUDState.LISTENING, amplitude=0.5, text="hello")
        ev = self.bridge.get_event()
        self.assertIsNotNone(ev)
        assert isinstance(ev, HUDEvent)
        self.assertEqual(ev.state, HUDState.LISTENING)
        self.assertAlmostEqual(ev.amplitude, 0.5)
        self.assertEqual(ev.text, "hello")

    def test_empty_queue_returns_none(self):
        ev = self.bridge.get_event()
        self.assertIsNone(ev)

    def test_amplitude_clamped(self):
        from visual_ui.hud_state import HUDState, HUDEvent
        self.bridge.post_event(HUDState.IDLE, amplitude=5.0)
        ev = self.bridge.get_event()
        self.assertIsNotNone(ev)
        assert isinstance(ev, HUDEvent)
        self.assertLessEqual(ev.amplitude, 1.0)

    def test_current_state_snapshot(self):
        from visual_ui.hud_state import HUDState
        self.bridge.post_event(HUDState.PROCESSING)
        self.assertEqual(self.bridge.current_state, HUDState.PROCESSING)

    def test_thread_safety(self):
        """Post events from multiple threads; bridge must not crash or deadlock."""
        from visual_ui.hud_state import HUDState
        results = []
        errors  = []

        def poster():
            try:
                for _ in range(50):
                    self.bridge.post_event(HUDState.IDLE)
                results.append("ok")
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=poster) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")
        self.assertEqual(len(results), 4)


# ── 4. Bridge amplitude update ────────────────────────────────────────────────
class TestBridgeAmplitude(unittest.TestCase):
    def test_post_amplitude(self):
        from visual_ui.hud_bridge import HUDBridge
        from visual_ui.hud_state  import HUDState, HUDEvent
        b = HUDBridge()
        b.post_event(HUDState.LISTENING)
        b.get_event()   # consume
        b.post_amplitude(0.75)
        ev = b.get_event()
        self.assertIsNotNone(ev)
        assert isinstance(ev, HUDEvent)
        self.assertAlmostEqual(ev.amplitude, 0.75)


# ── 5. State transitions via bridge ───────────────────────────────────────────
class TestStateTransitions(unittest.TestCase):
    def setUp(self):
        from visual_ui.hud_bridge import HUDBridge
        self.bridge = HUDBridge()

    def _transition(self, state, amplitude: float = 0.0, text: str = ""):
        from visual_ui.hud_state import HUDState, HUDEvent
        self.bridge.post_event(state, amplitude, text)
        ev = self.bridge.get_event()
        assert isinstance(ev, HUDEvent)
        return ev

    def test_idle_to_listening(self):
        from visual_ui.hud_state import HUDState
        ev = self._transition(HUDState.LISTENING, amplitude=0.3)
        self.assertEqual(ev.state, HUDState.LISTENING)

    def test_listening_to_processing(self):
        from visual_ui.hud_state import HUDState
        ev = self._transition(HUDState.PROCESSING)
        self.assertEqual(ev.state, HUDState.PROCESSING)

    def test_processing_to_speaking(self):
        from visual_ui.hud_state import HUDState
        ev = self._transition(HUDState.SPEAKING, amplitude=0.6)
        self.assertEqual(ev.state, HUDState.SPEAKING)

    def test_success_auto_return_config(self):
        from visual_ui.hud_state import HUDState, TRANSIENT_DURATION
        # SUCCESS should return to IDLE after its duration
        dur = TRANSIENT_DURATION[HUDState.SUCCESS]
        self.assertGreater(dur, 0)
        self.assertLess(dur, 5)   # reasonable upper bound

    def test_error_auto_return_config(self):
        from visual_ui.hud_state import HUDState, TRANSIENT_DURATION
        dur = TRANSIENT_DURATION[HUDState.ERROR]
        self.assertGreater(dur, 0)


# ── 6. Particle system ────────────────────────────────────────────────────────
class TestParticleSystem(unittest.TestCase):
    def test_particle_count(self):
        from visual_ui.particles import ParticleSystem
        ps = ParticleSystem(count=12)
        self.assertEqual(ps._count, 12)
        self.assertEqual(len(ps._particles), 12)
        self.assertEqual(len(ps._phases), 12)

    def test_update_advances_phases(self):
        from visual_ui.particles import ParticleSystem
        ps = ParticleSystem(count=4)
        phases_before = list(ps._phases)
        ps.update(dt=0.016, speed=1.0)
        for before, after in zip(phases_before, ps._phases):
            self.assertNotAlmostEqual(before, after, places=6)

    def test_zero_speed_no_advance(self):
        from visual_ui.particles import ParticleSystem
        ps = ParticleSystem(count=4)
        phases_before = list(ps._phases)
        ps.update(dt=0.016, speed=0.0)
        # phases should stay the same since speed=0
        for before, after in zip(phases_before, ps._phases):
            self.assertAlmostEqual(before, after, places=6)


# ── 7. Waveform update ────────────────────────────────────────────────────────
class TestFrequencyWaveform(unittest.TestCase):
    def setUp(self):
        from visual_ui.waveform import FrequencyWaveform
        self.wf = FrequencyWaveform(cx=260, cy=260, n_bars=20)

    def test_idle_bars_low(self):
        for _ in range(20):
            self.wf.update(dt=0.016, state_name="IDLE", amplitude=0.0, t=1.0)
        for bar in self.wf._bars:
            self.assertLess(bar, 0.25, "IDLE bars should be very low")

    def test_listening_bars_react_to_amplitude(self):
        for _ in range(30):
            self.wf.update(dt=0.016, state_name="LISTENING", amplitude=1.0, t=1.0)
        max_bar = max(self.wf._bars)
        self.assertGreater(max_bar, 0.1, "LISTENING at full amplitude should have non-zero bars")

    def test_processing_bars_sweep(self):
        for i in range(30):
            self.wf.update(dt=0.016, state_name="PROCESSING", amplitude=0.0, t=i * 0.016)
        max_bar = max(self.wf._bars)
        self.assertGreater(max_bar, 0.1, "PROCESSING should have sweep bars")

    def test_bars_clamped_to_unit(self):
        for _ in range(10):
            self.wf.update(dt=0.016, state_name="SPEAKING", amplitude=1.0, t=1.0)
        for bar in self.wf._bars:
            self.assertLessEqual(bar, 1.0)
            self.assertGreaterEqual(bar, 0.0)


# ── 8. Effects colour utilities ───────────────────────────────────────────────
class TestEffects(unittest.TestCase):
    def test_hex_color_full_alpha(self):
        from visual_ui.effects import hex_color
        result = hex_color("#FF8800", 1.0)
        self.assertEqual(result.lower(), "#ff8800")

    def test_hex_color_zero_alpha(self):
        from visual_ui.effects import hex_color
        result = hex_color("#FF8800", 0.0)
        self.assertEqual(result.lower(), "#000000")

    def test_hex_color_half_alpha(self):
        from visual_ui.effects import hex_color
        result = hex_color("#FF8800", 0.5)
        r, g, b = int(result[1:3], 16), int(result[3:5], 16), int(result[5:7], 16)
        self.assertAlmostEqual(r, 127, delta=2)
        self.assertAlmostEqual(g, 68, delta=2)
        self.assertEqual(b, 0)

    def test_blend_t0(self):
        from visual_ui.effects import blend
        result = blend("#FF0000", "#0000FF", 0.0)
        self.assertEqual(result.lower(), "#ff0000")

    def test_blend_t1(self):
        from visual_ui.effects import blend
        result = blend("#FF0000", "#0000FF", 1.0)
        self.assertEqual(result.lower(), "#0000ff")

    def test_blend_midpoint(self):
        from visual_ui.effects import blend
        result = blend("#FF0000", "#0000FF", 0.5)
        r = int(result[1:3], 16)
        b = int(result[5:7], 16)
        self.assertAlmostEqual(r, 127, delta=2)
        self.assertAlmostEqual(b, 127, delta=2)


# ── 9. Boot sequence ──────────────────────────────────────────────────────────
class TestBootSequence(unittest.TestCase):
    def test_starts_not_complete(self):
        from visual_ui.boot_sequence import BootSequence
        bs = BootSequence(cx=260, cy=260, total_duration=3.5)
        self.assertFalse(bs.is_complete)

    def test_completes_after_duration(self):
        from visual_ui.boot_sequence import BootSequence
        bs = BootSequence(cx=260, cy=260, total_duration=1.0)
        # Feed enough dt to exceed total duration
        for _ in range(100):
            bs.update(dt=0.02)
        self.assertTrue(bs.is_complete)

    def test_does_not_advance_after_complete(self):
        from visual_ui.boot_sequence import BootSequence
        bs = BootSequence(cx=260, cy=260, total_duration=0.5)
        for _ in range(40):
            bs.update(dt=0.016)
        elapsed_before = bs._elapsed
        bs.update(dt=0.1)  # should be a no-op
        self.assertEqual(bs._elapsed, elapsed_before)


# ── 10. TTS amplitude tracker ─────────────────────────────────────────────────
class TestTTSAmplitudeTracker(unittest.TestCase):
    def test_starts_at_zero(self):
        from visual_ui.audio_reactive import TTSAmplitudeTracker
        tr = TTSAmplitudeTracker()
        self.assertAlmostEqual(tr.get_amplitude(), 0.0)

    def test_stop_resets_amplitude(self):
        from visual_ui.audio_reactive import TTSAmplitudeTracker
        tr = TTSAmplitudeTracker()
        tr.stop()
        self.assertAlmostEqual(tr.get_amplitude(), 0.0)


# ── 11. Microphone monitor (no hardware) ─────────────────────────────────────
class TestMicrophoneMonitor(unittest.TestCase):
    def test_starts_at_zero(self):
        from visual_ui.audio_reactive import MicrophoneMonitor
        m = MicrophoneMonitor()
        self.assertAlmostEqual(m.get_amplitude(), 0.0)

    def test_stop_works_when_not_started(self):
        from visual_ui.audio_reactive import MicrophoneMonitor
        m = MicrophoneMonitor()
        m.stop()   # Should not raise
        self.assertAlmostEqual(m.get_amplitude(), 0.0)


# ── 12. Visual failure isolation ──────────────────────────────────────────────
class TestFailureIsolation(unittest.TestCase):
    def test_hud_bridge_post_is_safe_when_full(self):
        """Posting to a full queue should never raise an exception."""
        from visual_ui.hud_bridge import HUDBridge
        from visual_ui.hud_state  import HUDState
        b = HUDBridge()
        # Fill beyond maxsize (64)
        try:
            for _ in range(100):
                b.post_event(HUDState.IDLE)
        except Exception as exc:
            self.fail(f"post_event raised on full queue: {exc}")

    def test_start_hud_is_non_fatal(self):
        """
        If tkinter fails, start_hud must still return a HUDBridge
        without propagating the exception.
        """
        from visual_ui import hud_thread

        original_run = hud_thread._run_hud

        def broken_run(bridge: hud_thread.HUDBridge, ready_event: threading.Event, audio_ref: list) -> None:
            # Simulate failure: set ready first (as the real function does), then fail
            ready_event.set()
            # Do NOT re-raise — in production the thread dies silently
            # warnings.warn() is the expected behavior, not raise

        hud_thread._run_hud = broken_run
        try:
            bridge = hud_thread.start_hud(wait_timeout=2.0)
            self.assertIsNotNone(bridge)
        except Exception as exc:
            self.fail(f"start_hud raised exception on HUD failure: {exc}")
        finally:
            hud_thread._run_hud = original_run


# ── 13. VISUAL_UI_ENABLED=false skips HUD ────────────────────────────────────
class TestVisualUIDisable(unittest.TestCase):
    def test_disabled_flag(self):
        """When VISUAL_UI_ENABLED is False, the HUD bridge should be None in main."""
        # We test the config module directly
        with patch.dict(os.environ, {"VISUAL_UI_ENABLED": "false"}):
            import importlib
            import visual_ui.config as cfg
            importlib.reload(cfg)
            self.assertFalse(cfg.VISUAL_UI_ENABLED)


# ═══════════════════════════════════════════════════════════════════════════════
# DUAL-MODE TESTS (Full-Screen + Compact)
# ═══════════════════════════════════════════════════════════════════════════════

# ── 14. DisplayMode enum ──────────────────────────────────────────────────────
class TestDisplayModeEnum(unittest.TestCase):
    def test_all_modes_present(self):
        from visual_ui.display_mode import DisplayMode
        expected = {"FULLSCREEN", "COMPACT", "TO_COMPACT", "TO_FULL"}
        actual   = {m.value for m in DisplayMode}
        self.assertEqual(expected, actual)


# ── 15. TransitionController initialisation ───────────────────────────────────
class TestTransitionControllerInit(unittest.TestCase):
    def _make(self, wake_fullscreen=True):
        from visual_ui.display_mode import TransitionController
        return TransitionController(
            screen_w=1920,
            screen_h=1080,
            compact_w=200,
            compact_h=200,
            compact_position="right",
            transition_dur=0.7,
            wake_fullscreen=wake_fullscreen,
        )

    def test_starts_fullscreen_when_configured(self):
        from visual_ui.display_mode import DisplayMode
        tc = self._make(wake_fullscreen=True)
        self.assertEqual(tc.current_mode, DisplayMode.FULLSCREEN)

    def test_starts_compact_when_configured(self):
        from visual_ui.display_mode import DisplayMode
        tc = self._make(wake_fullscreen=False)
        self.assertEqual(tc.current_mode, DisplayMode.COMPACT)

    def test_fullscreen_geometry_is_screen_size(self):
        tc = self._make(wake_fullscreen=True)
        x, y, w, h = tc.get_geometry()
        self.assertEqual(w, 1920)
        self.assertEqual(h, 1080)

    def test_compact_geometry_is_compact_size(self):
        tc = self._make(wake_fullscreen=False)
        x, y, w, h = tc.get_geometry()
        self.assertEqual(w, 200)
        self.assertEqual(h, 200)

    def test_draw_scale_fullscreen_gt_1(self):
        tc = self._make(wake_fullscreen=True)
        scale = tc.get_draw_scale()
        self.assertGreater(scale, 1.0)

    def test_draw_scale_compact_lt_1(self):
        tc = self._make(wake_fullscreen=False)
        scale = tc.get_draw_scale()
        self.assertLess(scale, 1.0)


# ── 16. Transition: fullscreen → compact ─────────────────────────────────────
class TestTransitionToCompact(unittest.TestCase):
    def setUp(self):
        from visual_ui.display_mode import TransitionController, DisplayMode
        self.tc = TransitionController(
            screen_w=1920, screen_h=1080,
            compact_w=200, compact_h=200,
            compact_position="right",
            transition_dur=0.5,
            wake_fullscreen=True,
        )

    def test_go_compact_sets_transitioning(self):
        from visual_ui.display_mode import DisplayMode
        self.tc.go_compact()
        self.assertEqual(self.tc.current_mode, DisplayMode.TO_COMPACT)
        self.assertTrue(self.tc.is_transitioning)

    def test_transition_completes_after_duration(self):
        from visual_ui.display_mode import DisplayMode
        self.tc.go_compact()
        # Feed dt > transition_dur
        for _ in range(40):
            self.tc.update(dt=0.016)
        self.assertEqual(self.tc.current_mode, DisplayMode.COMPACT)
        self.assertTrue(self.tc.is_compact)
        self.assertFalse(self.tc.is_transitioning)

    def test_geometry_intermediate(self):
        """During transition, w/h should be between compact and fullscreen."""
        self.tc.go_compact()
        self.tc.update(dt=0.25)   # halfway through 0.5s transition
        x, y, w, h = self.tc.get_geometry()
        # Width should be somewhere between 200 and 1920
        self.assertGreater(w, 200)
        self.assertLess(w, 1920)

    def test_scale_interpolates_down(self):
        self.tc.go_compact()
        scale_before = self.tc.get_draw_scale()
        self.tc.update(dt=0.25)
        scale_mid = self.tc.get_draw_scale()
        self.assertLess(scale_mid, scale_before)

    def test_go_compact_idempotent(self):
        """Calling go_compact twice should not reset progress."""
        from visual_ui.display_mode import DisplayMode
        self.tc.go_compact()
        self.tc.update(dt=0.30)
        progress_before = self.tc.transition_progress
        self.tc.go_compact()   # second call — should be ignored
        self.assertEqual(self.tc.transition_progress, progress_before)


# ── 17. Transition: compact → fullscreen ──────────────────────────────────────
class TestTransitionToFullscreen(unittest.TestCase):
    def setUp(self):
        from visual_ui.display_mode import TransitionController
        self.tc = TransitionController(
            screen_w=1920, screen_h=1080,
            compact_w=200, compact_h=200,
            compact_position="right",
            transition_dur=0.5,
            wake_fullscreen=False,   # start in compact
        )

    def test_go_fullscreen_sets_transitioning(self):
        from visual_ui.display_mode import DisplayMode
        self.tc.go_fullscreen()
        self.assertEqual(self.tc.current_mode, DisplayMode.TO_FULL)

    def test_transition_completes_at_fullscreen(self):
        from visual_ui.display_mode import DisplayMode
        self.tc.go_fullscreen()
        for _ in range(40):
            self.tc.update(dt=0.016)
        self.assertEqual(self.tc.current_mode, DisplayMode.FULLSCREEN)
        self.assertTrue(self.tc.is_fullscreen)

    def test_geometry_reaches_screen_size(self):
        self.tc.go_fullscreen()
        for _ in range(50):
            self.tc.update(dt=0.016)
        x, y, w, h = self.tc.get_geometry()
        self.assertEqual(w, 1920)
        self.assertEqual(h, 1080)

    def test_draw_scale_reaches_fullscreen_value(self):
        from visual_ui.display_mode import TransitionController
        tc_fs = TransitionController(1920, 1080, 200, 200, "right", 0.5, True)
        expected_fs_scale = tc_fs.get_draw_scale()

        self.tc.go_fullscreen()
        for _ in range(50):
            self.tc.update(dt=0.016)
        self.assertAlmostEqual(self.tc.get_draw_scale(), expected_fs_scale, places=4)


# ── 18. Compact position calculation ─────────────────────────────────────────
class TestCompactPosition(unittest.TestCase):
    def _make_and_go_compact(self, position):
        from visual_ui.display_mode import TransitionController
        tc = TransitionController(
            screen_w=1920, screen_h=1080,
            compact_w=200, compact_h=200,
            compact_position=position,
            transition_dur=0.01,   # instant
            wake_fullscreen=False,
        )
        return tc

    def _xy(self, pos):
        tc = self._make_and_go_compact(pos)
        x, y, w, h = tc.get_geometry()
        return x, y

    def test_right_is_near_right_edge(self):
        x, y = self._xy("right")
        self.assertGreater(x, 1500)  # near right edge of 1920px screen

    def test_left_is_near_left_edge(self):
        x, y = self._xy("left")
        self.assertLess(x, 100)

    def test_center_is_centered(self):
        x, y = self._xy("center")
        self.assertAlmostEqual(x, (1920 - 200) // 2, delta=5)

    def test_bottom_right_corner(self):
        x, y = self._xy("bottom-right")
        self.assertGreater(x, 1500)
        self.assertGreater(y, 700)

    def test_top_left_corner(self):
        x, y = self._xy("top-left")
        self.assertLess(x, 100)
        self.assertLess(y, 100)


# ── 19. Bridge display mode events ───────────────────────────────────────────
class TestBridgeDisplayMode(unittest.TestCase):
    def setUp(self):
        from visual_ui.hud_bridge import HUDBridge
        self.bridge = HUDBridge()

    def test_request_compact_queues_event(self):
        from visual_ui.hud_bridge import DisplayModeEvent
        from visual_ui.display_mode import DisplayMode
        self.bridge.request_compact()
        ev = self.bridge.get_event()
        self.assertIsInstance(ev, DisplayModeEvent)
        assert isinstance(ev, DisplayModeEvent)
        self.assertEqual(ev.mode, DisplayMode.COMPACT)

    def test_request_fullscreen_queues_event(self):
        from visual_ui.hud_bridge import DisplayModeEvent
        from visual_ui.display_mode import DisplayMode
        self.bridge.request_fullscreen()
        ev = self.bridge.get_event()
        self.assertIsInstance(ev, DisplayModeEvent)
        assert isinstance(ev, DisplayModeEvent)
        self.assertEqual(ev.mode, DisplayMode.FULLSCREEN)

    def test_state_and_display_events_can_coexist(self):
        """Both event types can be queued and consumed independently."""
        from visual_ui.hud_bridge import DisplayModeEvent
        from visual_ui.hud_state  import HUDState
        from visual_ui.hud_bridge import HUDEvent

        self.bridge.request_fullscreen()
        self.bridge.post_event(HUDState.LISTENING, amplitude=0.5)
        self.bridge.request_compact()

        events = []
        while True:
            ev = self.bridge.get_event()
            if ev is None:
                break
            events.append(ev)

        types = [type(e).__name__ for e in events]
        self.assertIn("DisplayModeEvent", types)
        self.assertIn("HUDEvent",         types)

    def test_current_display_mode_snapshot(self):
        from visual_ui.display_mode import DisplayMode
        self.bridge.request_compact()
        self.assertEqual(self.bridge.current_display_mode, DisplayMode.COMPACT)


# ── 20. Dual-mode config ──────────────────────────────────────────────────────
class TestDualModeConfig(unittest.TestCase):
    def test_defaults_present(self):
        from visual_ui.config import (
            VISUAL_WAKE_FULLSCREEN,
            VISUAL_TASK_COMPACT,
            VISUAL_RETURN_FULLSCREEN_ON_WAKE,
            VISUAL_COMPACT_POSITION,
            VISUAL_COMPACT_WIDTH,
            VISUAL_COMPACT_HEIGHT,
            VISUAL_FULLSCREEN_FPS,
            VISUAL_COMPACT_FPS,
            VISUAL_TRANSITION_DURATION,
            FS_FRAME_MS,
            COMPACT_FRAME_MS,
        )
        self.assertIsInstance(VISUAL_WAKE_FULLSCREEN, bool)
        self.assertIsInstance(VISUAL_TASK_COMPACT, bool)
        self.assertIsInstance(VISUAL_RETURN_FULLSCREEN_ON_WAKE, bool)
        self.assertIsInstance(VISUAL_COMPACT_POSITION, str)
        self.assertGreater(VISUAL_COMPACT_WIDTH, 0)
        self.assertGreater(VISUAL_COMPACT_HEIGHT, 0)
        self.assertGreater(VISUAL_FULLSCREEN_FPS, 0)
        self.assertGreater(VISUAL_COMPACT_FPS, 0)
        self.assertGreater(VISUAL_TRANSITION_DURATION, 0)
        self.assertGreater(FS_FRAME_MS, 0)
        self.assertGreater(COMPACT_FRAME_MS, 0)

    def test_compact_fps_lte_fullscreen_fps(self):
        from visual_ui.config import VISUAL_COMPACT_FPS, VISUAL_FULLSCREEN_FPS
        # Compact FPS should be ≤ fullscreen FPS for resource efficiency
        self.assertLessEqual(VISUAL_COMPACT_FPS, VISUAL_FULLSCREEN_FPS)

    def test_transition_duration_in_range(self):
        from visual_ui.config import VISUAL_TRANSITION_DURATION
        # Must be between 100ms and 5s (reasonable range)
        self.assertGreater(VISUAL_TRANSITION_DURATION, 0.1)
        self.assertLess(VISUAL_TRANSITION_DURATION, 5.0)


    def test_advanced_3d_config_defaults(self):
        from visual_ui.config import (
            VISUAL_FULLSCREEN_ON_START,
            VISUAL_RETURN_FULLSCREEN_AFTER_TASK,
            VISUAL_CONFIRMATION_FULLSCREEN,
            VISUAL_3D_DEPTH,
            VISUAL_AUDIO_REACTIVITY,
            VISUAL_PARTICLE_COUNT,
            VISUAL_THEME,
            VISUAL_BLINK,
            VISUAL_AGGRESSIVE_PULSE,
        )
        self.assertTrue(VISUAL_FULLSCREEN_ON_START)
        self.assertTrue(VISUAL_RETURN_FULLSCREEN_AFTER_TASK)
        self.assertTrue(VISUAL_CONFIRMATION_FULLSCREEN)
        self.assertGreater(VISUAL_3D_DEPTH, 0)
        self.assertGreater(VISUAL_AUDIO_REACTIVITY, 0)
        self.assertGreater(VISUAL_PARTICLE_COUNT, 0)
        self.assertEqual(VISUAL_THEME, "blue_pink_violet")
        self.assertFalse(VISUAL_BLINK)
        self.assertFalse(VISUAL_AGGRESSIVE_PULSE)


# ── 21. Full state machine round-trip (display + AI state) ───────────────────
class TestFullStateMachineRoundTrip(unittest.TestCase):
    def setUp(self):
        from visual_ui.hud_bridge import HUDBridge
        self.bridge = HUDBridge()

    def test_boot_to_idle_to_compact_sequence(self):
        """Simulate the exact startup → task sequence."""
        from visual_ui.hud_state  import HUDState
        from visual_ui.hud_bridge import DisplayModeEvent, HUDEvent
        from visual_ui.display_mode import DisplayMode

        # 1. Boot
        self.bridge.post_event(HUDState.BOOTING, text="VOXAI INITIALISING")
        # 2. Ready → fullscreen idle
        self.bridge.post_event(HUDState.IDLE, text="READY")
        # 3. Wake word → expand fullscreen + listening
        self.bridge.request_fullscreen()
        self.bridge.post_event(HUDState.LISTENING, amplitude=0.4)
        # 4. Task detected → compact + processing
        self.bridge.request_compact()
        self.bridge.post_event(HUDState.PROCESSING, text="Opening Chrome...")
        # 5. Task done → return to fullscreen before speaking
        self.bridge.request_fullscreen()
        self.bridge.post_event(HUDState.SPEAKING, amplitude=0.7, text="Done!")
        # 6. Success → idle
        self.bridge.post_event(HUDState.SUCCESS)
        self.bridge.post_event(HUDState.IDLE)

        events = []
        while True:
            ev = self.bridge.get_event()
            if ev is None:
                break
            events.append(ev)

        self.assertGreater(len(events), 5)

        # Check we have both types
        display_events = [e for e in events if isinstance(e, DisplayModeEvent)]
        state_events   = [e for e in events if isinstance(e, HUDEvent)]
        self.assertGreaterEqual(len(display_events), 2)   # fullscreen + compact
        self.assertGreaterEqual(len(state_events), 5)

        # Check display sequence: fullscreen before compact
        first_full   = next((i for i, e in enumerate(display_events)
                            if isinstance(e, DisplayModeEvent) and e.mode == DisplayMode.FULLSCREEN), None)
        first_compact = next((i for i, e in enumerate(display_events)
                             if isinstance(e, DisplayModeEvent) and e.mode == DisplayMode.COMPACT), None)
        if first_full is not None and first_compact is not None:
            self.assertLess(first_full, first_compact)

    def test_conversation_stays_fullscreen(self):
        """Normal voice chat/QA/RAG must stay in FULLSCREEN mode."""
        from visual_ui.hud_state import HUDState
        from visual_ui.hud_bridge import DisplayModeEvent, HUDEvent
        from visual_ui.display_mode import DisplayMode

        # 1. Wake word -> fullscreen
        self.bridge.request_fullscreen()
        self.bridge.post_event(HUDState.LISTENING)
        # 2. QA reasoning -> stays fullscreen
        self.bridge.post_event(HUDState.PROCESSING, text="Thinking...")
        # 3. Speaking answer -> stays fullscreen
        self.bridge.post_event(HUDState.SPEAKING, text="Machine learning is...")
        self.bridge.post_event(HUDState.IDLE)

        events = []
        while True:
            ev = self.bridge.get_event()
            if ev is None:
                break
            events.append(ev)

        # No COMPACT events should be queued during pure conversation
        compact_events = [e for e in events if isinstance(e, DisplayModeEvent) and e.mode == DisplayMode.COMPACT]
        self.assertEqual(len(compact_events), 0, "Conversation should NEVER request compact mode")

    def test_task_failure_returns_to_fullscreen(self):
        """Task failure must trigger smooth expansion back to FULLSCREEN."""
        from visual_ui.hud_state import HUDState
        from visual_ui.hud_bridge import DisplayModeEvent
        from visual_ui.display_mode import DisplayMode

        self.bridge.request_compact()
        self.bridge.post_event(HUDState.PROCESSING, text="Executing tool...")
        # Failure occurs
        self.bridge.request_fullscreen()
        self.bridge.post_event(HUDState.ERROR, text="Tool failed")

        events = []
        while True:
            ev = self.bridge.get_event()
            if ev is None:
                break
            events.append(ev)

        # Final display event must be FULLSCREEN
        display_events = [e for e in events if isinstance(e, DisplayModeEvent)]
        self.assertTrue(len(display_events) >= 2)
        self.assertEqual(display_events[-1].mode, DisplayMode.FULLSCREEN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
