"""
MuthuAI Phase 3 — tools/browser/search_web.py

Tool to search the web (Google / DuckDuckGo) for information or news.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from retrieval.web_search import WebSearcher


class SearchWebTool(BaseTool):
    name = "web_search"
    description = "Search Google or DuckDuckGo for live web information, tutorials, or current news."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (e.g. 'Python tutorial', 'latest AI news', 'React interview questions')."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        if not query:
            return ToolResult.fail("Please specify a search query.")

        searcher = WebSearcher()
        results = searcher.search(query, max_results=5)

        if not results:
            return ToolResult.fail(f"No search results found for '{query}'.")

        first_title = results[0]["title"]
        return ToolResult.ok(
            f"Found {len(results)} web results for '{query}'. First result: '{first_title}'.",
            results=results
        )

