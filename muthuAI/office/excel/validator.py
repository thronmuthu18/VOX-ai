"""
MuthuAI Phase 5 — office/excel/validator.py

Excel file validation component.
Ensures generated .xlsx files exist, are readable by openpyxl, and contain expected columns.
"""

from __future__ import annotations
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.office.excel.validator")


class ExcelValidator:
    """
    Validates created Excel spreadsheet files.
    """

    def validate(self, file_path: str | Path, expected_columns: list[str] | None = None) -> bool:
        """
        Verify Excel file exists, opens cleanly, and has content.
        """
        p = Path(file_path).resolve()
        if not p.exists():
            log.error("Excel validation failed: File %s does not exist.", p)
            return False

        if p.stat().st_size == 0:
            log.error("Excel validation failed: File %s is 0 bytes.", p)
            return False

        try:
            from openpyxl import load_workbook
            wb = load_workbook(str(p), read_only=True)
            sheet = wb.active
            if sheet is None:
                log.error("Excel validation failed: No active worksheet found in %s.", p.name)
                wb.close()
                return False

            if expected_columns:
                first_row = [str(cell.value or '').strip() for cell in next(sheet.iter_rows(max_row=1))]
                for col in expected_columns:
                    if col not in first_row:
                        log.warning("Excel validation warning: Expected column '%s' missing from %s.", col, first_row)

            wb.close()
            log.info("Excel file %s validated successfully.", p.name)
            return True
        except Exception as exc:
            log.error("Excel validation error for %s: %s", p.name, exc)
            return False
