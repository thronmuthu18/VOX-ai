"""
VOX AI — tools/application_tools.py
Launching Windows applications by friendly name with robust path discovery and empirical verification.
"""

from __future__ import annotations
import os
import sys
import subprocess
import getpass
import time
from pathlib import Path

from utils.helpers import ok, fail
from utils.logger import get_logger

log = get_logger("muthuai.tools.application_tools")
_USERNAME = getpass.getuser()

# Standard Windows installation paths for key desktop apps
_STANDARD_APP_PATHS: dict[str, list[str]] = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        rf"C:\Users\{_USERNAME}\AppData\Local\Google\Chrome\Application\chrome.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "vscode": [
        rf"C:\Users\{_USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "word": [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
        r"C:\Program Files\Microsoft Office\root\Office15\WINWORD.EXE",
    ],
    "excel": [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
        r"C:\Program Files\Microsoft Office\root\Office15\EXCEL.EXE",
    ],
    "powerpoint": [
        r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files\Microsoft Office\Office16\POWERPNT.EXE",
    ],
    "vlc": [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ],
    "notepad": [
        r"C:\Windows\notepad.exe",
        r"C:\Windows\System32\notepad.exe",
    ],
}

KNOWN_APPS: list[str] = list(_STANDARD_APP_PATHS.keys())



def _find_via_registry(app_name: str) -> str | None:
    """Look up application executable path from Windows Registry App Paths."""
    try:
        import winreg
        sub_keys = [
            rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{app_name}.exe",
            rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{app_name}",
        ]
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for sk in sub_keys:
                try:
                    with winreg.OpenKey(root, sk) as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val:
                            p = Path(val.strip('"'))
                            if p.exists():
                                return str(p)
                except (FileNotFoundError, OSError):
                    pass
    except Exception:
        pass
    return None


def _find_via_start_menu(app_name: str) -> str | None:
    """Scan Start Menu folders for matching shortcuts (.lnk files)."""
    start_dirs = [
        Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("APPDATA", rf"C:\Users\{_USERNAME}\AppData\Roaming")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]
    name_clean = app_name.lower().replace(" ", "")
    for s_dir in start_dirs:
        if s_dir.exists():
            try:
                for lnk in s_dir.rglob("*.lnk"):
                    lnk_name = lnk.stem.lower().replace(" ", "")
                    if name_clean in lnk_name or lnk_name in name_clean:
                        return str(lnk)
            except Exception:
                pass
    return None


def _verify_app_launched(clean: str, launched_path: str = "") -> dict:
    """Empirically verify that the application process or window is running."""
    from desktop.action_verifier import ActionVerifier
    verifier = ActionVerifier()
    
    proc_map = {
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "notepad": "notepad.exe",
        "cmd": "cmd.exe",
        "explorer": "explorer.exe",
        "vscode": "code.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "task manager": "taskmgr.exe",
    }
    
    proc_name = proc_map.get(clean, f"{clean}.exe")
    is_running = verifier.verify_process_running(proc_name)
    is_win = verifier.verify_window_active(clean)
    
    return {
        "launched": True,
        "process_running": is_running,
        "window_active": is_win,
        "process_name": proc_name,
        "path": launched_path
    }


