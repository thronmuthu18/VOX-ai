"""
MuthuAI Phase 5 — tools/office/excel_tools.py

Excel creation and reading tools with validated output.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from office.excel.creator import ExcelCreator
from office.excel.validator import ExcelValidator
from office.excel.reader import ExcelReader


class CreateExcelTool(BaseTool):
    name = "create_excel"
    description = "Create a styled Excel spreadsheet (.xlsx) with columns, rows, formulas, and optional auto-average row."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "default": "spreadsheet.xlsx", "description": "Excel filename (e.g. 'students.xlsx')."},
            "save_dir": {"type": "string", "default": "data/documents", "description": "Destination directory path."},
            "sheet_name": {"type": "string", "default": "Sheet1"},
            "columns": {"type": "array", "items": {"type": "string"}, "description": "List of column names."},
            "rows": {"type": "array", "description": "List of row arrays."},
            "add_average_row": {"type": "boolean", "default": False, "description": "Calculate average formula row."}
        },
        "required": ["file_name"]
    }

    def execute(self, file_name: str = "spreadsheet.xlsx", save_dir: str = "data/documents", sheet_name: str = "Sheet1", columns: list[str] | None = None, rows: list[list] | None = None, add_average_row: bool = False, **kwargs) -> ToolResult:
        creator = ExcelCreator()
        res = creator.create(
            file_name=file_name,
            save_dir=save_dir,
            sheet_name=sheet_name,
            columns=columns,
            rows=rows,
            add_average_row=add_average_row
        )

        if not res["success"]:
            return ToolResult.fail(res["message"])

        # Validate file output
        validator = ExcelValidator()
        if not validator.validate(res["file_path"], expected_columns=columns):
            return ToolResult.fail(f"Excel file generation failed validation check: {res['file_name']}")

        return ToolResult.ok(res["message"], file_path=res["file_path"], file_name=res["file_name"])


class ReadExcelTool(BaseTool):
    name = "read_excel"
    description = "Read columns and rows from an existing Excel spreadsheet file."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the Excel file to read."}
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str = "", **kwargs) -> ToolResult:
        if not file_path:
            return ToolResult.fail("Please specify an Excel file path.")

        reader = ExcelReader()
        res = reader.read(file_path)

        if res["success"]:
            return ToolResult.ok(f"Read Excel file '{res['file_name']}' ({res['row_count']} rows).", data=res)
        return ToolResult.fail(res["message"])
