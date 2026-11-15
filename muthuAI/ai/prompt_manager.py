"""
MuthuAI — ai/prompt_manager.py
All system prompts and prompt templates in one place.
NO prompts should be hard-coded in other modules.
"""

from __future__ import annotations
import datetime
from typing import Any

from config.environment import AGENT_NAME
from voice.language_detector import get_language_prompt_instruction


# ── System Prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are {AGENT_NAME}, a highly capable personal AI assistant running on a Windows computer.
You assist the user with voice-controlled interactions in English, Tamil, or conversational Tanglish (Tamil+English code-mixed spoken style).

CORE RULES:
1. LANGUAGE & STYLE:
   - If the user explicitly asks for a language (e.g., 'in English', 'தமிழ்ல சொல்லு', 'Tanglish-la'), ALWAYS obey that instruction.
   - If user speaks English -> respond in natural, clear English.
   - If user speaks Tamil -> respond in natural modern Tamil.
   - If user speaks Tanglish (e.g. 'machine learning-na enna bro?') -> respond in natural, conversational Tanglish. Do NOT translate into awkward formal Tamil. Preserve common technical English words.
2. You have access to a set of TOOLS that let you control the user's computer. Use them whenever needed.
3. For CURRENT information (today's news, prices, weather, live data), always use the web_search tool — never guess.
4. For LOCAL KNOWLEDGE from the user's documents, use the search_documents tool.
5. For CONVERSATIONAL questions, answer directly without tools.
6. Be concise and natural (1-3 sentences). Speak like a helpful personal assistant, not a textbook.
7. NEVER perform destructive or sensitive actions without the user's explicit confirmation.
8. If a tool fails, acknowledge it honestly and suggest alternatives.

IMPORTANT:
- Keep responses spoken-friendly — they will be read aloud via TTS.
- Avoid markdown bullet points, code blocks, or raw URLs in spoken conversational turns.
"""


# ── Tool Planning Prompt ──────────────────────────────────────
def tool_planning_prompt(
    user_text: str,
    context: str = "",
    available_tools: str = "",
) -> str:
    """Generate the structured planning prompt for tool selection and task decomposition."""
    return f"""Based on the user's request, decide which tool(s) to use.

CONVERSATION CONTEXT:
{context}

AVAILABLE TOOLS:
{available_tools}

USER REQUEST: "{user_text}"

Respond ONLY with a JSON array of tool calls in this exact format:
[
  {{"tool": "tool_name", "params": {{"key": "value"}}}},
  ...
]

If no tool is needed (pure conversation), respond with: []
Do NOT add any explanation outside the JSON.
"""


# ── RAG Response Prompt ───────────────────────────────────────
def rag_response_prompt(
    user_text: str,
    retrieved_chunks: str,
    lang: str = "en",
) -> str:
    """Generate the prompt to answer questions grounded in retrieved document chunks."""
    lang_instruction = get_language_prompt_instruction(lang)
    return f"""The user asked: "{user_text}"

The following information was retrieved from their documents:
---
{retrieved_chunks}
---

Using ONLY the above retrieved information, answer the user's question clearly and helpfully.
{lang_instruction}
If the retrieved information does not contain enough to answer, say so honestly.
"""


# ── Web Search Response Prompt ────────────────────────────────
def web_search_response_prompt(
    user_text: str,
    search_results: str,
    lang: str = "en",
    current_date: str = "",
) -> str:
    """Generate the prompt to answer questions grounded in real-time web search results."""
    if not current_date:
        current_date = datetime.date.today().strftime("%A, %B %d, %Y")

    lang_instruction = get_language_prompt_instruction(lang)
    return f"""The user asked: "{user_text}"

TODAY'S DATE: {current_date}

THE FOLLOWING REAL-TIME CURRENT WEB INFORMATION WAS RETRIEVED FROM SEARCH:
---
{search_results}
---

CRITICAL INSTRUCTIONS:
1. Ground your response STRICTLY in the above retrieved web search information.
2. Under NO circumstances say "I don't have internet access" or "I cannot access real-time data" because live web information has already been retrieved and supplied above.
3. {lang_instruction}
4. Summarize the key facts clearly and mention the reporting source (e.g. "According to reports by The Hindu / NDTV / Dinamani...").
5. Keep the spoken response natural, conversational, and concise (1-3 sentences) for voice delivery.
6. Do NOT include raw URLs, markdown headers, or bullet points in the spoken text.
"""


# ── Final Response Prompt ─────────────────────────────────────
def final_response_prompt(
    user_text: str,
    tool_results: str,
    context: str = "",
    lang: str = "en",
) -> str:
    """Generate the prompt to summarize tool execution results into a natural spoken turn."""
    lang_instruction = get_language_prompt_instruction(lang)
    return f"""The user said: "{user_text}"

Tool execution results:
{tool_results}

Conversation context:
{context}

Generate a natural, concise spoken response for the user.
{lang_instruction}
Keep it under 3 sentences. Be warm and helpful.
"""


# ── Conversational Prompt ─────────────────────────────────────
def conversational_prompt(
    user_text: str,
    context: str = "",
    lang: str = "en",
) -> str:
    """Generate the prompt for direct conversation turns."""
    lang_instruction = get_language_prompt_instruction(lang)
    return f"""Conversation history:
{context}

User: {user_text}

{lang_instruction}
Respond naturally and helpfully. Keep it concise (1-3 sentences).
"""


# ── Dangerous Action Confirmation Prompt ─────────────────────
def confirmation_prompt(
    action: str,
    params: dict[str, Any] | None = None,
    lang: str = "en",
) -> str:
    """Generate a confirmation prompt before executing high-risk or destructive actions."""
    if lang == "ta":
        lang_instruction = "Ask in natural modern Tamil (தமிழ்)."
    elif lang == "tanglish":
        lang_instruction = "Ask in friendly conversational Tanglish (Tamil+English)."
    else:
        lang_instruction = "Ask in clear, friendly English."

    params_str = f" with parameters {params}" if params else ""
    return (
        f"The user wants to perform a potentially dangerous action: {action}{params_str}. "
        f"Generate a clear, friendly confirmation question asking if they are sure. {lang_instruction}"
    )
