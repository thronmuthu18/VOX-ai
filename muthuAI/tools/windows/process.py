"""
MuthuAI Phase 2 — tools/windows/process.py

Process management tools: list running processes, terminate process.
Terminating a process requires explicit user confirmation.
"""

from __future__ import annotations
import subprocess

from tools.base import BaseTool, ToolResult, PermissionLevel
from utils.logger import get_logger

log = get_logger("muthuai.tools.process")


class ListProcessesTool(BaseTool):
    name = "list_processes"
    description = "List currently running processes on Windows."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        try:
            out = subprocess.check_output(
                'tasklist /FI "STATUS eq RUNNING" /FO CSV',
                shell=True,
                text=True,
                stderr=subprocess.STDOUT,
            )
            lines = [line.split(',')[0].strip('"') for line in out.splitlines()[1:] if line]
            unique = sorted(list(set(lines)))[:20]
            return ToolResult.ok(f"Active processes: {', '.join(unique[:12])}...", processes=unique)
        except Exception as exc:
            return ToolResult.fail(f"Could not list processes: {exc}")


class TerminateProcessTool(BaseTool):
    name = "terminate_process"
    description = "Terminate/kill a running process by executable name (e.g., 'notepad.exe', 'chrome.exe'). Requires confirmation."
    permission = PermissionLevel.CONFIRM_REQUIRED
    parameters = {
        "type": "object",
        "properties": {
            "process_name": {
                "type": "string",
                "description": "Executable name of process to kill (e.g., 'notepad.exe')."
            }
        },
        "required": ["process_name"]
    }

    def execute(self, process_name: str = "", **kwargs) -> ToolResult:
        if not process_name:
            return ToolResult.fail("Please specify a process name to terminate.")

        if not process_name.endswith(".exe"):
            process_name += ".exe"

        log.info("Terminating process: %s", process_name)
        try:
            res = subprocess.run(
                ["taskkill", "/F", "/IM", process_name],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                return ToolResult.ok(f"Process '{process_name}' terminated successfully.")
            else:
                return ToolResult.fail(f"Could not terminate '{process_name}': {res.stderr.strip()}")
        except Exception as exc:
            return ToolResult.fail(f"Failed to terminate process: {exc}")
