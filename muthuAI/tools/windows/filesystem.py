"""
MuthuAI Phase 2 — tools/windows/filesystem.py

Natural-language Windows filesystem navigation and file operations.
Resolves paths like "D drive", "Downloads", "Desktop", "MuthuAI folder in D drive".
"""

from __future__ import annotations
import os
import subprocess
from pathlib import Path

from tools.base import BaseTool, ToolResult, PermissionLevel
from utils.logger import get_logger

log = get_logger("muthuai.tools.filesystem")

_ROOT = Path(__file__).resolve().parent.parent.parent

FOLDER_MAPPINGS: dict[str, str] = {
    "desktop": str(Path.home() / "Desktop"),
    "documents": str(Path.home() / "Documents"),
    "my documents": str(Path.home() / "Documents"),
    "downloads": str(Path("M:\\Downloads") if Path("M:\\").exists() else (Path.home() / "Downloads")),
    "pictures": str(Path.home() / "Pictures"),
    "photos": str(Path.home() / "Pictures"),
    "videos": str(Path.home() / "Videos"),
    "music": str(Path.home() / "Music"),
    "home": str(Path.home()),
    "this pc": "shell:MyComputerFolder",
    "my computer": "shell:MyComputerFolder",
    "c drive": "C:\\",
    "local disk c": "C:\\",
    "d drive": "D:\\",
    "local disk d": "D:\\",
    "e drive": "E:\\",
    "local disk e": "E:\\",
    "m drive": "M:\\",
    "local disk m": "M:\\",
    "m:\\": "M:\\",
    "m:": "M:\\",
    "workspace": "M:\\Workspace",
    "vox ai workspace": "M:\\",
    "generated": "M:\\Generated",
    "generated files": "M:\\Generated",
    "project folder": str(_ROOT),
    "my project folder": str(_ROOT),
    "muthuai": str(_ROOT),
    "muthuai folder": str(_ROOT),
    "vox ai folder": str(_ROOT),
    "juniors": str(_ROOT.parent),
    "juniors folder": str(_ROOT.parent),
}



def resolve_folder_path(path_input: str) -> str | Path | None:
    """Convert natural-language folder name or shortcut to a verified path."""
    lower = path_input.lower().strip()

    # Exact key match
    if lower in FOLDER_MAPPINGS:
        target = FOLDER_MAPPINGS[lower]
        if target.startswith("shell:"):
            return target
        p = Path(target)
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        return p if p.exists() else None

    # Natural language pattern checks
    # E.g. "champ folder in d drive", "champ folder in d:"
    if " in " in lower or "-la " in lower:
        # e.g., "Champ folder in D drive" or "D drive-la Champ folder"
        parts = lower.replace("-la ", " in ").split(" in ")
        if len(parts) == 2:
            subfolder = parts[0].replace("folder", "").strip()
            parent = parts[1].strip()
            parent_path = resolve_folder_path(parent)
            if isinstance(parent_path, Path) and parent_path.exists():
                candidate = parent_path / subfolder
                if candidate.exists():
                    return candidate
                # Try case insensitive search in parent
                for item in parent_path.iterdir():
                    if item.is_dir() and item.name.lower() == subfolder.lower():
                        return item

    # Check drive letter patterns: "d drive", "d:", "d"
    if lower.endswith(" drive"):
        drive_let = lower[0].upper()
        p = Path(f"{drive_let}:\\")
        if p.exists():
            return p

    # Direct Path check
    try:
        p = Path(os.path.expandvars(os.path.expanduser(path_input))).resolve()
        if p.exists():
            return p
    except Exception:
        pass

    return None


class OpenFolderTool(BaseTool):
    name = "open_folder"
    description = "Open a folder or drive in Windows File Explorer (e.g. 'D drive', 'Downloads', 'Desktop', 'Documents', 'Champ folder in D drive')."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "folder_path": {
                "type": "string",
                "description": "Folder name, drive letter, or natural language path (e.g., 'D drive', 'Downloads', 'Desktop', 'D:\\champ')."
            }
        },
        "required": ["folder_path"]
    }

    def execute(self, folder_path: str = "", **kwargs) -> ToolResult:
        target = folder_path or kwargs.get("path") or kwargs.get("folder_name") or kwargs.get("name") or ""
        if not target:
            return ToolResult.fail("Please specify which folder or drive to open.")

        resolved = resolve_folder_path(target)
        if resolved is None:
            return ToolResult.fail(f"Folder or drive '{target}' was not found on your computer.")

        log.info("Opening folder: %r -> %r", folder_path, resolved)
        try:
            if isinstance(resolved, str) and resolved.startswith("shell:"):
                os.system(f"explorer.exe {resolved}")
                return ToolResult.ok("This PC opened in File Explorer.")
            else:
                os.startfile(str(resolved))
                return ToolResult.ok(f"Opened folder: {resolved}")
        except Exception as exc:
            log.error("Failed to open folder %s: %s", resolved, exc)
            return ToolResult.fail(f"Could not open folder '{folder_path}': {exc}")


class OpenFileTool(BaseTool):
    name = "open_file"
    description = "Open a specific file using its default Windows application."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Full or relative path to the file to open."
            }
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str = "", **kwargs) -> ToolResult:
        if not file_path:
            return ToolResult.fail("Please specify a file path.")

        p = Path(os.path.expandvars(os.path.expanduser(file_path))).resolve()
        if not p.exists():
            return ToolResult.fail(f"File not found: '{file_path}'.")

        try:
            os.startfile(str(p))
            return ToolResult.ok(f"Opened file: {p.name}")
        except Exception as exc:
            return ToolResult.fail(f"Could not open file '{file_path}': {exc}")


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file permanently. Requires explicit user confirmation."
    permission = PermissionLevel.CONFIRM_REQUIRED
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "File path to delete."}
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str = "", **kwargs) -> ToolResult:
        p = Path(os.path.expandvars(os.path.expanduser(file_path))).resolve()
        if not p.exists():
            return ToolResult.fail(f"File '{file_path}' does not exist.")

        try:
            p.unlink()
            return ToolResult.ok(f"File deleted: {p.name}")
        except Exception as exc:
            return ToolResult.fail(f"Could not delete file '{file_path}': {exc}")


class DeleteFolderTool(BaseTool):
    name = "delete_folder"
    description = "Delete a folder and all its contents permanently. Requires explicit user confirmation."
    permission = PermissionLevel.CONFIRM_REQUIRED
    parameters = {
        "type": "object",
        "properties": {
            "folder_path": {"type": "string", "description": "Folder path to delete."}
        },
        "required": ["folder_path"]
    }

    def execute(self, folder_path: str = "", **kwargs) -> ToolResult:
        import shutil
        p = Path(os.path.expandvars(os.path.expanduser(folder_path))).resolve()
        if not p.exists():
            return ToolResult.fail(f"Folder '{folder_path}' does not exist.")

        try:
            shutil.rmtree(str(p))
            return ToolResult.ok(f"Folder deleted: {p.name}")
        except Exception as exc:
            return ToolResult.fail(f"Could not delete folder '{folder_path}': {exc}")
