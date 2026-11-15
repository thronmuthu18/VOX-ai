"""
MuthuAI Phase 4 — tools/rag/search_knowledge.py

Tool to search personal RAG document knowledge base for questions about notes, study material, or files.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from rag.retrieval.retriever import RAGRetriever


class SearchKnowledgeTool(BaseTool):
    name = "search_knowledge"
    description = "Search personal indexed documents/notes for relevant information to answer questions."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Question or topic to search in personal documents (e.g. 'Compiler design lexical analysis')."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        if not query:
            return ToolResult.fail("Please specify a search query.")

        retriever = RAGRetriever()
        chunks = retriever.retrieve(query, top_k=4)

        if not chunks:
            return ToolResult.fail(f"No relevant content found in your indexed documents for '{query}'.")

        first_source = chunks[0].get("metadata", {}).get("source", "Document")
        return ToolResult.ok(
            f"Found {len(chunks)} relevant document section(s). Primary source: {first_source}.",
            chunks=chunks
        )
