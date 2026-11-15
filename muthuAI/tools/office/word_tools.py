"""
MuthuAI Phase 5 — tools/office/word_tools.py

Word document (.docx) creation tools with validated output.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from office.word.creator import WordCreator
from office.word.validator import WordValidator


class CreateWordTool(BaseTool):
    name = "create_word"
    description = "Create a Word document (.docx) with title, section headings, paragraphs, bullet points, and tables."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "default": "document.docx", "description": "Word filename (e.g., 'project_report.docx')."},
            "save_dir": {"type": "string", "default": "data/documents"},
            "title": {"type": "string", "default": "Document Title"},
            "headings": {"type": "array", "description": "List of [Heading, Text] pairs."},
            "paragraphs": {"type": "array", "items": {"type": "string"}, "description": "List of body paragraphs."},
            "bullet_points": {"type": "array", "items": {"type": "string"}},
            "table_data": {"type": "array", "description": "Table rows."}
        },
        "required": ["file_name"]
    }

    def execute(self, file_name: str = "document.docx", save_dir: str = "data/documents", title: str = "Document Title", headings: list | None = None, paragraphs: list[str] | None = None, bullet_points: list[str] | None = None, table_data: list[list] | None = None, **kwargs) -> ToolResult:
        creator = WordCreator()
        res = creator.create(
            file_name=file_name,
            save_dir=save_dir,
            title=title,
            headings=headings,
            paragraphs=paragraphs,
            bullet_points=bullet_points,
            table_data=table_data
        )

        if not res["success"]:
            return ToolResult.fail(res["message"])

        # Validate file output
        validator = WordValidator()
        if not validator.validate(res["file_path"]):
            return ToolResult.fail(f"Word document generation failed validation check: {res['file_name']}")

        return ToolResult.ok(res["message"], file_path=res["file_path"], file_name=res["file_name"])
