"""
MuthuAI — safety/action_validator.py
Pre-execution validation of tool calls before they reach the executor.
"""

from __future__ import annotations


from pathlib import Path
from utils.helpers import expand_path
from utils.errors import ToolValidationError
from utils.logger import get_logger

log = get_logger(__name__)

# Paths the agent is NEVER allowed to touch
_PROTECTED_PATHS = [
    Path("C:/Windows"),
    Path("C:/Windows/System32"),
    Path("C:/Program Files"),
    Path("C:/Users/All Users"),
]

# Extensions that are never safe to delete via voice command
_PROTECTED_EXTENSIONS = {".sys", ".dll", ".exe", ".bat", ".ps1"}


class ActionValidator:
    """
    Validates tool parameters before execution.
    Raises ToolValidationError for unsafe or invalid parameters.
    """

    def validate(self, tool_name: str, params: dict) -> None:
        """
        Run all applicable validations for the given tool + params.
        Raises ToolValidationError if any check fails.
        """
        if "path" in params:
            self._validate_path(tool_name, params["path"])

        if tool_name == "run_command":
            self._validate_command(params.get("command", ""))

        if tool_name == "open_website":
            self._validate_url(params.get("url", ""))

    # ── Path Validation ──────────────────────────────────────

    def _validate_path(self, tool_name: str, path_input: str) -> None:
        if not path_input:
            return

        try:
            resolved = expand_path(path_input)
        except ValueError as exc:
            raise ToolValidationError(f"Invalid path: {exc}")

        # Block access to protected system paths on destructive operations
        if tool_name in ("delete_file", "delete_folder"):
            for protected in _PROTECTED_PATHS:
                try:
                    resolved.relative_to(protected)
                    raise ToolValidationError(
                        f"Refusing to delete protected path: {resolved}. "
                        "System directories are protected."
                    )
                except ValueError:
                    pass  # Not a subpath of protected

            if resolved.suffix.lower() in _PROTECTED_EXTENSIONS:
                raise ToolValidationError(
                    f"Refusing to delete '{resolved.suffix}' file — protected extension."
                )

    # ── Command Validation ───────────────────────────────────

    _BLOCKED_COMMANDS = [
        "format", "rm -rf", "del /f /s /q", "rd /s /q",
        "shutdown", "taskkill /f /im", "reg delete", "bcdedit",
    ]

    def _validate_command(self, command: str) -> None:
        lower = command.lower()
        for blocked in self._BLOCKED_COMMANDS:
            if blocked in lower:
                raise ToolValidationError(
                    f"Command blocked for safety reasons: {command!r}. "
                    f"Contains restricted keyword: {blocked!r}"
                )

    # ── URL Validation ───────────────────────────────────────

    def _validate_url(self, url: str) -> None:
        if not url:
            raise ToolValidationError("URL cannot be empty.")
        # Block non-web schemes
        if url.startswith(("file://", "javascript:", "data:", "about:")):
            raise ToolValidationError(f"Blocked URL scheme: {url!r}")
