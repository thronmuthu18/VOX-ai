"""
VOX AI — tools/registry.py

Central Tool Registry for VOX AI Personal Assistant.
Authoritative tool catalogue: registers, validates, discovers, and executes tools.
"""

from __future__ import annotations
from typing import Iterator

from tools.base import BaseTool, ToolResult, PermissionLevel
from utils.logger import get_logger

log = get_logger("muthuai.registry")


class DuplicateToolError(ValueError):
    """Raised when an attempt is made to register a duplicate tool without overwrite permission."""
    pass


class ToolRegistry:
    """
    Maintains the authoritative catalogue of all registered VOX AI tools.
    Provides validation against duplicate registration and uniform execution.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool, allow_overwrite: bool = True) -> None:
        """Add a tool instance to the registry with duplicate detection."""
        if not tool or not tool.name:
            raise ValueError(f"Tool {tool!r} has no valid name.")
        
        if tool.name in self._tools:
            if not allow_overwrite:
                raise DuplicateToolError(f"Tool '{tool.name}' is already registered in registry.")
            log.debug("Overwriting existing tool registration for '%s'.", tool.name)
        
        self._tools[tool.name] = tool
        log.debug("Registered tool: %s (%s)", tool.name, tool.permission.value)

    def register_all(self, tools: list[BaseTool], allow_overwrite: bool = True) -> None:
        """Register multiple tools at once."""
        for tool in tools:
            self.register(tool, allow_overwrite=allow_overwrite)

    def get(self, name: str) -> BaseTool | None:
        """Return a tool by name, or None if not found."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def all_tools(self) -> Iterator[BaseTool]:
        return iter(self._tools.values())

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Look up and execute a tool by name.
        Always returns a structured ToolResult — never raises.
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            log.warning("Unknown tool requested: %r", tool_name)
            return ToolResult.fail(
                f"I don't have a tool called '{tool_name}' yet.",
                tool=tool_name,
                error=f"TOOL_NOT_FOUND: {tool_name}",
                requested_tool=tool_name
            )

        log.info("Executing tool: %s args=%s", tool_name, kwargs)
        try:
            result = tool.execute(**kwargs)
            if not isinstance(result, ToolResult):
                if isinstance(result, dict):
                    success = bool(result.get("success", True))
                    msg = str(result.get("message", "Success" if success else "Failed"))
                    err = result.get("error")
                    ver = result.get("verification", {})
                    data = {k: v for k, v in result.items() if k not in ("success", "message", "error", "verification")}
                    if success:
                        result = ToolResult.ok(msg, tool=tool_name, verification=ver, **data)
                    else:
                        result = ToolResult.fail(msg, tool=tool_name, error=err, verification=ver, **data)
                elif isinstance(result, str):
                    result = ToolResult.ok(result, tool=tool_name)
                else:
                    result = ToolResult.ok(str(result), tool=tool_name)
            
            if not result.tool:
                result.tool = tool_name

            if result.success:
                log.info("Tool %s succeeded: %s", tool_name, result.message)
            else:
                log.warning("Tool %s failed: %s", tool_name, result.message)
            return result
        except Exception as exc:
            log.exception("Unhandled exception in tool %s: %s", tool_name, exc)
            return ToolResult.fail(
                f"An unexpected error occurred while running '{tool_name}': {exc}",
                tool=tool_name,
                error=str(exc)
            )

    def to_tool_schemas(self) -> list[dict]:
        """
        Export tool schemas for Gemini prompt / function declaration.
        """
        schemas = []
        for tool in self._tools.values():
            if tool.permission == PermissionLevel.BLOCKED:
                continue
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters or {
                    "type": "object", "properties": {}, "required": []
                },
            })
        return schemas

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        return f"<ToolRegistry tools={list(self._tools.keys())}>"

