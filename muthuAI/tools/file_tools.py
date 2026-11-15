"""
VOX AI — tools/file_tools.py
File and folder operations: open, read, list, create, write, edit, delete (with confirmation).
"""

from __future__ import annotations

import os
import csv
import subprocess
from pathlib import Path

from tools.windows.filesystem import FOLDER_MAPPINGS
from utils.helpers import ok, fail, expand_path, safe_filename
from utils.logger import get_logger

log = get_logger("voxai.tools.file_tools")


def open_folder(path: str | None = None, folder_name: str | None = None) -> dict:
    """Open a folder in Windows Explorer. Understands natural-language shortcuts."""
    target_path = path or folder_name or ""
    if not target_path:
        return fail("Please specify which folder or drive to open.")
    resolved = _resolve_folder(target_path)
    if resolved is None:
        return fail(f"Folder not recognised or does not exist: {path!r}")

    log.info("Opening folder: %s", resolved)
    try:
        os.startfile(str(resolved))
        return ok(f"Opened folder: {resolved}", data={"path": str(resolved)})
    except Exception as exc:
        try:
            subprocess.Popen(["explorer.exe", str(resolved)])
            return ok(f"Opened folder: {resolved}", data={"path": str(resolved)})
        except Exception as exc2:
            return fail(f"Cannot open folder: {exc2}", error=str(exc2))


def open_file(path: str) -> dict:
    """Open a file with its default Windows application."""
    try:
        resolved = expand_path(path)
        if not resolved.exists():
            return fail(f"File not found: {path!r}")
        os.startfile(str(resolved))
        return ok(f"Opened file: {resolved.name}", data={"path": str(resolved)})
    except Exception as exc:
        return fail(f"Cannot open file: {exc}", error=str(exc))


def read_file(path: str, max_chars: int = 5000) -> dict:
    """Read and return the text content of a file."""
    try:
        resolved = expand_path(path)
        if not resolved.exists():
            return fail(f"File not found: {path!r}")
        content = resolved.read_text(encoding="utf-8", errors="replace")
        truncated = len(content) > max_chars
        return ok(
            f"Read file: {resolved.name}",
            data={"content": content[:max_chars], "truncated": truncated, "path": str(resolved)}
        )
    except Exception as exc:
        return fail(f"Cannot read file: {exc}", error=str(exc))


def create_file(
    path: str = "",
    filename: str = "",
    file_name: str = "",
    name: str = "",
    content: str = "",
    overwrite: bool = True
) -> dict:
    """
    Create or write a text/code/data file on disk and verify its creation.
    Defaults to M:\\Generated\\Text\\ if no directory is specified.
    """
    raw_target = path or filename or file_name or name or "note.txt"
    try:
        from utils.workspace import resolve_output_path, verify_file_on_disk
        resolved = resolve_output_path(raw_target, category="text", extension=".txt")
        if resolved.exists() and not overwrite:
            return fail(f"File '{resolved.name}' already exists. Overwrite disabled.")

        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")

        # Physical empirical verification
        ver = verify_file_on_disk(resolved, min_bytes=0)
        if not ver["verified"]:
            return fail(f"Physical file verification failed: {ver['error']}", error=ver["error"])

        log.info("File created and verified: %s (%d bytes)", resolved, ver["size"])
        return ok(
            f"File '{resolved.name}' created successfully.",
            data={"path": str(resolved), "size": ver["size"], "name": resolved.name, "verification": ver}
        )
    except Exception as exc:
        log.error("Failed to create file '%s': %s", raw_target, exc)
        return fail(f"Failed to create file '{raw_target}': {exc}", error=str(exc))


