"""
CHAMP — agent/intent_router.py

Intent Router Module for CHAMP Windows Voice Personal AI Agent.
Routes normalized user inputs to either ACTION_MODE or CONVERSATION_MODE.

Architecture:
        INTENT ROUTER
              │
    ┌─────────┴─────────┐
    ┘                   ┘
CONVERSATION          ACTION
   MODE                MODE
    │                   │
    ┘                   ┘
 GEMINI              AGENT PLANNER

Fix log (2026-08-27):
  - Problem 4: Added web-search and real-time information patterns so queries
    like 'latest news', 'current price', 'search for ...', 'who won today'
    are routed to ACTION MODE (web retrieval) instead of CONVERSATION MODE.
"""

from __future__ import annotations
import re
from enum import Enum
from typing import TypedDict, Any
from agent.command_normalizer import NormalizedCommand
from agent.command_router import route_command
from utils.logger import get_logger

log = get_logger("muthuai.intent_router")


class IntentMode(str, Enum):
    ACTION = "ACTION"
    CONVERSATION = "CONVERSATION"


class IntentRoutingResult(TypedDict):
    mode: IntentMode
    command: str
    direct_plan: Any
    reason: str


# Intent patterns that clearly indicate ACTION MODE
_ACTION_PATTERNS: list[re.Pattern] = [
    # Application / App control verbs
    re.compile(r"\b(open|launch|start|close|minimize|maximize|focus|switch\s+to)\s+(chrome|youtube|google|excel|word|notepad|calculator|calc|vscode|vs code|code|whatsapp|settings|control panel|task manager|cmd|command prompt|explorer|browser|flipkart|instagram|camera)\b", re.I),
    re.compile(r"(?:ஓப்பன்|ஓபன்|லான்ச்|திற|மூடு)\s+", re.I),

    # Document creation / Office tools / Files / Downloads / Conversions
    re.compile(r"\b(create|make|generate|build|write|download|convert|save|export)\s+(a\s+)?(excel|marks sheet|marksheet|spreadsheet|word|docx|doc|document|powerpoint|ppt|presentation|pdf|report|folder|directory|text file|note|notes|file|csv|image|installer|package)\b", re.I),
    re.compile(r"\b(excel|word|pdf|ppt|powerpoint|folder|file|csv|image)\b.*?\b(create|make|generate|delete|remove|copy|move|rename|download|convert|save|export)\b", re.I),
    re.compile(r"\b(download|convert\s+(?:.*?\s+)?to\s+pdf|docx_to_pdf|word_to_pdf|save\s+image)\b", re.I),
    re.compile(r"\b(delete|remove|copy|move|rename|read|edit|search)\s+(file|folder|document|directory|code)\b", re.I),

    # WhatsApp messaging & Calls
    re.compile(r"\b(whatsapp|message|send\s+message|text|send\s+whatsapp|call\s+on\s+whatsapp)\b", re.I),

    # Audio & System volume & Brightness
    re.compile(r"\b(volume|sound|mute|unmute|louder|quieter|brightness|screenshot|take\s+screenshot)\b", re.I),

    # System Info & Time
    re.compile(r"\b(what\s+time|what\s+date|current\s+time|today['\s]*s\s+date|system\s+info)\b", re.I),

    # Browser scrolling, clicking, typing & explicit search actions
    re.compile(r"\b(scroll|click|type|press\s+key|go\s+back|go\s+forward|refresh\s+page|search\s+youtube|search\s+google|search\s+web|search\s+flipkart|play\s+youtube|play\s+first\s+video)\b", re.I),
    re.compile(r"\b(google-la|youtube-la|browser-la)\s+(.*?)\s+(search|play|open)\b", re.I),

    # Tanglish action verbs (open pannu, create pannu, search pannu, etc.)
    re.compile(r"\b(open|search|play|create|delete|close|type|click|send|scroll)\s+pann[ui](?:nga)?\b", re.I),

    # Memory persistence commands
    re.compile(r"^(remember|forget|show\s+memory|saved\s+preferences)\b", re.I),
]



class IntentRouter:
    """
    Classifies normalized text input into ACTION_MODE or CONVERSATION_MODE.
    """

    def route(self, normalized: NormalizedCommand | str) -> IntentRoutingResult:
        """
        Evaluate normalized command and determine routing mode.
        """
        if isinstance(normalized, str):
            cmd_text = normalized.strip()
        else:
            cmd_text = normalized.get("normalized_text", "").strip()

        if not cmd_text:
            return {
                "mode": IntentMode.CONVERSATION,
                "command": "",
                "direct_plan": None,
                "reason": "Empty input default to conversation",
            }

        log.debug("IntentRouter evaluating text: %r", cmd_text)

        # 1. Check local 0ms deterministic router first
        direct_plan = route_command(cmd_text)
        if direct_plan:
            log.info("IntentRouter: Direct deterministic action plan matched for %r", cmd_text)
            return {
                "mode": IntentMode.ACTION,
                "command": cmd_text,
                "direct_plan": direct_plan,
                "reason": "Matched 0ms deterministic action rule",
            }

        # 2. Check Action intent patterns (system actions, app creation, whatsapp, etc.)
        for pattern in _ACTION_PATTERNS:
            if pattern.search(cmd_text):
                log.info("IntentRouter: Action pattern matched for %r", cmd_text)
                return {
                    "mode": IntentMode.ACTION,
                    "command": cmd_text,
                    "direct_plan": None,
                    "reason": f"Matched action pattern '{pattern.pattern[:40]}'",
                }

        # 3. Default to Conversation Mode (AI Reasoning / QA / Gemini)
        log.info("IntentRouter: Routed %r to CONVERSATION MODE", cmd_text)
        return {
            "mode": IntentMode.CONVERSATION,
            "command": cmd_text,
            "direct_plan": None,
            "reason": "Default conversational query",
        }
