"""
CHAMP Phase 2 — planner/voice_planner.py

VoiceAgentPlanner: Converts a single multi-step voice input into a TaskQueue
with dependency graph.

Pipeline:
  voice text
    → detect if multi-step
    → extract individual actions (Gemini or fast-path regex)
    → build Task objects with sequential dependencies
    → return TaskQueue

Supports English, Tamil, and Tanglish input natively.

Multi-step detection heuristics:
  - Multiple action verbs in one sentence
  - Conjunctions: "and", "then", "after that", "panni", "-la", "apram"
  - Comma-separated action clauses

Example:
  "Bro, open Chrome, open YouTube, search Python tutorial, play the first video."
  → 4 tasks: open_application → open_website → search_youtube → play_youtube
    where each task depends on the previous
"""

from __future__ import annotations
import json
import re
import uuid
from typing import TYPE_CHECKING, Any

from task_queue.task_model import Task, TaskStatus
from task_queue.task_queue import TaskQueue
from utils.logger import get_logger

if TYPE_CHECKING:
    from ai.gemini_client import GeminiClient
    from tools.registry import ToolRegistry

log = get_logger("muthuai.planner.voice_planner")


# ── Multi-step detection patterns ─────────────────────────────────────────────

# Connectors that signal a continuation to another action
_STEP_CONNECTORS = re.compile(
    r"""
    \b(
        and\s+then|then|after\s+that|next|also|followed\s+by|  # English
        panni|pannunga|panna|apram|piragu|konjam|              # Tanglish
        -la|-il                                                 # Tamil locative suffix
    )\b
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Repeated action verbs — strong signal of multi-step
_ACTION_VERBS = re.compile(
    r"\b(open|launch|start|close|search|play|scroll|send|create|make|"
    r"click|type|go to|navigate|find|"
    r"open\s+panni|search\s+panni|play\s+panni|"
    r"திற|தேடு|இயக்கு)\b",
    re.IGNORECASE,
)

# Minimum verb count to classify as multi-step
_MULTI_STEP_VERB_THRESHOLD = 2


def _is_multi_step(text: str) -> bool:
    """
    Heuristic: detect if a voice input describes multiple sequential actions.

    Returns True if:
    - 2+ distinct action verbs are found, OR
    - A step connector word is found AND at least 1 action verb exists
    """
    verb_matches = _ACTION_VERBS.findall(text)
    has_connector = bool(_STEP_CONNECTORS.search(text))

    if len(verb_matches) >= _MULTI_STEP_VERB_THRESHOLD:
        return True
    if has_connector and len(verb_matches) >= 1:
        return True
    return False


# ── Tanglish → English action normalization ───────────────────────────────────

_TANGLISH_NORMALIZERS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bopen\s+pann[ui]\b", re.I), "open"),
    (re.compile(r"\bsearch\s+pann[ui]\b", re.I), "search"),
    (re.compile(r"\bplay\s+pann[ui]\b", re.I), "play"),
    (re.compile(r"\bclose\s+pann[ui]\b", re.I), "close"),
]


def _normalize_tanglish(text: str) -> str:
    """Normalize Tanglish action phrases to plain English before Gemini parsing."""
    for pat, repl in _TANGLISH_NORMALIZERS:
        text = pat.sub(repl, text)
    return text


# ── Tool step description builders ───────────────────────────────────────────

def _describe(tool: str, args: dict) -> str:
    """Build a short human-readable description for a tool step."""
    if tool == "open_application":
        return f"Open {args.get('name', 'application')}"
    if tool in ("open_website", "open_browser"):
        return f"Open {args.get('website_name', args.get('url', 'website'))}"
    if tool == "search_google":
        return f"Search Google for '{args.get('query', '')}'"
    if tool in ("search_youtube", "browser_search", "search_web"):
        return f"Search for '{args.get('query', args.get('search_query', '...'))}'"
    if tool in ("play_youtube", "play_media"):
        return f"Play {args.get('query', args.get('video_title', 'video'))}"
    if tool in ("scroll", "browser_scroll"):
        return f"Scroll {args.get('direction', 'down')}"
    if tool in ("click", "browser_click"):
        target = args.get("target") or args.get("text") or args.get("selector") or "element"
        return f"Click '{target}'"
    if tool in ("type", "browser_type", "type_text"):
        return f"Type '{args.get('text', '')}'"
    if tool == "press_key":
        return f"Press {args.get('key', 'Enter')}"
    if tool == "back":
        return "Navigate back"
    if tool == "forward":
        return "Navigate forward"
    if tool == "refresh":
        return "Refresh page"
    if tool == "find_text":
        return f"Find text '{args.get('query', '')}'"
    if tool in ("get_page_state", "browser_read"):
        return "Inspect page state"
    if tool == "open_vscode":
        target = args.get("file_name") or args.get("path") or args.get("target") or "project"
        return f"Open VS Code with {target}"
    if tool in ("edit_code", "edit_file"):
        target = args.get("file_name") or args.get("path") or args.get("file_path") or "file"
        return f"Edit code in {target}"
    if tool == "search_files":
        return f"Search files for '{args.get('query', '')}'"
    if tool == "open_folder":
        return f"Open folder '{args.get('path', args.get('folder_name', ''))}'"
    if tool == "set_volume":
        return f"Set volume to {args.get('level', 50)}%"
    if tool == "explain_and_create_pdf":
        return f"Explain '{args.get('topic', '')}' and create PDF"
    if tool in ("desktop_press_key", "press_key"):
        return f"Press key '{args.get('key', 'Enter')}'"
    if tool == "whatsapp_send_message":
        return f"Send WhatsApp message to {args.get('phone_number', '')}"
    if tool == "whatsapp_call":
        return f"Initiate WhatsApp call to {args.get('phone_number', '')}"
    if tool == "open_instagram":
        return "Open Instagram"
    if tool == "open_instagram_reels":
        return "Open Instagram Reels"
    if tool == "instagram_next_reel":
        return "Navigate to next Instagram Reel"
    if tool == "instagram_stop":
        return "Stop/Pause Instagram Reel"
    if tool == "instagram_share_reel":
        return "Share Instagram Reel"
    if tool == "instagram_add_reel_to_story":
        return "Add Instagram Reel to Story"
    if tool == "read_emails":
        return f"Read {args.get('limit', 10)} emails from inbox"
    if tool in ("check_important_emails", "summarize_inbox"):
        return "Check and summarize important emails"
    if tool == "email_to_whatsapp_alert":
        return f"Send email summary alert to WhatsApp ({args.get('user_phone', '')})"
    if tool == "search_flipkart":
        return f"Search Flipkart for '{args.get('query', '')}'"
    if tool.startswith("create_"):
        name = tool.replace("create_", "").capitalize()
        return f"Create {name} '{args.get('file_name', args.get('filename', ''))}'"

    return tool.replace("_", " ").capitalize()




# ── Gemini multi-step planning prompt ────────────────────────────────────────

_PLANNER_PROMPT = """\
You are the Multi-Step Task Planner for VOX AI, a Windows desktop AI assistant.

The user gave a voice command in English, Tamil, or Tanglish that contains MULTIPLE actions.
Your job is to decompose it into individual sequential tool calls.

User input: "{text}"

Available tools:
{tools_json}

RULES:
1. Return a JSON array of tool call objects: [{{"tool": "tool_name", "arguments": {{...}}}}, ...]
2. Order matters — list steps in the order they should execute.
3. For browser tasks: open Chrome/browser first, then navigate, then search, then interact.
4. If a step requires a previous step (e.g. search needs browser open), list them in order.
5. Do NOT include conversational explanations. Output ONLY valid JSON array.
6. If the input is NOT multi-step, return a single-element array.
7. Never fabricate tool names — only use tools from the available list.

Example for "open Chrome, open YouTube, search Python tutorial, play first video":
[
  {{"tool": "open_application", "arguments": {{"name": "chrome"}}}},
  {{"tool": "open_website", "arguments": {{"website_name": "YouTube"}}}},
  {{"tool": "search_youtube", "arguments": {{"query": "Python tutorial"}}}},
  {{"tool": "play_youtube", "arguments": {{"query": "Python tutorial"}}}}
]

Now decompose: "{text}"
"""


class VoiceAgentPlanner:
    """
    Converts a single multi-step voice input into a TaskQueue.

    The resulting TaskQueue has:
    - One Task per action
    - Sequential dependencies: task N depends on task N-1
    - Human-readable descriptions for each task
    - Unique IDs for dependency cross-referencing

    Usage:
        planner = VoiceAgentPlanner(gemini_client, registry)
        queue = planner.build_plan("open Chrome, YouTube search, play first video")
    """

    def __init__(
        self,
        gemini_client: "GeminiClient | None",
        registry: "ToolRegistry",
    ) -> None:
        self._gemini = gemini_client
        self._registry = registry

    def is_multi_step(self, text: str) -> bool:
        """Public accessor for multi-step detection heuristic."""
        return _is_multi_step(text)

    def build_plan(self, user_text: str) -> TaskQueue:
        """
        Parse the user's multi-step voice input into a TaskQueue.

        Returns an empty TaskQueue if no actionable steps are found.
        """
        text = _normalize_tanglish(user_text.strip())

        # 1. Extract tool steps (Gemini or fast path)
        steps = self._extract_steps(text)

        if not steps:
            log.info("VoiceAgentPlanner: No steps extracted from %r", user_text)
            return TaskQueue()

        # 2. Build Task objects with sequential dependency chain
        queue = TaskQueue()
        prev_id: str | None = None

        for idx, step in enumerate(steps, start=1):
            tool = step.get("tool", "")
            args = step.get("arguments", {})

            task_id = f"task_{idx:03d}"
            deps = [prev_id] if prev_id else []

            task = Task(
                id=task_id,
                action=tool,
                parameters=args,
                dependencies=deps,
                description=_describe(tool, args),
                status=TaskStatus.PENDING,
            )
            queue.add(task)
            prev_id = task_id

        log.info(
            "VoiceAgentPlanner: Built %d-task queue from %r",
            len(queue), user_text
        )
        return queue

    def _extract_steps(self, text: str) -> list[dict]:
        """
        Extract ordered tool steps from the text using Gemini or fast-path.

        Returns list of {"tool": str, "arguments": dict} dicts.
        """
        # Try Gemini first (handles complex Tanglish + multi-step)
        if self._gemini:
            steps = self._plan_with_gemini(text)
            if steps:
                return steps

        # Fallback: fast-path single-step or multi-step via existing command_router
        from agent.command_router import route_command
        fast = route_command(text)
        if fast:
            if isinstance(fast, list):
                valid = [r for r in fast if isinstance(r, dict) and self._registry.has(r.get("tool", ""))]
                if valid:
                    return valid
            elif isinstance(fast, dict) and self._registry.has(fast.get("tool", "")):
                return [fast]

        return []

    def _plan_with_gemini(self, text: str) -> list[dict]:
        """Use Gemini to decompose multi-step input into ordered tool calls."""
        available_tools = self._registry.to_tool_schemas()
        if not available_tools:
            return []

        prompt = _PLANNER_PROMPT.format(
            text=text,
            tools_json=json.dumps(available_tools, indent=2, ensure_ascii=False)
        )

        try:
            raw = self._gemini.generate_response(prompt, conversation_history=[])
            clean = raw.strip()
            # Strip markdown fences if present
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            parsed = json.loads(clean)
            if not isinstance(parsed, list):
                log.warning("VoiceAgentPlanner: Gemini returned non-list: %r", clean[:200])
                return []

            valid_steps = []
            for item in parsed:
                if not isinstance(item, dict) or "tool" not in item:
                    continue
                tool_name = item["tool"]
                if not self._registry.has(tool_name):
                    log.warning("VoiceAgentPlanner: Gemini suggested unknown tool '%s' — skipping.", tool_name)
                    continue
                valid_steps.append({
                    "tool": tool_name,
                    "arguments": item.get("arguments", {}),
                })

            log.info(
                "VoiceAgentPlanner: Gemini produced %d valid steps from %d returned.",
                len(valid_steps), len(parsed)
            )
            return valid_steps

        except json.JSONDecodeError as exc:
            log.warning("VoiceAgentPlanner: Gemini JSON parse failed: %s — raw: %r", exc, raw[:200] if 'raw' in dir() else "N/A")
        except Exception as exc:
            log.warning("VoiceAgentPlanner: Gemini call failed: %s", exc)

        return []
