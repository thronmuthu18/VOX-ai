"""
MuthuAI Phase 5 — office/excel/reader.py

Excel file reader: extracts columns and rows from .xlsx files.
"""

from __future__ import annotations
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.office.excel.reader")


class ExcelReader:
    """
    Reads existing Excel spreadsheet files into structured dictionary format.
    """

    def read(self, file_path: str | Path, max_rows: int = 50) -> dict:
        """
        Read Excel file and return columns and rows.
        """
        p = Path(file_path).resolve()
        if not p.exists():
            return {"success": False, "message": f"File not found: {p}"}

        try:
            from openpyxl import load_workbook
            wb = load_workbook(str(p), data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            wb.close()

            if not rows:
                return {"success": True, "columns": [], "rows": [], "row_count": 0}

            columns = [str(c or '') for c in rows[0]]
            data_rows = [list(r) for r in rows[1:max_rows+1]]

            return {
                "success": True,
                "file_name": p.name,
                "sheet_name": sheet.title,
                "columns": columns,
                "rows": data_rows,
                "row_count": len(rows) - 1
            }
        except Exception as exc:
            log.error("Failed to read Excel file %s: %s", p.name, exc)
            return {"success": False, "message": f"Could not read Excel file: {exc}"}