def create_csv(
    path: str = "",
    filename: str = "",
    file_name: str = "",
    name: str = "",
    headers: list[str] | None = None,
    rows: list[list] | None = None
) -> dict:
    """
    Create a CSV file with headers and rows, then verify physical existence.
    Defaults to M:\\Generated\\Excel\\ if no directory is specified.
    """
    raw_target = path or filename or file_name or name or "data.csv"
    try:
        from utils.workspace import resolve_output_path, verify_file_on_disk
        resolved = resolve_output_path(raw_target, category="excel", extension=".csv")
        resolved.parent.mkdir(parents=True, exist_ok=True)

        with open(resolved, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            if rows:
                writer.writerows(rows)

        # Physical verification
        ver = verify_file_on_disk(resolved, expected_extension=".csv", min_bytes=0)
        if not ver["verified"]:
            return fail(f"Physical verification failed: CSV file '{resolved.name}' was not created on disk.")

        return ok(
            f"CSV file '{resolved.name}' created successfully.",
            data={"path": str(resolved), "size": ver["size"], "rows": len(rows or []), "verification": ver}
        )
    except Exception as exc:
        return fail(f"Failed to create CSV file '{raw_target}': {exc}", error=str(exc))


def download_file(
    url: str = "",
    filename: str = "",
    file_name: str = "",
    destination: str = "",
    target_path: str = "",
) -> dict:
    """
    Download a file from a URL to the permanent workspace (M:\\Downloads\\ by default)
    and verify physical existence and size on disk.
    """
    if not url:
        return fail("Please specify the URL of the file to download.")

    try:
        import urllib.request
        from urllib.parse import urlparse
        from utils.workspace import resolve_output_path, verify_file_on_disk, DOWNLOADS_DIR

        # Derive filename if not specified
        raw_name = filename or file_name or target_path or destination or ""
        if not raw_name:
            parsed = urlparse(url)
            derived = os.path.basename(parsed.path)
            raw_name = derived if derived else "downloaded_file"

        # Resolve destination under M:\Downloads\
        resolved = resolve_output_path(raw_name, category="downloads", requested_path=destination or target_path)
        resolved.parent.mkdir(parents=True, exist_ok=True)

        log.info("Downloading file from '%s' to '%s'", url, resolved)

        # Stream download with User-Agent
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VOX-AI-Downloader/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as response, open(resolved, "wb") as out_file:
            chunk_size = 16384
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)

        # Empirical physical verification
        ver = verify_file_on_disk(resolved, min_bytes=1)
        if not ver["verified"]:
            return fail(f"Download verification failed: {ver['error']}", error=ver["error"])

        log.info("Download completed and verified: %s (%d bytes)", resolved, ver["size"])
        return ok(
            f"File '{resolved.name}' downloaded successfully to '{resolved}'.",
            data={"path": str(resolved), "size": ver["size"], "url": url, "filename": resolved.name, "verification": ver}
        )
    except Exception as exc:
        log.error("Download failed for URL '%s': %s", url, exc)
        return fail(f"Failed to download file from '{url}': {exc}", error=str(exc))


def save_image(
    image_data: bytes | str | None = None,
    filename: str = "",
    file_name: str = "",
    prompt: str = "",
) -> dict:
    """
    Save an image to M:\\Generated\\Images\\ and physically verify disk existence.
    """
    try:
        from utils.workspace import resolve_output_path, verify_file_on_disk
        raw_name = filename or file_name or (f"{safe_filename(prompt)}.png" if prompt else "generated_image.png")
        resolved = resolve_output_path(raw_name, category="images", extension=".png")
        resolved.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(image_data, bytes):
            resolved.write_bytes(image_data)
        elif isinstance(image_data, str) and image_data:
            import base64
            clean_b64 = image_data.split(",")[-1]
            resolved.write_bytes(base64.b64decode(clean_b64))
        else:
            # Create a simple placeholder image canvas if none provided
            from PIL import Image, ImageDraw, ImageFont  # type: ignore
            img = Image.new("RGB", (800, 600), color=(20, 25, 40))
            draw = ImageDraw.Draw(img)
            draw.text((50, 280), f"VOX AI Generated Image: {prompt or 'Asset'}", fill=(100, 200, 255))
            img.save(str(resolved))

        ver = verify_file_on_disk(resolved, expected_extension=".png", min_bytes=1)
        if not ver["verified"]:
            return fail(f"Image save verification failed: {ver['error']}", error=ver["error"])

        return ok(
            f"Image saved successfully to '{resolved}'.",
            data={"path": str(resolved), "size": ver["size"], "name": resolved.name, "verification": ver}
        )
    except Exception as exc:
        return fail(f"Failed to save image: {exc}", error=str(exc))


def list_files(directory: str = "", pattern: str = "*") -> dict:
    """List files in a directory, optionally filtered by a glob pattern."""
    try:
        from utils.workspace import DEFAULT_WORKSPACE
        target_dir = directory or str(DEFAULT_WORKSPACE)
        resolved = _resolve_folder(target_dir)
        if resolved is None or not resolved.exists():
            return fail(f"Directory not found: {directory!r}")
        files = [f.name for f in sorted(resolved.glob(pattern)) if f.is_file()]
        dirs = [d.name for d in sorted(resolved.glob("*/")) if d.is_dir()]
        return ok(
            f"Listed {len(files)} files and {len(dirs)} folders in {resolved.name}.",
            data={"files": files, "folders": dirs, "path": str(resolved)}
        )
    except Exception as exc:
        return fail(str(exc), error=str(exc))


def create_folder(path: str = "", folder_name: str = "", name: str = "") -> dict:
    """Create a new folder (including parent directories) and verify existence."""
    target = path or folder_name or name or ""
    if not target:
        return fail("Please specify the folder name or path to create.")
    try:
        p = Path(target)
        if not p.is_absolute() and len(p.parts) == 1:
            from utils.workspace import DEFAULT_WORKSPACE, PROJECTS_DIR
            resolved = PROJECTS_DIR / target
        else:
            resolved = expand_path(target)

        resolved.mkdir(parents=True, exist_ok=True)
        if not resolved.exists() or not resolved.is_dir():
            return fail(f"Physical verification failed: Folder '{resolved}' was not created.")
        return ok(f"Folder created: {resolved}", data={"path": str(resolved)})
    except Exception as exc:
        return fail(f"Cannot create folder: {exc}", error=str(exc))


