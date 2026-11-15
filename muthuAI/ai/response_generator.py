"""
MuthuAI — ai/response_generator.py
Generates the final natural-language response for the user
after tool execution results are collected.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from ai.prompt_manager import (
    final_response_prompt,
    conversational_prompt,
    rag_response_prompt,
    web_search_response_prompt,
)
from utils.logger import get_logger

if TYPE_CHECKING:
    from ai.gemini_client import GeminiClient
    from memory.conversation_memory import ConversationMemory

log = get_logger(__name__)


class ResponseGenerator:
    """
    Generates human-readable, language-appropriate responses.

    Four response modes:
      1. conversational — no tools used, pure Gemini chat
      2. tool_result    — tools executed, summarise results
      3. rag            — answer from retrieved document chunks
      4. web_search     — answer from live web search results
    """

    def __init__(self, gemini: "GeminiClient", memory: "ConversationMemory"):
        self._gemini = gemini
        self._memory = memory

    def _call_gemini(self, prompt: str) -> str:
        """Send prompt to Gemini client using generate() or generate_response()."""
        if hasattr(self._gemini, "generate"):
            return self._gemini.generate(prompt)
        return self._gemini.generate_response(prompt, conversation_history=[])

    def conversational(self, user_text: str, lang: str = "en") -> str:
        """Direct conversational Gemini response (no tool execution)."""
        context = self._memory.get_context_string()
        prompt = conversational_prompt(user_text, context, lang)
        response = self._call_gemini(prompt)
        log.debug("Conversational response: %r", response[:100])
        return response

    def from_tool_results(
        self,
        user_text: str,
        tool_results: list[dict[str, Any]],
        lang: str = "en",
    ) -> str:
        """Generate response summarising tool execution outcomes."""
        context = self._memory.get_context_string()
        results_text = _format_tool_results(tool_results)
        prompt = final_response_prompt(user_text, results_text, context, lang)
        response = self._call_gemini(prompt)
        log.debug("Tool result response: %r", response[:100])
        return response

    def from_rag_chunks(
        self,
        user_text: str,
        chunks: list[dict[str, Any]],
        lang: str = "en",
    ) -> str:
        """Generate response from RAG-retrieved document chunks."""
        chunks_text = _format_rag_chunks(chunks)
        prompt = rag_response_prompt(user_text, chunks_text, lang)
        response = self._call_gemini(prompt)
        log.debug("RAG response: %r", response[:100])
        return response

    def from_web_results(
        self,
        user_text: str,
        search_results: list[dict[str, Any]],
        lang: str = "en",
    ) -> str:
        """Generate response from live web search results."""
        results_text = _format_web_results(search_results)
        prompt = web_search_response_prompt(user_text, results_text, lang)
        response = self._call_gemini(prompt)
        log.debug("Web search response: %r", response[:100])
        return response


# ── Formatters ───────────────────────────────────────────────

def _format_tool_results(results: list[dict[str, Any]]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        status = "✓" if r.get("success") else "✗"
        lines.append(f"{i}. [{status}] {r.get('message', '')} "
                     f"(tool: {r.get('tool', 'unknown')})")
    return "\n".join(lines) or "No tool results."


def _format_rag_chunks(chunks: list[dict[str, Any]]) -> str:
    parts = []
    for chunk in chunks:
        source = chunk.get("metadata", {}).get("source", "unknown")
        text = chunk.get("text", "")
        parts.append(f"[Source: {source}]\n{text}")
    return "\n\n".join(parts) or "No document content retrieved."


def _format_web_results(results: list[dict[str, Any]]) -> str:
    parts = []
    for r in results:
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("snippet", r.get("body", ""))
        parts.append(f"• {title}\n  {snippet}\n  URL: {url}")
    return "\n\n".join(parts) or "No web results found."
