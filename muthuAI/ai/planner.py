"""
MuthuAI Phase 5 — ai/planner.py

Gemini Intent Planner & Multi-Step Task Decomposer for Windows Desktop, Browser, RAG, Memory, and Office Tools.
"""

from __future__ import annotations
import json
import re
from typing import TYPE_CHECKING

from tools.registry import ToolRegistry
from utils.logger import get_logger

if TYPE_CHECKING:
    from ai.gemini_client import GeminiClient

log = get_logger("muthuai.planner")

# Deterministic fast-path regex rules (Tamil, English, Tanglish)
_FAST_PATH_RULES: list[tuple[re.Pattern, str, dict]] = [
    # System Volume
    (re.compile(r"\b(volume up|volume increase|increase volume|sound jaasthi|volume அதிகப்படுத்து)\b", re.I), "volume_up", {"step": 10}),
    (re.compile(r"\b(volume down|volume decrease|decrease volume|sound kammi|volume குறை)\b", re.I), "volume_down", {"step": 10}),
    (re.compile(r"\b(mute|unmute|sound mute|mute பண்ணு)\b", re.I), "mute_volume", {}),
    # System Date/Time
    (re.compile(r"\b(what time|time enna|time என்ன|current time|tell me the time)\b", re.I), "get_time", {}),
    (re.compile(r"\b(what date|today['\s]*s date|date enna|date என்ன|today date)\b", re.I), "get_date", {}),
    # Windows Launchers
    (re.compile(r"\b(task manager open|open task manager)\b", re.I), "open_task_manager", {}),
    (re.compile(r"\b(control panel open|open control panel)\b", re.I), "open_control_panel", {}),
    (re.compile(r"\b(settings open|open settings|open windows settings)\b", re.I), "open_settings", {}),
    (re.compile(r"\b(cmd open|open cmd|command prompt open|open command prompt)\b", re.I), "open_command_prompt", {}),
    # Browser Fast Path
    (re.compile(r"\b(open browser|browser open|launch browser)\b", re.I), "open_browser", {}),
    (re.compile(r"\b(open google|google open|google open pannu)\b", re.I), "open_website", {"website_name": "Google"}),
    (re.compile(r"\b(open youtube|youtube open|youtube open pannu)\b", re.I), "open_website", {"website_name": "YouTube"}),
    (re.compile(r"\b(open github|github open|github open pannu)\b", re.I), "open_website", {"website_name": "GitHub"}),
    (re.compile(r"\b(open instagram|instagram open|instagram open pannu)\b", re.I), "open_website", {"website_name": "Instagram"}),
    (re.compile(r"\b(open flipkart|flipkart open|flipkart open pannu)\b", re.I), "open_website", {"website_name": "Flipkart"}),
    (re.compile(r"\b(scroll down|keela scroll|keela scroll pannu)\b", re.I), "browser_scroll", {"direction": "down"}),
    (re.compile(r"\b(scroll up|mele scroll|mele scroll pannu)\b", re.I), "browser_scroll", {"direction": "up"}),
    # Memory Commands
    (re.compile(r"\b(what do you remember|show my saved preferences|show memory|saved preferences)\b", re.I), "show_memory", {}),
]


