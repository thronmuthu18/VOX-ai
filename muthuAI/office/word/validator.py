"""
MuthuAI Phase 5 — office/word/validator.py

Word file validation component.
Ensures created .docx files exist and can be opened cleanly by python-docx.
"""

from __future__ import annotations
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.office.word.validator")


class WordValidator:
    """
    Validates created Word document files (.docx).
    """

    def validate(self, file_path: str | Path) -> bool:
        p = Path(file_path).resolve()
        if not p.exists() or p.stat().st_size == 0:
            log.error("Word validation failed: File %s does not exist or is empty.", p)
            return False

        try:
            from docx import Document
            doc = Document(str(p))
            # Check non-empty document structure
            has_content = len(doc.paragraphs) > 0 or len(doc.tables) > 0
            if not has_content:
                log.warning("Word document %s contains no paragraphs or tables.", p.name)
            log.info("Word document %s validated successfully.", p.name)
            return True
        except Exception as exc:
            log.error("Word validation error for %s: %s", p.name, exc)
            return False
