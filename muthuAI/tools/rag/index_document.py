"""
MuthuAI Phase 4 — tools/rag/index_document.py

Tool to ingest and index PDF, DOCX, TXT, or MD documents/folders into personal RAG knowledge base.
"""

from __future__ import annotations
from pathlib import Path
from tools.base import BaseTool, ToolResult, PermissionLevel
# pyrefly: ignore [missing-import]
from rag.pipeline import RAGPipeline
from utils.logger import get_logger

log = get_logger("muthuai.tools.index_document")


class IndexDocumentTool(BaseTool):
    name = "index_document"
    description = "Ingest and index a PDF, DOCX, TXT, or Markdown document/folder into the personal RAG knowledge base."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "target_path": {
                "type": "string",
                "description": "Path to document or folder to index (e.g. 'data/documents', 'compiler_notes.pdf')."
            }
        },
        "required": ["target_path"]
    }

    def execute(self, target_path: str = "", **kwargs) -> ToolResult:
        if not target_path:
            return ToolResult.fail("Please specify a document or folder path to index.")

        pipeline = RAGPipeline()
        report = pipeline.ingest(target_path)

        if report.get("success"):
            return ToolResult.ok(report["message"], data=report)
        return ToolResult.fail(report.get("message", "Ingestion failed."))
