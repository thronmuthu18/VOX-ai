"""
MuthuAI Phase 5 — tools/office/powerpoint_tools.py

PowerPoint presentation (.pptx) creation tools with validated output.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from office.powerpoint.creator import PowerPointCreator
from office.powerpoint.validator import PowerPointValidator


class CreatePowerPointTool(BaseTool):
    name = "create_powerpoint"
    description = "Create a multi-slide PowerPoint presentation (.pptx) with title, subtitle, and content/bullet slides."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "default": "presentation.pptx", "description": "Presentation filename (e.g. 'ai_overview.pptx')."},
            "save_dir": {"type": "string", "default": "data/documents"},
            "title": {"type": "string", "default": "Presentation Title"},
            "subtitle": {"type": "string", "default": ""},
            "slides": {
                "type": "array",
                "description": "List of slide dicts: [{'title': 'Slide Title', 'content': 'Paragraph...', 'bullets': ['Item 1']}]"
            }
        },
        "required": ["file_name", "title"]
    }

    def execute(self, file_name: str = "presentation.pptx", save_dir: str = "data/documents", title: str = "Presentation Title", subtitle: str = "", slides: list[dict] | None = None, **kwargs) -> ToolResult:
        creator = PowerPointCreator()
        res = creator.create(
            file_name=file_name,
            save_dir=save_dir,
            title=title,
            subtitle=subtitle,
            slides=slides
        )

        if not res["success"]:
            return ToolResult.fail(res["message"])

        # Validate file output
        validator = PowerPointValidator()
        if not validator.validate(res["file_path"]):
            return ToolResult.fail(f"PowerPoint generation failed validation check: {res['file_name']}")

        return ToolResult.ok(res["message"], file_path=res["file_path"], file_name=res["file_name"], slide_count=res.get("slide_count", 0))
