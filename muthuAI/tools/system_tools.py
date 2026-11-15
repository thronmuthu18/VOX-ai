"""
MuthuAI — tools/system_tools.py
Windows system-level tools: volume, info, screenshot, and media controls.
"""

import os
import platform
import subprocess
import ctypes
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from utils.helpers import ok, fail, expand_path, safe_filename
from utils.logger import get_logger

log = get_logger(__name__)

# Windows Virtual-Key codes
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3


def _parse_int(val: Any, default: int = 50, min_val: int = 0, max_val: int = 100) -> int:
    """Safely parse an integer from int, float, or string (including percentage signs)."""
    if val is None:
        return default
    try:
        if isinstance(val, str):
            val = val.replace("%", "").strip()
        num = round(float(val))
        return max(min_val, min(max_val, num))
    except (ValueError, TypeError):
        return default


def _send_key_event(vk_code: int, times: int = 1) -> None:
    """Send a Windows keyboard event using user32.keybd_event."""
    try:
        for _ in range(max(1, times)):
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
    except Exception as exc:
        log.debug("Failed to send key event 0x%X: %s", vk_code, exc)


def _get_volume_endpoint() -> Any:
    """Retrieve Windows master volume endpoint interface with multi-version pycaw support."""
    try:
        import comtypes
        try:
            comtypes.CoInitialize()
        except Exception:
            pass

        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER

        device: Any = AudioUtilities.GetSpeakers()
        if device is None:
            return None

        # 1. Modern pycaw (AudioDevice.EndpointVolume property)
        if hasattr(device, "EndpointVolume") and device.EndpointVolume is not None:
            return device.EndpointVolume

        # 2. Modern pycaw internal device Activate
        if hasattr(device, "_dev") and hasattr(device._dev, "Activate"):
            interface = device._dev.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))

        # 3. Direct Activate on AudioDevice
        if hasattr(device, "Activate"):
            interface = device.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
            if hasattr(interface, "QueryInterface"):
                try:
                    return interface.QueryInterface(IAudioEndpointVolume)
                except Exception:
                    pass
            return cast(interface, POINTER(IAudioEndpointVolume))

        # 4. Endpoint property Activate
        if hasattr(device, "Endpoint") and hasattr(device.Endpoint, "Activate"):
            interface = device.Endpoint.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
            if hasattr(interface, "QueryInterface"):
                try:
                    return interface.QueryInterface(IAudioEndpointVolume)
                except Exception:
                    pass
            return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as exc:
        log.debug("pycaw audio endpoint unavailable: %s", exc)
    return None


def volume_up(step: Union[int, str] = 5, **kwargs) -> dict:
    """Increase system volume by 'step' percent units."""
    step_val = _parse_int(step, default=5, min_val=1, max_val=100)
    return _change_volume(step_val, direction="up")


def volume_down(step: Union[int, str] = 5, **kwargs) -> dict:
    """Decrease system volume by 'step' percent units."""
    step_val = _parse_int(step, default=5, min_val=1, max_val=100)
    return _change_volume(step_val, direction="down")


def mute_volume(**kwargs) -> dict:
    """Mute system audio."""
    vol: Any = _get_volume_endpoint()
    if vol:
        try:
            vol.SetMute(1, None)
            return ok("Volume muted.", data={"muted": True})
        except Exception as exc:
            log.debug("pycaw mute failed: %s", exc)

    # Fallback to Windows virtual key
    _send_key_event(VK_VOLUME_MUTE)
    return ok("Volume muted.", data={"muted": True})


def unmute_volume(**kwargs) -> dict:
    """Unmute system audio."""
    vol: Any = _get_volume_endpoint()
    if vol:
        try:
            vol.SetMute(0, None)
            return ok("Volume unmuted.", data={"muted": False})
        except Exception as exc:
            log.debug("pycaw unmute failed: %s", exc)

    # Fallback: sending volume up/down unmutes Windows without toggling
    _send_key_event(VK_VOLUME_UP)
    _send_key_event(VK_VOLUME_DOWN)
    return ok("Volume unmuted.", data={"muted": False})


