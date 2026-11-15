"""
MuthuAI Phase 5 — office/excel/creator.py

Excel Workbook Creator & Formatter using openpyxl and pandas.
Creates styled spreadsheets with headers, rows, formulas, and auto-adjusted column widths.
"""

from __future__ import annotations
import os
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.office.excel.creator")


class ExcelCreator:
    """
    Creates styled Excel workbooks (.xlsx) with headers, rows, and formulas.
    """

    def create(
        self,
        file_name: str = "spreadsheet.xlsx",
        save_dir: str | Path = "data/documents",
        sheet_name: str = "Sheet1",
        columns: list[str] | None = None,
        rows: list[list] | None = None,
        add_average_row: bool = False,
        open_after: bool = False
    ) -> dict:
        """
        Create a styled Excel spreadsheet.
        Returns dict: {"success": bool, "file_path": str, "message": str}
        """
        save_path = Path(save_dir).resolve() / (file_name if file_name.endswith(".xlsx") else f"{file_name}.xlsx")
        save_path.parent.mkdir(parents=True, exist_ok=True)

        cols = columns or ["ID", "Name", "Score", "Status"]
        row_data = rows or []

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name

            # Styling constants
            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_fill = PatternFill("solid", fgColor="1F4E78")
            center_align = Alignment(horizontal="center", vertical="center")
            thin_border = Border(
                left=Side(style="thin", color="CCCCCC"),
                right=Side(style="thin", color="CCCCCC"),
                top=Side(style="thin", color="CCCCCC"),
                bottom=Side(style="thin", color="CCCCCC")
            )

            # Write headers
            ws.append(cols)
            for col_num in range(1, len(cols) + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align
                cell.border = thin_border

            # Write row data
            for r in row_data:
                ws.append(r)
                current_row = ws.max_row
                for c_idx in range(1, len(r) + 1):
                    cell = ws.cell(row=current_row, column=c_idx)
                    cell.border = thin_border
                    cell.alignment = center_align

            # Optional formula row for numeric column (e.g. Average)
            if add_average_row and len(row_data) > 0:
                avg_row_num = ws.max_row + 1
                ws.cell(row=avg_row_num, column=1, value="AVERAGE").font = Font(bold=True)
                # Apply AVERAGE formula to numeric columns
                for c_idx in range(2, len(cols) + 1):
                    col_letter = get_column_letter(c_idx)
                    formula = f"=AVERAGE({col_letter}2:{col_letter}{avg_row_num-1})"
                    cell = ws.cell(row=avg_row_num, column=c_idx, value=formula)
                    cell.font = Font(bold=True)
                    cell.border = thin_border

            # Auto-adjust column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

            wb.save(str(save_path))
            log.info("Excel spreadsheet created: %s", save_path)

            if open_after:
                try:
                    os.startfile(str(save_path))
                except Exception:
                    pass

            return {
                "success": True,
                "file_path": str(save_path),
                "file_name": save_path.name,
                "columns": cols,
                "row_count": len(row_data),
                "message": f"Excel spreadsheet '{save_path.name}' created successfully with {len(cols)} columns and {len(row_data)} rows."
            }

        except Exception as exc:
            log.error("Failed to create Excel file %s: %s", save_path.name, exc)
            return {"success": False, "file_path": "", "message": f"Could not create Excel file: {exc}"}
