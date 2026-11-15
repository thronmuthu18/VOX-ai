"""
MuthuAI Phase 3 — tools/browser/youtube_tools.py

Dedicated YouTube search and video playback tools.
Inspects results to open and play the most relevant video.
"""

from __future__ import annotations
import urllib.parse
from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.manager import BrowserManager
from browser.interaction import BrowserController
from utils.logger import get_logger

log = get_logger("muthuai.tools.youtube")


class SearchYouTubeTool(BaseTool):
    name = "search_youtube"
    description = "Search YouTube for videos on a specific topic or lecture."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Topic or lecture to search on YouTube (e.g. 'Compiler design lecture', 'Python tutorial')."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        if not query:
            return ToolResult.fail("Please specify what to search on YouTube.")

        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"

        controller = BrowserController()
        try:
            controller.navigate(search_url)
            return ToolResult.ok(f"Searching YouTube for '{query}'.", query=query, url=search_url)
        except Exception as exc:
            return ToolResult.fail(f"Could not search YouTube: {exc}")


class PlayYouTubeTool(BaseTool):
    name = "play_youtube"
    description = "Search YouTube and play the most relevant video for a query or lecture."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Video topic, lecture, or song to play on YouTube."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        if not query:
            return ToolResult.fail("Please specify which video or topic to play.")

        controller = BrowserController()
        success, msg, video_url = controller.play_first_youtube_result(query)
        if success:
            return ToolResult.ok(msg, query=query, url=video_url)
        return ToolResult.fail(msg, query=query, url=video_url)

