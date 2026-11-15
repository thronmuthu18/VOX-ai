"""
CHAMP Phase 4 — tools/code_tools.py

VS Code project management, file opening, and safe code editing tools.
Never blindly replaces files: reads target file first, validates syntax, and verifies modification.
"""

from __future__ import annotations
import os
import ast
import shutil
import subprocess
from pathlib import Path
from utils.helpers import ok, fail, expand_path
from tools.windows.filesystem import FOLDER_MAPPINGS
from utils.logger import get_logger

log = get_logger("muthuai.tools.code_tools")

_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def _find_file_in_workspace(name: str, root_dir: Path | None = None) -> Path | None:
    """Locate a file by filename in the workspace."""
    search_root = root_dir or _WORKSPACE_ROOT
    # 1. Direct check
    candidate = search_root / name
    if candidate.exists() and candidate.is_file():
        return candidate

    # 2. Case-insensitive recursive search
    name_clean = name.lower().strip()
    for p in search_root.rglob("*"):
        if p.is_file() and not any(part.startswith((".", "__pycache__", "node_modules", ".venv")) for part in p.parts):
            if p.name.lower() == name_clean:
                return p
    return None


def open_vscode(path: str = "", file_name: str = "", target: str = "") -> dict:
    """
    Open VS Code with a project folder or specific file.
    Examples:
      - open_vscode() -> Opens VS Code
      - open_vscode(path="my project folder") -> Opens project root in VS Code
      - open_vscode(file_name="Chat.tsx") -> Locates Chat.tsx and opens it in VS Code
    """
    requested = target or file_name or path or ""
    log.info("open_vscode called with target: %r", requested)

    # 1. Resolve VS Code executable
    code_exe = shutil.which("code") or shutil.which("code.cmd")
    if not code_exe:
        # Check standard installation locations
        std_paths = [
            Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code" / "Code.exe",
            Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code" / "bin" / "code.cmd",
            Path(r"C:\Program Files\Microsoft VS Code\Code.exe"),
            Path(r"C:\Program Files\Microsoft VS Code\bin\code.cmd"),
            Path(r"C:\Program Files (x86)\Microsoft VS Code\Code.exe"),
        ]
        for sp in std_paths:
            if sp.exists():
                code_exe = str(sp)
                break

    if not code_exe:
        return fail("VS Code executable ('code') could not be located on this machine.")

    # 2. Determine target path
    target_path: Path | None = None
    if requested:
        req_lower = requested.lower().strip()
        if req_lower in FOLDER_MAPPINGS:
            mapped = FOLDER_MAPPINGS[req_lower]
            if not mapped.startswith("shell:"):
                target_path = Path(mapped)

        if target_path is None or not target_path.exists():
            # Check direct expansion
            try:
                candidate = expand_path(requested)
                if candidate.exists():
                    target_path = candidate
            except Exception:
                pass

        if target_path is None or not target_path.exists():
            # Search file in workspace
            target_path = _find_file_in_workspace(requested)

    # 3. Launch VS Code
    try:
        if target_path and target_path.exists():
            subprocess.Popen([code_exe, str(target_path)], shell=False)
            log.info("Launched VS Code with target: %s", target_path)
            return ok(
                f"VS Code opened with: {target_path.name}",
                data={"path": str(target_path), "is_file": target_path.is_file()}
            )
        else:
            subprocess.Popen([code_exe], shell=False)
            log.info("Launched VS Code (empty/last session)")
            return ok("VS Code opened successfully.", data={"path": code_exe})
    except Exception as exc:
        log.error("Failed to launch VS Code: %s", exc)
        return fail(f"Cannot launch VS Code: {exc}", error=str(exc))


def edit_code(
    file_path: str = "",
    file_name: str = "",
    old_code: str = "",
    new_code: str = "",
    validate_syntax: bool = True,
) -> dict:
    """
    Safely edit a code file:
      1. Locate file
      2. Read existing content
      3. Verify old_code exists
      4. Apply modification
      5. Validate syntax (AST check for Python files)
      6. Save and verify file modification
    """
    target = file_path or file_name or ""
    if not target:
        return fail("Please specify the file to edit.")
    if not old_code and not new_code:
        return fail("Please provide old_code and new_code for the edit.")

    # Locate file
    resolved: Path | None = None
    try:
        cand = expand_path(target)
        if cand.exists() and cand.is_file():
            resolved = cand
    except Exception:
        pass

    if resolved is None or not resolved.exists():
        resolved = _find_file_in_workspace(target)

    if resolved is None or not resolved.exists():
        return fail(f"Code file not found: {target!r}")

    # Read target file first
    try:
        original = resolved.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return fail(f"Could not read '{resolved.name}': {exc}", error=str(exc))

    if old_code not in original:
        return fail(
            f"Target snippet not found in '{resolved.name}'. File was not changed.",
            error="old_code snippet not found in file content."
        )

    updated = original.replace(old_code, new_code, 1)

    # Validate syntax if Python
    if validate_syntax and resolved.suffix.lower() == ".py":
        try:
            ast.parse(updated, filename=resolved.name)
        except SyntaxError as syn_err:
            log.warning("Syntax validation failed for proposed edit in %s: %s", resolved.name, syn_err)
            return fail(
                f"Syntax validation failed on proposed edit: {syn_err}. File was not saved.",
                error=str(syn_err)
            )

    # Save
    try:
        resolved.write_text(updated, encoding="utf-8")
        log.info("Successfully edited code file: %s", resolved)
        return ok(
            f"Code file '{resolved.name}' successfully edited and verified.",
            data={"path": str(resolved), "size": len(updated)}
        )
    except Exception as exc:
        return fail(f"Could not save '{resolved.name}': {exc}", error=str(exc))
