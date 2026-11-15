"""
MuthuAI Phase 5 — files/manager.py

File Workspace & Productivity Manager.
Handles file creation, renaming, moving, copying, folder creation, and safe overwrite checks.
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.files.manager")


class FileWorkspaceManager:
    """
    Manages workspace files and directory operations safely.
    """

    def create_directory(self, dir_path: str | Path) -> dict:
        p = Path(dir_path).resolve()
        try:
            p.mkdir(parents=True, exist_ok=True)
            log.info("Directory created: %s", p)
            return {"success": True, "path": str(p), "message": f"Folder '{p.name}' created successfully."}
        except Exception as exc:
            return {"success": False, "message": f"Could not create directory '{dir_path}': {exc}"}

    def copy_file(self, src: str | Path, dest: str | Path, overwrite: bool = False) -> dict:
        s = Path(src).resolve()
        d = Path(dest).resolve()

        if not s.exists():
            return {"success": False, "message": f"Source file '{src}' does not exist."}

        if d.is_dir():
            d = d / s.name

        if d.exists() and not overwrite:
            return {"success": False, "requires_confirmation": True, "message": f"Destination file '{d.name}' already exists. Confirm overwrite?"}

        try:
            shutil.copy2(str(s), str(d))
            log.info("Copied file %s -> %s", s.name, d)
            return {"success": True, "path": str(d), "message": f"File '{s.name}' copied to '{d.parent.name}'."}
        except Exception as exc:
            return {"success": False, "message": f"Could not copy file: {exc}"}

    def move_file(self, src: str | Path, dest: str | Path, overwrite: bool = False) -> dict:
        s = Path(src).resolve()
        d = Path(dest).resolve()

        if not s.exists():
            return {"success": False, "message": f"Source file '{src}' does not exist."}

        if d.is_dir():
            d = d / s.name

        if d.exists() and not overwrite:
            return {"success": False, "requires_confirmation": True, "message": f"Destination file '{d.name}' already exists. Confirm overwrite?"}

        try:
            shutil.move(str(s), str(d))
            log.info("Moved file %s -> %s", s.name, d)
            return {"success": True, "path": str(d), "message": f"File '{s.name}' moved to '{d.parent.name}'."}
        except Exception as exc:
            return {"success": False, "message": f"Could not move file: {exc}"}

    def rename_file(self, src: str | Path, new_name: str) -> dict:
        s = Path(src).resolve()
        if not s.exists():
            return {"success": False, "message": f"File '{src}' does not exist."}

        d = s.parent / new_name
        try:
            s.rename(d)
            log.info("Renamed file %s -> %s", s.name, d.name)
            return {"success": True, "path": str(d), "message": f"File renamed from '{s.name}' to '{d.name}'."}
        except Exception as exc:
            return {"success": False, "message": f"Could not rename file: {exc}"}
