"""
MuthuAI Phase 4 — rag/ingestion/file_router.py

File router to detect files/directories and route them to appropriate document loaders.
"""

from __future__ import annotations
from pathlib import Path
from rag.ingestion.loader import DocumentLoader
from utils.logger import get_logger

log = get_logger("muthuai.rag.file_router")

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown", ".csv"}


class FileRouter:
    """
    Routes files or directories to DocumentLoader.
    """

    def __init__(self, loader: DocumentLoader | None = None) -> None:
        self._loader = loader or DocumentLoader()

    def route_path(self, target_path: str | Path) -> list[dict]:
        """
        Process a single file or an entire directory.
        Returns list of extracted pages/sections.
        """
        p = Path(target_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Path does not exist: {p}")

        if p.is_file():
            if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                return self._loader.load(p)
            else:
                log.warning("Skipping unsupported file extension: %s", p.name)
                return []

        # Directory ingestion
        all_pages = []
        for item in p.rglob("*"):
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    pages = self._loader.load(item)
                    all_pages.extend(pages)
                except Exception as exc:
                    log.warning("Could not ingest file %s: %s", item.name, exc)

        log.info("Ingested %d total page/section blocks from directory %s", len(all_pages), p.name)
        return all_pages