def delete_file(path: str) -> dict:
    """
    Delete a file. This is a DANGEROUS action — caller must confirm first.
    """
    try:
        resolved = expand_path(path)
        if not resolved.exists():
            return fail(f"File not found: {path!r}")
        resolved.unlink()
        if resolved.exists():
            return fail(f"Failed to delete file '{resolved.name}'.")
        return ok(f"File deleted: {resolved.name}", data={"path": str(resolved)})
    except Exception as exc:
        return fail(f"Cannot delete file: {exc}", error=str(exc))


def delete_folder(path: str) -> dict:
    """
    Delete a folder and all contents. DANGEROUS — requires confirmation.
    """
    import shutil
    try:
        resolved = expand_path(path)
        if not resolved.exists():
            return fail(f"Folder not found: {path!r}")
        shutil.rmtree(str(resolved))
        if resolved.exists():
            return fail(f"Failed to delete folder '{resolved.name}'.")
        return ok(f"Folder deleted: {resolved}", data={"path": str(resolved)})
    except Exception as exc:
        return fail(f"Cannot delete folder: {exc}", error=str(exc))


def search_files(query: str, directory: str = "", pattern: str = "*", recursive: bool = True) -> dict:
    """Search for files matching a query in name or content."""
    try:
        resolved = _resolve_folder(directory) if directory else Path.cwd()
        if resolved is None or not resolved.exists():
            resolved = Path.cwd()

        matched_files = []
        glob_fn = resolved.rglob if recursive else resolved.glob
        for p in glob_fn(pattern):
            if p.is_file() and not any(part.startswith((".", "__pycache__", "node_modules", ".venv")) for part in p.parts):
                if query.lower() in p.name.lower():
                    matched_files.append({"name": p.name, "path": str(p), "match": "filename"})
                elif p.stat().st_size < 500_000:
                    try:
                        content = p.read_text(encoding="utf-8", errors="ignore")
                        if query.lower() in content.lower():
                            matched_files.append({"name": p.name, "path": str(p), "match": "content"})
                    except Exception:
                        pass
            if len(matched_files) >= 20:
                break

        return ok(
            f"Found {len(matched_files)} matching file(s) for '{query}'.",
            data={"results": matched_files, "query": query, "count": len(matched_files)}
        )
    except Exception as exc:
        return fail(f"File search failed: {exc}", error=str(exc))


def edit_file(path: str, old_text: str, new_text: str, validate_syntax: bool = True) -> dict:
    """
    Safely edit a file by replacing old_text with new_text.
    Never blindly replaces: reads target file first, checks presence, applies edit, validates syntax for python files.
    """
    try:
        resolved = expand_path(path)
        if not resolved.exists():
            return fail(f"File not found: {path!r}")
        if not resolved.is_file():
            return fail(f"Path is not a file: {path!r}")

        original = resolved.read_text(encoding="utf-8", errors="replace")
        if old_text not in original:
            return fail(f"Target text not found in '{resolved.name}'. File was not modified.")

        updated = original.replace(old_text, new_text, 1)

        # Syntax check for Python files
        if validate_syntax and resolved.suffix.lower() == ".py":
            import ast
            try:
                ast.parse(updated, filename=resolved.name)
            except SyntaxError as syn_err:
                return fail(f"Syntax validation failed on proposed edit: {syn_err}. File was not saved.", error=str(syn_err))

        resolved.write_text(updated, encoding="utf-8")
        return ok(
            f"File '{resolved.name}' successfully edited and verified.",
            data={"path": str(resolved), "chars": len(updated)}
        )
    except Exception as exc:
        return fail(f"Failed to edit file '{path}': {exc}", error=str(exc))


# ── Path Resolution ───────────────────────────────────────────

def _resolve_folder(path_input: str) -> Path | None:
    """
    Convert natural-language folder names to real paths.
    """
    lower = path_input.lower().strip()

    # Check FOLDER_MAPPINGS shortcuts
    for key, mapped in FOLDER_MAPPINGS.items():
        if key in lower:
            if mapped.startswith("::"):
                # Windows CLSID — open via shell
                try:
                    subprocess.Popen(f'explorer.exe shell:{mapped}', shell=True)
                    return Path("~").expanduser()  # Return home as placeholder
                except Exception:
                    return None
            return Path(mapped.replace("~", str(Path.home()))).resolve()

    # Try direct expansion
    try:
        resolved = expand_path(path_input)
        if resolved.exists():
            return resolved
    except Exception:
        pass

    # Try as drive letter
    if len(path_input) == 1 and path_input.isalpha():
        drive = Path(f"{path_input.upper()}:\\")
        if drive.exists():
            return drive

    return None
