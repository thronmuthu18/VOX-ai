"""
MuthuAI Phase 5 — tools/office/pdf_tools.py

PDF document (.pdf) creation tools with validated output.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from office.pdf.creator import PDFCreator
from office.pdf.validator import PDFValidator


class CreatePDFTool(BaseTool):
    name = "create_pdf"
    description = "Create a styled PDF document (.pdf) with title and paragraphs."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "default": "report.pdf", "description": "PDF filename (e.g. 'summary_report.pdf')."},
            "save_dir": {"type": "string", "default": "data/documents"},
            "title": {"type": "string", "default": "PDF Report"},
            "paragraphs": {"type": "array", "items": {"type": "string"}, "description": "Body paragraphs."}
        },
        "required": ["file_name"]
    }

    def execute(self, file_name: str = "report.pdf", save_dir: str = "data/documents", title: str = "PDF Report", paragraphs: list[str] | None = None, **kwargs) -> ToolResult:
        creator = PDFCreator()
        res = creator.create(
            file_name=file_name,
            save_dir=save_dir,
            title=title,
            paragraphs=paragraphs
        )

        if not res["success"]:
            return ToolResult.fail(res["message"])

        validator = PDFValidator()
        if not validator.validate(res["file_path"]):
            return ToolResult.fail(f"PDF generation failed validation check: {res['file_name']}")

        return ToolResult.ok(res["message"], file_path=res["file_path"], file_name=res["file_name"])
