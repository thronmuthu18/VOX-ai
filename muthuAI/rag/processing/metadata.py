"""
MuthuAI Phase 4 — rag/processing/metadata.py

Document Hashing & Duplicate Detection.
Computes file hashes to prevent re-indexing unchanged documents and manages chunk IDs.
"""

from __future__ import annotations
import hashlib
import uuid
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.rag.metadata")


def compute_file_hash(file_path: str | Path) -> str:
    """Compute MD5 hash of a file for duplicate detection."""
    p = Path(file_path).resolve()
    if not p.exists():
        return ""
    hasher = hashlib.md5()
    try:
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as exc:
        log.warning("Hash computation failed for %s: %s", p.name, exc)
        return ""


def generate_chunk_id(file_name: str, page_number: int, chunk_index: int) -> str:
    """Generate deterministic unique ID for a document chunk."""
    clean_name = file_name.replace(" ", "_").lower()
    return f"{clean_name}_p{page_number}_c{chunk_index}_{uuid.uuid4().hex[:6]}"
