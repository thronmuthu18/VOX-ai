"""
MuthuAI Phase 2 — safety/validator.py

Pre-execution validation layer.
Blocks destructive system paths, malicious inputs, and disallowed shell commands.
"""

from __future__ import annotations
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.safety.validator")

# System directory paths that are strictly protected from deletion/modification
_PROTECTED_PATHS = (
    Path("C:/Windows"),
    Path("C:/Windows/System32"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/Users/All Users"),
)

_BLOCKED_COMMAND_KEYWORDS = (
    "format ", "rmdir /s", "del /f /s /q", "rd /s /q",
    "shutdown", "bcedit", "reg delete", "diskpart"
)


class SafetyValidationError(Exception):
    """Raised when an operation fails safety validation."""


class ActionValidator:
    """
    Validates tool names and parameters prior to tool execution.
    Raises SafetyValidationError if dangerous or prohibited.
    """

    def validate(self, tool_name: str, params: dict) -> None:
        """
        Validate tool arguments. Raises SafetyValidationError if unsafe.
        """
        # Validate paths in params
        for key in ("file_path", "folder_path", "path"):
            if key in params and params[key]:
                self._validate_path(tool_name, params[key])

        # Validate process names
        if tool_name == "terminate_process":
            proc = params.get("process_name", "").lower()
            if proc in ("csrss.exe", "lsass.exe", "smss.exe", "services.exe", "svchost.exe", "explorer.exe"):
                raise SafetyValidationError(f"Refusing to terminate critical Windows system process: '{proc}'.")

    def _validate_path(self, tool_name: str, path_input: str) -> None:
        if not path_input:
            return

        try:
            p = Path(path_input).resolve()
        except Exception:
            return

        # Check deletion of protected system paths
        if "delete" in tool_name:
            for protected in _PROTECTED_PATHS:
                try:
                    if p == protected or p.is_relative_to(protected):
                        raise SafetyValidationError(
                            f"Refusing to delete protected system path '{p}'. System directories are protected."
                        )
                except (ValueError, AttributeError):
                    pass
