"""
MuthuAI Phase 2 — tools/windows/system.py

Deterministic Windows system tools: Volume, Date/Time, Control Panel, Settings, Task Manager, Command Prompt.
Uses pycaw / ctypes / pyautogui for volume and native Windows launchers.
"""

from __future__ import annotations
import os
import subprocess
from datetime import datetime

from tools.base import BaseTool, ToolResult, PermissionLevel
from utils.logger import get_logger

log = get_logger("muthuai.tools.system")


# ── Volume Utilities ──────────────────────────────────────────

def _change_volume(delta_step: int) -> str:
    """Change system volume by delta_step percent units (positive or negative)."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        import comtypes
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        current = volume.GetMasterVolumeLevelScalar()
        new_vol = max(0.0, min(1.0, current + (delta_step / 100.0)))
        volume.SetMasterVolumeLevelScalar(new_vol, None)
        pct = int(new_vol * 100)
        return f"Volume set to {pct}%."
    except Exception:
        # Fallback to direct Windows Virtual Key events
        try:
            import ctypes
            VK_VOLUME_UP = 0xAF
            VK_VOLUME_DOWN = 0xAE
            vk = VK_VOLUME_UP if delta_step > 0 else VK_VOLUME_DOWN
            steps = max(1, abs(delta_step) // 2)
            for _ in range(steps):
                ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
                ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
            return f"Volume {'increased' if delta_step > 0 else 'decreased'}."
        except Exception as exc:
            return f"Could not adjust volume: {exc}"


def _toggle_mute() -> str:
    """Toggle mute on audio speakers."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        import comtypes
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        is_muted = volume.GetMute()
        volume.SetMute(0 if is_muted else 1, None)
        return "Audio unmuted." if is_muted else "Audio muted."
    except Exception:
        try:
            import ctypes
            VK_VOLUME_MUTE = 0xAD
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
            return "Volume mute toggled."
        except Exception as exc:
            return f"Could not toggle mute: {exc}"



# ── Tool Definitions ──────────────────────────────────────────

class VolumeUpTool(BaseTool):
    name = "volume_up"
    description = "Increase the Windows system master volume by a specified step (default 10%)."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "step": {"type": "integer", "default": 10, "description": "Percentage step to increase volume (1-50)."}
        },
        "required": []
    }

    def execute(self, step: int = 10, **kwargs) -> ToolResult:
        msg = _change_volume(abs(step))
        return ToolResult.ok(msg)


class VolumeDownTool(BaseTool):
    name = "volume_down"
    description = "Decrease the Windows system master volume by a specified step (default 10%)."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "step": {"type": "integer", "default": 10, "description": "Percentage step to decrease volume (1-50)."}
        },
        "required": []
    }

    def execute(self, step: int = 10, **kwargs) -> ToolResult:
        msg = _change_volume(-abs(step))
        return ToolResult.ok(msg)


class MuteVolumeTool(BaseTool):
    name = "mute_volume"
    description = "Mute or unmute the system audio."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        msg = _toggle_mute()
        return ToolResult.ok(msg)


class GetTimeTool(BaseTool):
    name = "get_time"
    description = "Get the current time on the computer."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        now_str = datetime.now().strftime("%I:%M %p")
        return ToolResult.ok(f"The current time is {now_str}.", time=now_str)


class GetDateTool(BaseTool):
    name = "get_date"
    description = "Get today's date."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        date_str = datetime.now().strftime("%A, %B %d, %Y")
        return ToolResult.ok(f"Today is {date_str}.", date=date_str)


class OpenCommandPromptTool(BaseTool):
    name = "open_command_prompt"
    description = "Open Windows Command Prompt (CMD)."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        try:
            subprocess.Popen("cmd.exe", shell=True)
            return ToolResult.ok("Command Prompt opened.")
        except Exception as exc:
            return ToolResult.fail(f"Could not open Command Prompt: {exc}")


class OpenControlPanelTool(BaseTool):
    name = "open_control_panel"
    description = "Open Windows Control Panel."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        try:
            subprocess.Popen("control.exe", shell=True)
            return ToolResult.ok("Control Panel opened.")
        except Exception as exc:
            return ToolResult.fail(f"Could not open Control Panel: {exc}")


class OpenSettingsTool(BaseTool):
    name = "open_settings"
    description = "Open Windows Settings."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        try:
            os.system("start ms-settings:")
            return ToolResult.ok("Windows Settings opened.")
        except Exception as exc:
            return ToolResult.fail(f"Could not open Windows Settings: {exc}")


class OpenTaskManagerTool(BaseTool):
    name = "open_task_manager"
    description = "Open Windows Task Manager."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        try:
            subprocess.Popen("taskmgr.exe", shell=True)
            return ToolResult.ok("Task Manager opened.")
        except Exception as exc:
            return ToolResult.fail(f"Could not open Task Manager: {exc}")