class AgentPlanner:
    """
    Translates user text into structured tool plans and decomposes multi-step productivity tasks.
    """

    def __init__(self, gemini_client: "GeminiClient" | None, registry: ToolRegistry) -> None:
        self._gemini = gemini_client
        self._registry = registry

    def plan(self, user_text: str) -> list[dict]:
        """
        Determine which tool(s) should be executed in sequence.
        Returns a list of dicts: [{"tool": str, "arguments": dict}]
        """
        text_clean = user_text.strip()

        # ── 1. Fast Path Check ───────────────────────────────
        fast_tool = self._check_fast_path(text_clean)
        if fast_tool:
            log.info("Fast path triggered: %s", str(fast_tool))
            if isinstance(fast_tool, list):
                return fast_tool
            return [fast_tool]

        # Explicit Memory Command Fast Checks
        if text_clean.lower().startswith("remember that ") or text_clean.lower().startswith("remember "):
            fact = text_clean[8:].strip() if text_clean.lower().startswith("remember ") else text_clean[14:].strip()
            if fact:
                return [{"tool": "remember_fact", "arguments": {"fact": fact}}]

        if text_clean.lower().startswith("forget that ") or text_clean.lower().startswith("forget "):
            query = text_clean[6:].strip() if text_clean.lower().startswith("forget ") else text_clean[12:].strip()
            if query:
                return [{"tool": "forget_fact", "arguments": {"query": query}}]

        # ── 2. Gemini Slow Path & Multi-Step Decomposer ──────
        if self._gemini is None:
            return []

        return self._plan_with_gemini(text_clean)

    def _check_fast_path(self, text: str) -> dict | list[dict] | None:
        """Check if query matches a 0ms deterministic rule."""
        from agent.command_router import route_command
        routed = route_command(text)
        if routed:
            if isinstance(routed, list):
                valid_list = [r for r in routed if isinstance(r, dict) and self._registry.has(r.get("tool", ""))]
                if valid_list:
                    return valid_list
            elif isinstance(routed, dict) and self._registry.has(routed.get("tool", "")):
                return routed

        for pattern, tool_name, default_args in _FAST_PATH_RULES:
            if pattern.search(text) and self._registry.has(tool_name):
                return {"tool": tool_name, "arguments": default_args}
        return None

    def _plan_with_gemini(self, text: str) -> list[dict]:
        """Use Gemini to select appropriate tool(s) and decompose multi-step tasks."""
        available_tools = self._registry.to_tool_schemas()
        if not available_tools:
            return []

        prompt = (
            "You are the Intent Planner and Multi-Step Task Decomposer for VOX AI, a Windows desktop AI Agent.\n"
            "The user speaks in English, Tamil, or Tanglish (Tamil+English mixed).\n\n"
            "Return ONE of:\n"
            "1. Empty array [] — if the input is purely conversational (question/definition/explanation).\n"
            "2. JSON array of tool calls — for Windows actions, browser, app control, file creation, etc.\n\n"
            f"User input: \"{text}\"\n\n"
            f"Available tools:\n{json.dumps(available_tools, indent=2)}\n\n"
            "STRICT RULES:\n"
            "- For multi-step commands return ALL steps in order.\n"
            "- For browser tasks: ALWAYS open Chrome before navigation steps.\n"
            "- For YouTube: open_application(chrome) -> open_website(YouTube) -> search_youtube -> play_youtube.\n"
            "- Tanglish verbs: open panni=open, search panni=search, play panni=play, -la=in/on.\n"
            "- Example: 'Chrome open panni YouTube-la Python tutorial search panni play pannu'\n"
            "  -> [{open chrome}, {open youtube}, {search youtube: Python tutorial}, {play youtube}]\n"
            "- Return ONLY valid JSON array. No markdown. No explanation. No extra text.\n"
            "- Never use tool names not in the available tools list.\n"
        )

        try:
            response_text = self._gemini.generate_response(prompt, conversation_history=[])
            clean = response_text.strip()
            if clean.startswith("```json"):
                clean = clean.replace("```json", "").replace("```", "").strip()
            elif clean.startswith("```"):
                clean = clean.replace("```", "").strip()

            parsed = json.loads(clean)
            if isinstance(parsed, list):
                valid_plans = []
                for item in parsed:
                    if isinstance(item, dict) and "tool" in item and self._registry.has(item["tool"]):
                        valid_plans.append({
                            "tool": item["tool"],
                            "arguments": item.get("arguments", {})
                        })
                log.info("Gemini multi-step plan generated (%d steps): %s", len(valid_plans), str(valid_plans))
                return valid_plans
        except Exception as exc:
            log.warning("Gemini planning failed/parsed non-JSON (%s). Proceeding as conversational.", exc)

        return []
