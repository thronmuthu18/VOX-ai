"""
VOX AI — utils/workspace.py

Authoritative Workspace and Storage Management for VOX AI.
Permanent Default Workspace: M:\\

All created, generated, downloaded, exported, and saved files use M:\\ by default
organized into standard subdirectories:
  M:\\
  ├── Downloads\\
  ├── Generated\\
  │   ├── PDF\\
  │   ├── Word\\
  │   ├── Excel\\
  │   ├── PowerPoint\\
  │   ├── Text\\
  │   └── Images\\
  ├── Projects\\
  ├── Temp\\
  └── Workspace\\
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from utils.logger import get_logger

log = get_logger("voxai.utils.workspace")

# ── 1. Configuration & Default Root ──────────────────────────────────────────

_ENV_WORKSPACE = os.getenv("VOXAI_WORKSPACE", "M:\\")

def get_default_workspace() -> Path:
    """Return the configured default workspace root Path (defaults to M:\\)."""
    ws = os.getenv("VOXAI_WORKSPACE", _ENV_WORKSPACE)
    try:
        p = Path(ws).resolve()
        return p
    except Exception:
        return Path("M:\\")

DEFAULT_WORKSPACE: Path = get_default_workspace()

# ── 2. Standard Workspace Subdirectories ─────────────────────────────────────

DOWNLOADS_DIR: Path = DEFAULT_WORKSPACE / "Downloads"
GENERATED_DIR: Path = DEFAULT_WORKSPACE / "Generated"

PDF_DIR: Path = GENERATED_DIR / "PDF"
WORD_DIR: Path = GENERATED_DIR / "Word"
EXCEL_DIR: Path = GENERATED_DIR / "Excel"
PPT_DIR: Path = GENERATED_DIR / "PowerPoint"
TEXT_DIR: Path = GENERATED_DIR / "Text"
IMAGES_DIR: Path = GENERATED_DIR / "Images"

PROJECTS_DIR: Path = DEFAULT_WORKSPACE / "Projects"
TEMP_DIR: Path = DEFAULT_WORKSPACE / "Temp"
WORKSPACE_DIR: Path = DEFAULT_WORKSPACE / "Workspace"

CATEGORY_DIRS: dict[str, Path] = {
    "pdf": PDF_DIR,
    "word": WORD_DIR,
    "doc": WORD_DIR,
    "docx": WORD_DIR,
    "excel": EXCEL_DIR,
    "xls": EXCEL_DIR,
    "xlsx": EXCEL_DIR,
    "csv": EXCEL_DIR,
    "powerpoint": PPT_DIR,
    "ppt": PPT_DIR,
    "pptx": PPT_DIR,
    "text": TEXT_DIR,
    "txt": TEXT_DIR,
    "note": TEXT_DIR,
    "notes": TEXT_DIR,
    "log": TEXT_DIR,
    "md": TEXT_DIR,
    "images": IMAGES_DIR,
    "image": IMAGES_DIR,
    "img": IMAGES_DIR,
    "png": IMAGES_DIR,
    "jpg": IMAGES_DIR,
    "jpeg": IMAGES_DIR,
    "downloads": DOWNLOADS_DIR,
    "download": DOWNLOADS_DIR,
    "projects": PROJECTS_DIR,
    "project": PROJECTS_DIR,
    "temp": TEMP_DIR,
    "workspace": WORKSPACE_DIR,
}


def init_workspace_dirs() -> bool:
    """
    Ensure all standard workspace directories exist under M:\\.
    Gracefully handles environment restrictions.
    """
    ws = get_default_workspace()
    all_dirs = [
        ws,
        DOWNLOADS_DIR,
        GENERATED_DIR,
        PDF_DIR,
        WORD_DIR,
        EXCEL_DIR,
        PPT_DIR,
        TEXT_DIR,
        IMAGES_DIR,
        PROJECTS_DIR,
        TEMP_DIR,
        WORKSPACE_DIR,
    ]
    created = 0
    for d in all_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            created += 1
        except Exception as exc:
            log.debug("Workspace dir '%s' could not be pre-created (%s)", d, exc)
    log.info("Initialized VOX AI workspace at '%s' (%d directories verified)", ws, created)
    return created > 0


# ── 3. Central Path Resolver ──────────────────────────────────────────────────

def sanitize_stem(name: str) -> str:
    """Sanitize a file stem without stripping valid filename characters."""
    clean = re.sub(r'[\\/:*?"<>|]', '_', name)
    clean = re.sub(r'\s+', '_', clean).strip('._ ')
    return clean or "file"


def resolve_output_path(
    filename: str = "",
    category: str | None = None,
    requested_path: str | None = None,
    default_name: str = "output",
    extension: str | None = None,
) -> Path:
    """
    Authoritative path resolver for all VOX AI file operations.

    Rules:
    1. If user explicitly provided a full path (with drive or parent directory), use it.
    2. If user provided a simple filename or none, route to M:\\Generated\\<Category>\\<filename>.
    3. Ensure parent directory exists before returning.
    """
    raw = requested_path or filename or default_name

    # Check if raw is already an explicit path with directory structure
    p = Path(raw)
    is_explicit_path = False
    try:
        is_explicit_path = p.is_absolute() or len(p.parts) > 1 or (len(str(raw)) > 2 and str(raw)[1] == ":")
    except Exception:
        is_explicit_path = False

    if is_explicit_path:
        # User provided an explicit directory or full path
        resolved = p.resolve()
        if extension and not resolved.suffix:
            resolved = resolved.with_suffix(f".{extension.lstrip('.')}")
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return resolved

    # Plain filename -> Resolve to default M:\ subdirectory by category/extension
    name_only = p.name or default_name
    ext = extension or (p.suffix if p.suffix else "")
    ext_clean = f".{ext.lstrip('.')}" if ext else ""

    # Strip existing extension from stem if present
    stem = name_only
    if ext_clean and stem.lower().endswith(ext_clean.lower()):
        stem = stem[:-len(ext_clean)]
    elif "." in stem:
        stem_part, dot_ext = os.path.splitext(stem)
        if dot_ext.lower() in (".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".csv", ".png", ".jpg", ".jpeg", ".webp", ".json", ".py", ".html"):
            stem = stem_part
            if not ext_clean:
                ext_clean = dot_ext

    safe_stem = sanitize_stem(stem)
    target_filename = f"{safe_stem}{ext_clean}"

    # Determine target subdirectory
    target_dir: Path | None = None
    if category and category.lower() in CATEGORY_DIRS:
        target_dir = CATEGORY_DIRS[category.lower()]
    elif ext_clean:
        ext_key = ext_clean.lstrip(".").lower()
        if ext_key in CATEGORY_DIRS:
            target_dir = CATEGORY_DIRS[ext_key]

    if target_dir is None:
        target_dir = GENERATED_DIR / "Text"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        log.warning("Could not create target directory '%s' (%s). Fallback to local.", target_dir, exc)

    return target_dir / target_filename


# ── 4. File Verification Helper ───────────────────────────────────────────────

def verify_file_on_disk(
    path: Path | str,
    expected_extension: str | None = None,
    min_bytes: int = 1,
) -> dict[str, Any]:
    """
    Empirically verifies that a file exists physically on disk, is non-empty,
    matches the expected extension, and can be read.
    """
    p = Path(path)
    result: dict[str, Any] = {
        "verified": False,
        "path": str(p),
        "name": p.name,
        "size": 0,
        "exists": False,
        "is_file": False,
        "readable": False,
        "error": None,
    }

    try:
        if not p.exists():
            result["error"] = f"File does not exist on disk: {p}"
            return result
        result["exists"] = True

        if not p.is_file():
            result["error"] = f"Path is not a regular file: {p}"
            return result
        result["is_file"] = True

        size = p.stat().st_size
        result["size"] = size
        if size < min_bytes:
            result["error"] = f"File size ({size} bytes) is below minimum required ({min_bytes} bytes)."
            return result

        if expected_extension:
            expected_ext = f".{expected_extension.lstrip('.').lower()}"
            if p.suffix.lower() != expected_ext:
                result["error"] = f"File extension '{p.suffix}' does not match expected '{expected_ext}'."
                return result

        # Readability check
        try:
            with open(p, "rb") as f:
                f.read(min(size, 1024))
            result["readable"] = True
        except Exception as read_exc:
            result["error"] = f"File is not readable: {read_exc}"
            return result

        result["verified"] = True
        return result

    except Exception as exc:
        result["error"] = f"Verification exception: {exc}"
        return result
