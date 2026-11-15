"""
MuthuAI Phase 2 — tools/base.py

BaseTool abstract class and ToolResult dataclass.
Every tool in Phase 2+ inherits from BaseTool.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PermissionLevel(str, Enum):
    SAFE = "safe"                    # Execute automatically without confirmation
    MODERATE = "moderate"            # Creates/modifies content, reversible
    DANGEROUS = "dangerous"          # Irreversible / sensitive, requires confirmation
    CONFIRM_REQUIRED = "confirm"     # Require explicit user confirmation before execution
    BLOCKED = "blocked"              # Never execute via voice command


@dataclass
class ToolResult:
    """Standard structured result returned by every tool execution."""
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    tool: str = ""
    action: str = ""
    error: str | None = None
    verification: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Extract error from data if present and not set
        if self.error is None and "error" in self.data:
            self.error = str(self.data["error"]) if self.data["error"] is not None else None
        # Extract verification from data if present and not set
        if not self.verification and "verification" in self.data and isinstance(self.data["verification"], dict):
            self.verification = self.data["verification"]

    @classmethod
    def ok(cls, message: str, tool: str = "", action: str = "", verification: dict[str, Any] | None = None, **data) -> "ToolResult":
        ver = verification or data.pop("verification", {})
        return cls(success=True, message=message, data=data, tool=tool, action=action, error=None, verification=ver)

    @classmethod
    def fail(cls, message: str, tool: str = "", action: str = "", error: str | None = None, verification: dict[str, Any] | None = None, **data) -> "ToolResult":
        err = error or str(data.get("error")) if "error" in data else None
        ver = verification or data.pop("verification", {})
        return cls(success=False, message=message, data=data, tool=tool, action=action, error=err, verification=ver)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "tool": self.tool,
            "action": self.action,
            "result": self.message,
            "message": self.message,
            "error": self.error,
            "data": self.data,
            "verification": self.verification,
        }


class BaseTool(ABC):
    """
    Abstract base for all VOX AI tools.

    Subclasses must define:
        name        — unique identifier used in planner JSON
        description — shown to Gemini for tool selection
        parameters  — JSON-schema dict describing accepted arguments
        permission  — PermissionLevel controlling whether confirmation is needed
        execute()   — the actual implementation
    """

    name: str = ""
    description: str = ""
    parameters: dict = {}
    permission: PermissionLevel = PermissionLevel.SAFE

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Run the tool and return a ToolResult. Never raises."""
        ...

    def __repr__(self) -> str:
        return f"<Tool:{self.name} perm={self.permission.value}>"


@dataclass
class ToolDefinition(BaseTool):
    name: str = ""
    description: str = ""
    parameters: dict = field(default_factory=dict)
    permission_level: PermissionLevel = PermissionLevel.SAFE
    handler: Any = None
    aliases: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.permission = self.permission_level

    def execute(self, **kwargs) -> ToolResult:
        if self.handler:
            try:
                res = self.handler(**kwargs)
                if isinstance(res, ToolResult):
                    if not res.tool:
                        res.tool = self.name
                    return res
                elif isinstance(res, dict):
                    success = bool(res.get("success", True))
                    msg = str(res.get("message", "Success" if success else "Failed"))
                    data = dict(res.get("data", {})) if isinstance(res.get("data"), dict) else {}
                    err = res.get("error")
                    ver = res.get("verification", {})
                    for k, v in res.items():
                        if k not in ("success", "message", "data", "error", "verification") and k not in data:
                            data[k] = v
                    data.pop("verification", None)
                    data.pop("error", None)
                    data.pop("tool", None)
                    data.pop("action", None)
                    if success:
                        return ToolResult.ok(msg, tool=self.name, verification=ver, **data)
                    return ToolResult.fail(msg, tool=self.name, error=err, verification=ver, **data)
                elif isinstance(res, str):
                    return ToolResult.ok(res, tool=self.name)
                return ToolResult.ok(str(res), tool=self.name)
            except Exception as exc:
                return ToolResult.fail(f"Tool '{self.name}' execution failed: {exc}", tool=self.name, error=str(exc))
        return ToolResult.fail("No handler attached.", tool=self.name)


