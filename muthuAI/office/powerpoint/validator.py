"""
MuthuAI Phase 5 — office/powerpoint/validator.py

PowerPoint file validation component.
Ensures created .pptx files exist, open cleanly, and match expected slide count.
"""

from __future__ import annotations
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.office.powerpoint.validator")


class PowerPointValidator:
    """
    Validates created PowerPoint presentation files (.pptx).
    """

    def validate(self, file_path: str | Path, expected_min_slides: int = 1) -> bool:
        p = Path(file_path).resolve()
        if not p.exists() or p.stat().st_size == 0:
            log.error("PowerPoint validation failed: File %s does not exist or is empty.", p)
            return False

        try:
            from pptx import Presentation
            prs = Presentation(str(p))
            slide_count = len(prs.slides)
            if slide_count < expected_min_slides:
                log.warning("PowerPoint validation warning: %s has %d slides (expected min %d).", p.name, slide_count, expected_min_slides)
                return False

            log.info("PowerPoint file %s (%d slides) validated successfully.", p.name, slide_count)
            return True
        except Exception as exc:
            log.error("PowerPoint validation error for %s: %s", p.name, exc)
            return False