def launch_application(app_name: str) -> dict:
    """
    Unified, robust application launcher for Windows with empirical launch verification.
    Supports Chrome, Edge, VS Code, Word, Excel, PowerPoint, Notepad, Calculator, Explorer, CMD, Settings, Control Panel.
    """
    if not app_name or not app_name.strip():
        return fail("Please specify which application to open.", error="EMPTY_APP_NAME")

    raw = app_name.lower().strip()
    clean = (
        raw.replace("google chrome", "chrome")
        .replace("microsoft chrome", "chrome")
        .replace("microsoft edge", "edge")
        .replace("vs code", "vscode")
        .replace("visual studio code", "vscode")
        .replace("microsoft word", "word")
        .replace("ms word", "word")
        .replace("microsoft excel", "excel")
        .replace("ms excel", "excel")
        .replace("microsoft powerpoint", "powerpoint")
        .replace("ms powerpoint", "powerpoint")
        .replace("ppt", "powerpoint")
        .replace("file explorer", "explorer")
        .replace("command prompt", "cmd")
    )

    # Built-in system tools (direct execution)
    if clean in ("calc", "calculator"):
        try:
            subprocess.Popen(["calc.exe"])
            time.sleep(0.3)
            ver = _verify_app_launched("calculator", "calc.exe")
            return ok("Calculator opened successfully.", verification=ver, data={"app": "calculator"})
        except Exception as exc:
            return fail(f"Cannot open Calculator: {exc}", error=str(exc))

    if clean in ("notepad", "text editor"):
        try:
            subprocess.Popen(["notepad.exe"])
            time.sleep(0.3)
            ver = _verify_app_launched("notepad", "notepad.exe")
            return ok("Notepad opened successfully.", verification=ver, data={"app": "notepad"})
        except Exception as exc:
            return fail(f"Cannot open Notepad: {exc}", error=str(exc))

    if clean in ("cmd", "command prompt", "terminal"):
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe"])
            time.sleep(0.3)
            ver = _verify_app_launched("cmd", "cmd.exe")
            return ok("Command Prompt opened successfully.", verification=ver, data={"app": "cmd"})
        except Exception as exc:
            return fail(f"Cannot open Command Prompt: {exc}", error=str(exc))

    if clean in ("explorer", "my computer", "this pc"):
        try:
            subprocess.Popen(["explorer.exe"])
            time.sleep(0.3)
            ver = _verify_app_launched("explorer", "explorer.exe")
            return ok("File Explorer opened successfully.", verification=ver, data={"app": "explorer"})
        except Exception as exc:
            return fail(f"Cannot open File Explorer: {exc}", error=str(exc))

    if clean in ("settings", "windows settings"):
        try:
            os.startfile("ms-settings:")
            return ok("Settings opened successfully.", data={"app": "settings", "path": "ms-settings:"})
        except Exception as exc:
            return fail(f"Cannot open Settings: {exc}", error=str(exc))

    if clean in ("control panel", "control"):
        try:
            subprocess.Popen(["control.exe"])
            time.sleep(0.3)
            ver = _verify_app_launched("control panel", "control.exe")
            return ok("Control Panel opened successfully.", verification=ver, data={"app": "control panel"})
        except Exception as exc:
            return fail(f"Cannot open Control Panel: {exc}", error=str(exc))

    if clean in ("camera", "webcam"):
        try:
            os.startfile("microsoft.windows.camera:")
            return ok("Camera opened successfully.", data={"app": "camera"})
        except Exception as exc:
            return fail(f"Cannot open Camera: {exc}", error=str(exc))

    if clean in ("whatsapp", "whats app"):
        try:
            # Try Windows Store WhatsApp protocol first
            subprocess.Popen(["cmd.exe", "/c", "start", "whatsapp:"], shell=False)
            time.sleep(0.5)
            return ok("WhatsApp application opened successfully.", data={"path": "whatsapp:"})
        except Exception:
            try:
                from browser.manager import BrowserManager
                bm = BrowserManager.get_instance()
                page = bm.get_page(headless=False)
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=15000)
                return ok("WhatsApp Web opened successfully in browser.", data={"url": "https://web.whatsapp.com"})
            except Exception as exc:
                return fail(f"Cannot open WhatsApp: {exc}", error=str(exc))

    # Check Windows Registry App Paths
    reg_path = _find_via_registry(clean)
    if reg_path and Path(reg_path).exists():
        try:
            subprocess.Popen([reg_path], shell=False)
            time.sleep(0.4)
            ver = _verify_app_launched(clean, reg_path)
            log.info("Launched %s via Windows Registry: %s", clean, reg_path)
            return ok(f"{clean.title()} opened successfully.", verification=ver, data={"path": reg_path, "source": "registry"})
        except Exception as exc:
            log.warning("Failed to launch %s from registry path %s: %s", clean, reg_path, exc)

    # Check standard installation paths on disk
    standard_paths = _STANDARD_APP_PATHS.get(clean, [])
    for p_str in standard_paths:
        p = Path(p_str)
        if p.exists():
            try:
                subprocess.Popen([str(p)], shell=False)
                time.sleep(0.4)
                ver = _verify_app_launched(clean, str(p))
                log.info("Launched %s via standard path: %s", clean, p)
                return ok(f"{clean.title()} opened successfully.", verification=ver, data={"path": str(p), "source": "standard_path"})
            except Exception as exc:
                log.warning("Failed to launch %s from %s: %s", clean, p, exc)

    # Check Start Menu shortcut (.lnk)
    lnk_path = _find_via_start_menu(clean)
    if lnk_path and Path(lnk_path).exists():
        try:
            os.startfile(lnk_path)
            time.sleep(0.4)
            ver = _verify_app_launched(clean, lnk_path)
            log.info("Launched %s via Start Menu shortcut: %s", clean, lnk_path)
            return ok(f"{clean.title()} opened successfully.", verification=ver, data={"path": lnk_path, "source": "start_menu"})
        except Exception as exc:
            log.warning("Failed to launch %s from shortcut %s: %s", clean, lnk_path, exc)

    # Check PATH via 'where'
    try:
        res = subprocess.run(["where", clean], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            found = res.stdout.strip().splitlines()[0]
            subprocess.Popen([found], shell=False)
            time.sleep(0.4)
            ver = _verify_app_launched(clean, found)
            log.info("Launched %s via PATH lookup: %s", clean, found)
            return ok(f"{clean.title()} opened successfully.", verification=ver, data={"path": found, "source": "path"})
    except Exception:
        pass

    # Windows Start shell fallback (for registered protocol / system commands)
    try:
        if clean in ("excel", "ms excel"):
            subprocess.Popen('start excel', shell=True)
            time.sleep(0.4)
            ver = _verify_app_launched("excel", "shell")
            return ok("Excel opened successfully.", verification=ver, data={"path": "shell"})
        if clean in ("powerpoint", "ppt", "ms powerpoint"):
            subprocess.Popen('start powerpnt', shell=True)
            time.sleep(0.4)
            ver = _verify_app_launched("powerpoint", "shell")
            return ok("PowerPoint opened successfully.", verification=ver, data={"path": "shell"})
        if clean in ("word", "ms word"):
            subprocess.Popen('start winword', shell=True)
            time.sleep(0.4)
            ver = _verify_app_launched("word", "shell")
            return ok("Word opened successfully.", verification=ver, data={"path": "shell"})
    except Exception:
        pass

    import shutil
    if shutil.which(clean) or shutil.which(f"{clean}.exe"):
        try:
            subprocess.Popen(f'start "" "{clean}"', shell=True)
            time.sleep(0.4)
            ver = _verify_app_launched(clean, "shell")
            log.info("Launched %s via shell start", clean)
            return ok(f"{clean.title()} opened successfully.", verification=ver, data={"path": "shell"})
        except Exception:
            pass

    return fail(
        f"{clean.title()} could not be located. Checked standard installation paths, Windows Registry, Start Menu, and system PATH.",
        error=f"Executable not found for '{clean}'."
    )


def open_application(name: str | None = None, app_name: str | None = None, application_name: str | None = None, target: str | None = None) -> dict:
    """
    Launch a Windows application by its friendly name. Accepts 'name', 'app_name', 'application_name', or 'target'.
    """
    target_app = name or app_name or application_name or target or ""
    return launch_application(target_app)


def open_control_panel() -> dict:
    return launch_application("control panel")


def open_settings() -> dict:
    return launch_application("settings")


def open_calculator() -> dict:
    return launch_application("calculator")


def open_notepad() -> dict:
    return launch_application("notepad")


def open_command_prompt() -> dict:
    return launch_application("cmd")


def open_camera() -> dict:
    return launch_application("camera")


def open_task_manager() -> dict:
    try:
        subprocess.Popen(["taskmgr.exe"])
        time.sleep(0.3)
        ver = _verify_app_launched("task manager", "taskmgr.exe")
        return ok("Task Manager opened successfully.", verification=ver)
    except Exception as exc:
        return fail(f"Cannot open Task Manager: {exc}", error=str(exc))


