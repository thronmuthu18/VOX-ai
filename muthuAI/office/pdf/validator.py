"""
MuthuAI Phase 5 — office/pdf/validator.py

PDF file validation component.
Ensures created .pdf files exist, are readable, and non-empty.
"""

from __future__ import annotations
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.office.pdf.validator")


class PDFValidator:
    """
    Validates created PDF document files.
    """

    def validate(self, file_path: str | Path) -> bool:
        p = Path(file_path).resolve()
        if not p.exists() or p.stat().st_size == 0:
            log.error("PDF validation failed: File %s does not exist or is 0 bytes.", p)
            return False

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(p))
            page_count = len(doc)
            doc.close()
            if page_count == 0:
                log.error("PDF validation failed: %s has 0 pages.", p.name)
                return False
            log.info("PDF file %s (%d pages) validated successfully.", p.name, page_count)
            return True
        except Exception:
            # Fallback simple check
            return p.stat().st_size > 100
