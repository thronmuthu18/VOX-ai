"""
VOX AI — tools package.

Populates tool registry with Windows desktop tools, Browser tools, RAG tools, Memory tools, and Office/File Productivity tools.
"""

from __future__ import annotations

from tools.base import BaseTool, ToolDefinition, ToolResult, PermissionLevel
from tools.registry import ToolRegistry
from tools.setup_registry import setup_tools


def setup_default_registry() -> ToolRegistry:
    """Create and return a single authoritative ToolRegistry populated with all VOX AI tools."""
    registry = ToolRegistry()
    setup_tools(registry)
    return registry