def set_volume(level: Union[int, str] = 50, **kwargs) -> dict:
    """Set system master volume to an exact percentage (0-100)."""
    target = _parse_int(level, default=50, min_val=0, max_val=100)
    vol: Any = _get_volume_endpoint()
    if vol:
        try:
            vol.SetMasterVolumeLevelScalar(target / 100.0, None)
            try:
                # If target volume > 0 and system is muted, unmute
                if target > 0 and hasattr(vol, "GetMute") and vol.GetMute():
                    vol.SetMute(0, None)
            except Exception:
                pass
            return ok(f"Volume set to {target}%.", data={"volume": target})
        except Exception as exc:
            log.debug("pycaw set volume failed: %s", exc)

    # Fallback: Send volume keys
    vk = VK_VOLUME_UP if target > 50 else VK_VOLUME_DOWN
    steps = max(1, abs(target - 50) // 2)
    _send_key_event(vk, times=steps)
    return ok(f"Volume set to {target}%.", data={"volume": target})


def _change_volume(step: int, direction: str) -> dict:
    """Internal helper to increase or decrease volume."""
    vol: Any = _get_volume_endpoint()
    if vol:
        try:
            current = vol.GetMasterVolumeLevelScalar()
            delta = step / 100.0
            new_vol = min(1.0, current + delta) if direction == "up" else max(0.0, current - delta)
            vol.SetMasterVolumeLevelScalar(new_vol, None)
            if direction == "up" and hasattr(vol, "GetMute") and vol.GetMute():
                try:
                    vol.SetMute(0, None)
                except Exception:
                    pass
            pct = round(new_vol * 100)
            return ok(f"Volume {'increased' if direction == 'up' else 'decreased'} to {pct}%.", data={"volume": pct})
        except Exception as exc:
            log.debug("pycaw change volume failed: %s", exc)

    # Fallback: use Windows keybd_event
    vk = VK_VOLUME_UP if direction == "up" else VK_VOLUME_DOWN
    steps = max(1, step // 2)
    _send_key_event(vk, times=steps)
    return ok(f"Volume {'increased' if direction == 'up' else 'decreased'}.")


def _nircmd_volume(cmd: str) -> dict:
    """Execute NirCmd audio command if nircmd utility is available."""
    if not cmd:
        return fail("NirCmd command cannot be empty.")
    try:
        subprocess.run(["nircmd.exe", *cmd.split()], check=True, timeout=5)
        return ok("Volume command executed.")
    except Exception as exc:
        return fail(f"Volume command failed: {exc}")


# ── System Information ────────────────────────────────────────

def get_system_info(**kwargs) -> dict:
    """Return basic Windows system information (OS, CPU, RAM, Disk, Uptime)."""
    info: dict[str, Any] = {
        "os": platform.system(),
        "os_version": platform.version(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "python_version": platform.python_version(),
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        import psutil  # type: ignore[import-untyped,import-not-found]
        info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        vm = psutil.virtual_memory()
        info["ram_percent"] = vm.percent
        info["ram_total_gb"] = round(vm.total / (1024 ** 3), 2)
        info["ram_available_gb"] = round(vm.available / (1024 ** 3), 2)

        # Disk usage on Windows root drive
        drive = os.environ.get("SystemDrive", "C:") + "\\"
        try:
            disk = psutil.disk_usage(drive)
            info["disk_percent"] = disk.percent
            info["disk_free_gb"] = round(disk.free / (1024 ** 3), 2)
            info["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
        except Exception:
            disk = psutil.disk_usage(Path.home().anchor or "/")
            info["disk_percent"] = disk.percent

        # Battery if available
        if hasattr(psutil, "sensors_battery"):
            batt = psutil.sensors_battery()
            if batt:
                info["battery_percent"] = round(batt.percent, 1)
                info["power_plugged"] = batt.power_plugged

    except (ImportError, Exception) as exc:
        log.debug("psutil info collection skipped: %s", exc)

    return ok("System info retrieved.", data=info)


# ── Screenshot ────────────────────────────────────────────────

def take_screenshot(
    save_dir: str = "~\\Desktop",
    filename: str = "",
    file_name: str = "",
    **kwargs,
) -> dict:
    """Capture the full screen and save to the specified directory or Desktop."""
    try:
        from utils.helpers import expand_path, safe_filename

        raw_filename = filename or file_name or kwargs.get("name") or ""
        if raw_filename:
            clean_filename = safe_filename(raw_filename, extension=".png")
            if not clean_filename.lower().endswith(".png"):
                clean_filename += ".png"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_filename = f"MuthuAI_screenshot_{timestamp}.png"

        target_dir = expand_path(save_dir)
        # If save_dir is accidentally a full file path
        if target_dir.suffix.lower() in (".png", ".jpg", ".jpeg"):
            dest = target_dir
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            dest = target_dir / clean_filename

        # Attempt capture via pyautogui or PIL ImageGrab
        img = None
        try:
            import pyautogui  # type: ignore[import-untyped,import-not-found]
            img = pyautogui.screenshot()
        except Exception:
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
            except Exception as exc:
                log.debug("ImageGrab failed: %s", exc)

        if img is not None:
            img.save(str(dest))
            return ok(f"Screenshot saved to {dest}.", data={"path": str(dest), "filename": dest.name})
        else:
            return fail("Screenshot capture failed: display capture unavailable.")

    except Exception as exc:
        return fail(f"Screenshot failed: {exc}", error=str(exc))


# ── Stop / Pause / Media Controls ─────────────────────────────

def stop_media(**kwargs) -> dict:
    """Send media stop key."""
    try:
        import pyautogui  # type: ignore[import-untyped,import-not-found]
        pyautogui.press("stop")
        return ok("Media stopped.")
    except Exception:
        pass

    try:
        _send_key_event(VK_MEDIA_STOP)
        return ok("Media stopped.")
    except Exception as exc:
        return fail(str(exc))


def pause_media(**kwargs) -> dict:
    """Send media play/pause key."""
    try:
        import pyautogui  # type: ignore[import-untyped,import-not-found]
        pyautogui.press("playpause")
        return ok("Media paused/resumed.")
    except Exception:
        pass

    try:
        _send_key_event(VK_MEDIA_PLAY_PAUSE)
        return ok("Media paused/resumed.")
    except Exception as exc:
        return fail(str(exc))


def next_media(**kwargs) -> dict:
    """Skip to next media track."""
    try:
        import pyautogui  # type: ignore[import-untyped,import-not-found]
        pyautogui.press("nexttrack")
        return ok("Next track skipped.")
    except Exception:
        pass

    try:
        _send_key_event(VK_MEDIA_NEXT_TRACK)
        return ok("Next track skipped.")
    except Exception as exc:
        return fail(str(exc))


def prev_media(**kwargs) -> dict:
    """Skip to previous media track."""
    try:
        import pyautogui  # type: ignore[import-untyped,import-not-found]
        pyautogui.press("prevtrack")
        return ok("Previous track.")
    except Exception:
        pass

    try:
        _send_key_event(VK_MEDIA_PREV_TRACK)
        return ok("Previous track.")
    except Exception as exc:
        return fail(str(exc))
