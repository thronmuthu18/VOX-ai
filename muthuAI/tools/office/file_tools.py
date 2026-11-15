"""
MuthuAI Phase 5 — tools/office/file_tools.py

File Workspace Tools: Create folder, Copy file, Move file, Rename file.
Destructive overwrites require user confirmation.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from files.manager import FileWorkspaceManager


class CreateDirectoryTool(BaseTool):
    name = "create_directory"
    description = "Create a new folder/directory at the specified location."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "dir_path": {"type": "string", "description": "Folder path to create (e.g. 'data/documents/project_notes')."}
        },
        "required": ["dir_path"]
    }

    def execute(self, dir_path: str = "", **kwargs) -> ToolResult:
        if not dir_path:
            return ToolResult.fail("Please specify a directory path to create.")

        mgr = FileWorkspaceManager()
        res = mgr.create_directory(dir_path)
        if res["success"]:
            return ToolResult.ok(res["message"], path=res["path"])
        return ToolResult.fail(res["message"])


class CopyFileTool(BaseTool):
    name = "copy_file"
    description = "Copy a file from one location to another."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "src": {"type": "string", "description": "Source file path."},
            "dest": {"type": "string", "description": "Destination file path or folder."},
            "overwrite": {"type": "boolean", "default": False}
        },
        "required": ["src", "dest"]
    }

    def execute(self, src: str = "", dest: str = "", overwrite: bool = False, **kwargs) -> ToolResult:
        mgr = FileWorkspaceManager()
        res = mgr.copy_file(src, dest, overwrite=overwrite)
        if res["success"]:
            return ToolResult.ok(res["message"], path=res.get("path"))
        return ToolResult.fail(res["message"])


class MoveFileTool(BaseTool):
    name = "move_file"
    description = "Move a file from one location to another."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "src": {"type": "string", "description": "Source file path."},
            "dest": {"type": "string", "description": "Destination file path or folder."},
            "overwrite": {"type": "boolean", "default": False}
        },
        "required": ["src", "dest"]
    }

    def execute(self, src: str = "", dest: str = "", overwrite: bool = False, **kwargs) -> ToolResult:
        mgr = FileWorkspaceManager()
        res = mgr.move_file(src, dest, overwrite=overwrite)
        if res["success"]:
            return ToolResult.ok(res["message"], path=res.get("path"))
        return ToolResult.fail(res["message"])


class RenameFileTool(BaseTool):
    name = "rename_file"
    description = "Rename an existing file."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "src": {"type": "string", "description": "Source file path."},
            "new_name": {"type": "string", "description": "New filename (e.g. 'final_students.xlsx')."}
        },
        "required": ["src", "new_name"]
    }

    def execute(self, src: str = "", new_name: str = "", **kwargs) -> ToolResult:
        mgr = FileWorkspaceManager()
        res = mgr.rename_file(src, new_name)
        if res["success"]:
            return ToolResult.ok(res["message"], path=res.get("path"))
        return ToolResult.fail(res["message"])
