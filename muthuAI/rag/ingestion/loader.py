"""
MuthuAI Phase 4 — rag/ingestion/loader.py

Document Ingestion Loaders: PDF, TXT, DOCX, Markdown.
Extracts clean text and page/section metadata.
"""

from __future__ import annotations
import os
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.rag.loader")


class DocumentLoader:
    """
    Unified Loader for PDF, TXT, DOCX, and Markdown files.
    """

    def load(self, file_path: str | Path) -> list[dict]:
        """
        Load a file and return a list of extracted pages/sections:
        [{"text": str, "page_number": int, "section": str, "file_name": str, "file_path": str, "file_type": str}]
        """
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")

        ext = p.suffix.lower()
        log.info("Loading document: %s (type=%s)", p.name, ext)

        if ext == ".pdf":
            return self._load_pdf(p)
        elif ext == ".docx":
            return self._load_docx(p)
        elif ext in (".txt", ".md", ".markdown"):
            return self._load_text(p)
        elif ext == ".csv":
            return self._load_csv(p)
        else:
            raise ValueError(f"Unsupported file format: '{ext}'. Supported: .pdf, .docx, .txt, .md, .csv")

    # Alias for backward compatibility
    load_file = load

    def _load_pdf(self, path: Path) -> list[dict]:
        pages = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().strip()
                if text:
                    pages.append({
                        "text": text,
                        "page_number": page_num + 1,
                        "section": f"Page {page_num + 1}",
                        "file_name": path.name,
                        "file_path": str(path),
                        "file_type": "pdf"
                    })
            doc.close()
        except Exception as exc:
            log.error("Failed to load PDF %s: %s", path.name, exc)
        return pages

    def _load_docx(self, path: Path) -> list[dict]:
        sections = []
        try:
            import docx
            doc = docx.Document(str(path))
            current_section = "Document Content"
            current_paras = []

            for p in doc.paragraphs:
                txt = p.text.strip()
                if not txt:
                    continue
                if p.style.name.startswith("Heading"):
                    if current_paras:
                        sections.append({
                            "text": "\n".join(current_paras),
                            "page_number": len(sections) + 1,
                            "section": current_section,
                            "file_name": path.name,
                            "file_path": str(path),
                            "file_type": "docx"
                        })
                        current_paras = []
                    current_section = txt
                else:
                    current_paras.append(txt)

            if current_paras:
                sections.append({
                    "text": "\n".join(current_paras),
                    "page_number": len(sections) + 1,
                    "section": current_section,
                    "file_name": path.name,
                    "file_path": str(path),
                    "file_type": "docx"
                })
        except Exception as exc:
            log.error("Failed to load DOCX %s: %s", path.name, exc)

        return sections

    def _load_text(self, path: Path) -> list[dict]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                return []
            return [{
                "text": text,
                "page_number": 1,
                "section": "Full Document",
                "file_name": path.name,
                "file_path": str(path),
                "file_type": path.suffix.lstrip(".")
            }]
        except Exception as exc:
            log.error("Failed to load text file %s: %s", path.name, exc)
            return []

    def _load_csv(self, path: Path) -> list[dict]:
        try:
            import csv
            lines = []
            with open(path, mode="r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        lines.append(" | ".join(row))
            text = "\n".join(lines).strip()
            if not text:
                return []
            return [{
                "text": text,
                "page_number": 1,
                "section": "CSV Table Data",
                "file_name": path.name,
                "file_path": str(path),
                "file_type": "csv"
            }]
        except Exception as exc:
            log.error("Failed to load CSV file %s: %s", path.name, exc)
            return []
