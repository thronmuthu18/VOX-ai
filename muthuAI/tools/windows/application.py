"""
MuthuAI Phase 2 — tools/windows/application.py

Safe Windows application launcher with friendly name resolution.
Supports alias mappings (e.g. "vs code" -> "code", "chrome" -> "chrome.exe").
"""

from __future__ import annotations
import os
import subprocess
import getpass
from pathlib import Path

from tools.base import BaseTool, ToolResult, PermissionLevel
from utils.logger import get_logger

log = get_logger("muthuai.tools.application")

_USERNAME = getpass.getuser()

# Mapping friendly app names/aliases to executable names or paths
APP_ALIASES: dict[str, list[str]] = {
    "chrome": ["chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "google chrome": ["chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
    "vs code": ["code.exe", f"C:\\Users\\{_USERNAME}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe", r"C:\Program Files\Microsoft VS Code\Code.exe"],
    "visual studio code": ["code.exe", f"C:\\Users\\{_USERNAME}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"],
    "code": ["code.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "notepad": ["notepad.exe"],
    "command prompt": ["cmd.exe"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "control panel": ["control.exe"],
    "settings": ["ms-settings:"],
    "task manager": ["taskmgr.exe"],
    "taskmgr": ["taskmgr.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "vlc": ["vlc.exe", r"C:\Program Files\VideoLAN\VLC\vlc.exe"],
    "paint": ["mspaint.exe"],
    "mspaint": ["mspaint.exe"],
    "wordpad": ["wordpad.exe"],
}


def resolve_app(name: str) -> str | None:
    """Find executable or launch target for friendly app name."""
    name_lower = name.lower().strip()

    # Direct match in aliases
    if name_lower in APP_ALIASES:
        candidates = APP_ALIASES[name_lower]
        for cand in candidates:
            if cand.startswith("ms-settings:"):
                return cand
            if Path(cand).is_absolute() and Path(cand).exists():
                return cand
        # Fallback to candidate string if no absolute file exists yet
        for cand in candidates:
            if not Path(cand).is_absolute():
                return cand

    # Substring match in aliases
    for alias, candidates in APP_ALIASES.items():
        if alias in name_lower or name_lower in alias:
            for cand in candidates:
                if Path(cand).is_absolute() and Path(cand).exists():
                    return cand
            return candidates[0]

    # Fallback to name directly if simple alphanumeric and executable exists on system
    import shutil
    if name_lower.isalnum() and (shutil.which(name_lower) or shutil.which(f"{name_lower}.exe")):
        return f"{name_lower}.exe"

    return None


class OpenApplicationTool(BaseTool):
    name = "open_application"
    description = "Launch an installed Windows application by friendly name (e.g. Chrome, VS Code, Calculator, Notepad, Command Prompt, Control Panel, Settings, Task Manager)."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "application_name": {"type": "string", "description": "Application name."},
            "name": {"type": "string", "description": "Application name alias."},
            "app_name": {"type": "string", "description": "Application name alias."}
        },
        "required": []
    }

    def execute(self, application_name: str = "", name: str = "", app_name: str = "", **kwargs) -> ToolResult:
        target_name = application_name or name or app_name or ""
        if not target_name:
            return ToolResult.fail("Please specify which application to open.")

        from tools.application_tools import launch_application
        res = launch_application(target_name)
        if res.get("success", False):
            return ToolResult.ok(res.get("message", f"{target_name.title()} opened."), **res.get("data", {}))
        return ToolResult.fail(res.get("message", f"Could not open {target_name}."), **res.get("data", {}))



class ListApplicationsTool(BaseTool):
    name = "list_running_applications"
    description = "List currently open/running window titles on the computer."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        try:
            import pygetwindow as gw
            windows = gw.getAllTitles()
            non_empty = [w for w in windows if w.strip()]
            return ToolResult.ok(f"Found {len(non_empty)} running window(s).", windows=non_empty[:15])
        except Exception:
            try:
                out = subprocess.check_output('tasklist /FI "STATUS eq RUNNING" /FO CSV', shell=True, text=True)
                lines = [line.split(',')[0].strip('"') for line in out.splitlines()[1:] if line]
                unique = sorted(list(set(lines)))[:15]
                return ToolResult.ok(f"Found running processes: {', '.join(unique[:10])}", processes=unique)
            except Exception as exc:
                return ToolResult.fail(f"Could not list running applications: {exc}")
