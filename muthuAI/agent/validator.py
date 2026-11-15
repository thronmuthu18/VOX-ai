"""
MuthuAI Phase 6 — agent/validator.py

Task Step Output Validator.
Verifies tool execution output and returns structured validation results.
"""

from __future__ import annotations
from pathlib import Path
from tools.base import ToolResult
from utils.logger import get_logger

log = get_logger("muthuai.agent.validator")


class StepValidator:
    """
    Validates execution results of individual task steps.
    """

    def validate_result(self, tool_name: str, args: dict, result: ToolResult) -> tuple[bool, str]:
        """
        Validate execution result. Returns (is_valid: bool, reason: str).
        """
        if not result.success:
            return False, result.message

        # Check created file outputs
        if tool_name in ("create_excel", "create_word", "create_powerpoint", "create_pdf", "explain_and_create_pdf", "create_file", "create_csv", "create_folder"):
            file_path = result.data.get("file_path") or result.data.get("path") or result.data.get("output_path")
            if not file_path or not Path(file_path).exists():
                return False, f"Generated file '{file_path}' was not found on disk."

            if tool_name != "create_folder" and Path(file_path).stat().st_size == 0 and result.data.get("size", 1) > 0:
                return False, f"Generated file '{file_path}' is empty (0 bytes)."


        log.debug("Step validation passed for tool %s.", tool_name)
        return True, "Validated successfully."
