"""
CHAMP Phase 2 (Multi-Step Planner) — agent/orchestrator.py

Central Agent Orchestrator.
Phase 2: Multi-step voice commands are decomposed into TaskQueues and executed
with dependency-aware ordering, retry, and honest partial-success reporting.
"""

from __future__ import annotations
import uuid
import re
from typing import Any, TYPE_CHECKING

from agent.task import TaskPlan, TaskStep, TaskState
from agent.state import SessionState
from agent.executor import TaskExecutor
from agent.recovery import RecoveryEngine
from safety.policy import PolicyEngine
from safety.confirmation import ConfirmationHandler
from monitoring.health import HealthChecker
from monitoring.metrics import MetricsCollector
from rag.retrieval.retriever import RAGRetriever
from memory.personal_memory import PersonalMemoryStore
from retrieval.web_search import WebSearcher, is_freshness_query
from retrieval.source_processor import SourceProcessor
from agent.command_normalizer import CommandNormalizer
from agent.intent_router import IntentRouter, IntentMode
from agent.command_router import route_command
# Phase 2: Multi-Step Planner imports
from planner.voice_planner import VoiceAgentPlanner
from executor.dependency_executor import DependencyAwareExecutor
from utils.logger import get_logger

if TYPE_CHECKING:
    from ai.gemini_client import GeminiClient
    from ai.conversation import ConversationManager
    from ai.planner import AgentPlanner
    from tools.registry import ToolRegistry
    from speech import tts

log = get_logger("muthuai.agent.orchestrator")

_RAG_KEYWORDS = re.compile(
    r"\b(my notes|from my notes|in my notes|enoda notes|enoda pdf|enoda doc|enoda study material|from my document|in my document|my document|my documents|my file|my files|study material|according to my notes|search notes|search document|search study material|கோப்பில் உள்ள|குறிப்புகளில் உள்ள|நோட்ஸில்)\b",
    re.IGNORECASE
)


_CANCELLATION_KEYWORDS = ("stop", "cancel", "நிறுத்து", "cancel pannidu", "விடு", "quit")


class AgentOrchestrator:
    """
    Central Agent Orchestrator for MuthuAI v1.0.
    """

    def __init__(
        self,
        gemini_client: "GeminiClient",
        conversation: "ConversationManager",
        planner: "AgentPlanner",
        registry: "ToolRegistry",
        validator: Any = None,
        confirmation: ConfirmationHandler | None = None,
        tts_module: Any = None,
        hud_bridge: Any = None,
    ) -> None:
        self.gemini = gemini_client
        self.conversation = conversation
        self.planner = planner
        self.registry = registry
        self.validator = validator
        self.confirmation: ConfirmationHandler = confirmation if confirmation is not None else ConfirmationHandler()
        self.tts = tts_module
        self.hud_bridge = hud_bridge

        self.normalizer = CommandNormalizer()
        self.intent_router = IntentRouter()
        self.policy = PolicyEngine()
        self.session_state = SessionState()
        self.executor = TaskExecutor(
            registry=self.registry,
            policy=self.policy,
            confirmation=self.confirmation,
            state=self.session_state,
            tts_speak=lambda q: self.tts.speak(q) if self.tts else None
        )
        self.rag_retriever = RAGRetriever()
        self.web_searcher = WebSearcher()
        self.source_processor = SourceProcessor()
        self.personal_memory = PersonalMemoryStore()
        from memory.task_memory import TaskMemoryManager
        from memory.desktop_context import DesktopContextManager
        from memory.long_term_memory import LongTermMemory
        from memory.context_resolver import ContextResolver

        self.task_mem = TaskMemoryManager()
        self.desktop_ctx = DesktopContextManager()
        self.long_term_mem = LongTermMemory()
        self.context_resolver = ContextResolver(desktop_ctx=self.desktop_ctx, task_mem=self.task_mem)

        # Phase 2: Multi-step planner and dependency-aware executor
        self.voice_planner = VoiceAgentPlanner(
            gemini_client=gemini_client,
            registry=registry,
        )
        self.dep_executor = DependencyAwareExecutor(
            registry=self.registry,
            tts_speak=lambda q: self.tts.speak(q) if self.tts else None,
        )

    def process_turn(self, user_text: str, wake_authenticated: bool | None = None) -> str:
        """
        Process single user turn through Command Normalizer -> Intent Router -> Action/Conversation Mode.
        """
        # Auto-detect wake word if not explicitly passed from upstream voice pipeline
        if wake_authenticated is None:
            wake_authenticated = self.normalizer.wake_detector.is_activated(user_text)

        # 1. Command Normalization
        norm = self.normalizer.normalize(user_text, wake_authenticated=wake_authenticated)
        cmd_text = norm["normalized_text"] or norm["cleaned_command"] or user_text.strip()
        log.info("AgentOrchestrator processing turn (raw=%r, norm=%r, lang=%s, wake=%s)", user_text, cmd_text, norm["language"], norm["has_wake_word"])

        # Check Cancellation request
        if any(cw in user_text.lower() for cw in _CANCELLATION_KEYWORDS):
            log.info("Cancellation command received.")
            self.session_state.context_memory["cancel_scroll"] = True
            self.task_mem.cancel_task()
            return "Task cancelled. Standing by for your next command."

        # Rule 16: NO BRO = NO ACTION (Strict Wake Word Requirement)
        if not norm.get("has_wake_word", False):
            log.info("Input %r missing wake word 'Bro'. Ignored (NO BRO = NO ACTION).", user_text)
            return "No action taken — please include the wake word 'Bro' (e.g., 'Bro, open YouTube')."

        # ── PHASE 10: MEMORY DEBUG & RESET COMMANDS ─────────────────────────
        cmd_clean = cmd_text.lower().strip()
        if "what do you remember" in cmd_clean or "remember summary" in cmd_clean or "memory summary" in cmd_clean:
            return self.desktop_ctx.get_context_summary()
        elif "forget this task" in cmd_clean:
            self.task_mem.clear_task()
            return "Cleared active task context."
        elif "clear conversation" in cmd_clean:
            self.conversation.clear()
            return "Cleared conversation history."
        elif "reset memory" in cmd_clean:
            self.task_mem.clear_task()
            self.desktop_ctx.reset()
            self.long_term_mem.clear()
            return "Reset all persistent agent memory."

        # ── PHASE 10: CONTEXT RESOLUTION ─────────────────────────────────────
        resolved = self.context_resolver.resolve_reference(cmd_text)
        if resolved.get("target_app"):
            self.desktop_ctx.set_active_app(resolved["target_app"])

        # 2. Intent Routing
        route_res = self.intent_router.route(norm)
        log.info("IntentRouter decision: mode=%s, reason=%s", route_res["mode"], route_res["reason"])

        # ── ACTION MODE ─────────────────────────────────────────
        if route_res["mode"] == IntentMode.ACTION:

            direct_plan = route_res["direct_plan"]
            if direct_plan:
                log.info("[ROUTER] Executing deterministic plan (0 Gemini Calls): %s", direct_plan)
                if isinstance(direct_plan, list):
                    tool_plans = direct_plan
                else:
                    tool_plans = [direct_plan]
            else:
                tool_plans = self.planner.plan(cmd_text)

            if tool_plans:
                # ── Visual UI: Transition to COMPACT for task execution ────────
                if self.hud_bridge:
                    try:
                        from visual_ui.config import VISUAL_TASK_COMPACT
                        from visual_ui.hud_state import HUDState as _HS
                        if VISUAL_TASK_COMPACT:
                            self.hud_bridge.request_compact()
                        self.hud_bridge.post_event(_HS.EXECUTING, text=f"Planning: {cmd_text[:35]}")
                    except Exception:
                        pass

                # Phase 2: Check if this is a multi-step command for the new planner
                is_multi = (
                    self.voice_planner.is_multi_step(cmd_text)
                    or len(tool_plans) >= 2
                )

                task_succeeded = True

                if is_multi or len(tool_plans) >= 2:
                    # Route through Phase 2 VoiceAgentPlanner + DependencyAwareExecutor
                    log.info(
                        "[PHASE2] Multi-step command detected (%d steps). Routing through VoiceAgentPlanner.",
                        len(tool_plans)
                    )

                    # Build TaskQueue from Gemini-extracted steps
                    from task_queue.task_model import Task, TaskStatus
                    from task_queue.task_queue import TaskQueue

                    queue = TaskQueue()
                    prev_id: str | None = None
                    for idx, item in enumerate(tool_plans, start=1):
                        task_id = f"task_{idx:03d}"
                        from planner.voice_planner import _describe
                        task = Task(
                            id=task_id,
                            action=item["tool"],
                            parameters=item.get("arguments", {}),
                            dependencies=[prev_id] if prev_id else [],
                            description=_describe(item["tool"], item.get("arguments", {})),
                        )
                        queue.add(task)
                        prev_id = task_id

                    # Inject HUD bridge into dep_executor for per-step updates
                    self.dep_executor._hud_bridge = self.hud_bridge
                    total_steps = len(queue)

                    if self.tts:
                        self.tts.speak(f"Starting a {total_steps}-step task now.")

                    self.dep_executor.execute(queue)
                    response_text = queue.summary()

                    # Check if any tasks failed
                    from task_queue.task_model import TaskStatus
                    all_tasks = list(queue._tasks.values()) if hasattr(queue, '_tasks') else []
                    task_succeeded = all(
                        t.status == TaskStatus.SUCCESS
                        for t in all_tasks
                    ) if all_tasks else True

                else:
                    # Single-step: use existing executor (fast path)
                    steps = []
                    for idx, item in enumerate(tool_plans, 1):
                        steps.append(TaskStep(
                            step_id=idx,
                            tool_name=item["tool"],
                            arguments=item.get("arguments", {}),
                            description=f"Execute {item['tool']}"
                        ))

                    task_plan = TaskPlan(
                        task_id=f"task_{uuid.uuid4().hex[:6]}",
                        user_request=user_text,
                        steps=steps
                    )

                    # If confirmation needed, go fullscreen first
                    if self.hud_bridge:
                        try:
                            from visual_ui.config import VISUAL_CONFIRMATION_FULLSCREEN
                            from visual_ui.hud_state import HUDState as _HS
                            from safety.policy import PolicyEngine
                            _pol = PolicyEngine()
                            _needs_confirm = any(
                                self.confirmation.requires_confirmation(
                                    _pol.evaluate_permission(s.tool_name, s.arguments)
                                )
                                for s in steps
                            )
                            if _needs_confirm and VISUAL_CONFIRMATION_FULLSCREEN:
                                self.hud_bridge.request_fullscreen()
                                self.hud_bridge.post_event(_HS.CONFIRMATION, text="Awaiting confirmation...")
                        except Exception:
                            pass

                    # Post per-step EXECUTING + VERIFYING events
                    if self.hud_bridge:
                        try:
                            from visual_ui.hud_state import HUDState as _HS
                            step_desc = steps[0].description if steps else cmd_text[:35]
                            self.hud_bridge.post_event(_HS.EXECUTING, text=step_desc[:40])
                        except Exception:
                            pass

                    executed_steps = self.executor.execute_plan(task_plan)

                    # Post VERIFYING state
                    if self.hud_bridge:
                        try:
                            from visual_ui.hud_state import HUDState as _HS
                            self.hud_bridge.post_event(_HS.VERIFYING, text="Verifying result...")
                        except Exception:
                            pass

                    response_text = self._build_task_response(executed_steps)
                    from agent.task import TaskState
                    task_succeeded = all(s.state == TaskState.SUCCESS for s in executed_steps)

                # ── Visual UI: Return to FULLSCREEN upon task completion ───────
                if self.hud_bridge:
                    try:
                        from visual_ui.config import VISUAL_RETURN_FULLSCREEN_AFTER_TASK
                        from visual_ui.hud_state import HUDState as _HS
                        if task_succeeded:
                            self.hud_bridge.post_event(_HS.SUCCESS, text="Task Complete", auto_return=True)
                        else:
                            self.hud_bridge.post_event(_HS.ERROR, text="Task Failed", auto_return=True)
                        if VISUAL_RETURN_FULLSCREEN_AFTER_TASK:
                            self.hud_bridge.request_fullscreen()
                    except Exception:
                        pass

                self.conversation.add_user_turn(user_text)
                self.conversation.add_assistant_turn(response_text)
                return response_text

        # ── CONVERSATION MODE (Always FULLSCREEN) ────────────────
        if self.hud_bridge:
            try:
                from visual_ui.hud_state import HUDState
                self.hud_bridge.request_fullscreen()
                self.hud_bridge.post_event(HUDState.PROCESSING, text="Thinking...")
            except Exception:
                pass

        from voice.language_detector import detect_language, get_language_prompt_instruction
        last_lang = self.session_state.context_memory.get("last_language")
        detected_lang = detect_language(user_text, context_lang=last_lang)
        self.session_state.context_memory["last_language"] = detected_lang
        lang_instruction = get_language_prompt_instruction(detected_lang)

        context_blocks = []

        # A. Personal Memory Context
        memory_ctx = self.personal_memory.format_memory_context()
        if memory_ctx:
            context_blocks.append(memory_ctx)

        # B. RAG Document Retrieval
        is_rag_query = bool(_RAG_KEYWORDS.search(cmd_text))
        if is_rag_query:
            log.info("RAG query detected: %r", cmd_text)
            chunks = self.rag_retriever.retrieve(cmd_text, top_k=4)
            if chunks:
                rag_ctx = self.rag_retriever.format_context(chunks)
                context_blocks.append(rag_ctx)
            else:
                log.info("RAG query yielded no relevant chunks for %r", cmd_text)
                if detected_lang == "ta":
                    no_chunks_msg = f"உங்கள் கோப்புகளில் '{user_text}' பற்றிய விவரங்கள் எதுவும் கிடைக்கவில்லை."
                elif detected_lang == "tanglish":
                    no_chunks_msg = f"Unga indexed documents-la '{user_text}' pathi relevant notes edhuvum kedaikala bro."
                else:
                    no_chunks_msg = f"I searched your indexed documents for '{user_text}', but could not find relevant information in your notes."
                self.conversation.add_user_turn(user_text)
                self.conversation.add_assistant_turn(no_chunks_msg)
                return no_chunks_msg

        # C. Live Web Retrieval / Current Information
        if is_freshness_query(cmd_text):
            log.info("Current Information / Freshness query detected: %r", cmd_text)
            from retrieval.web_search import check_internet_connectivity
            conn_status = check_internet_connectivity()
            if not conn_status["internet_available"]:
                log.warning("Internet offline during current information query: %s", conn_status["status_code"])
                if detected_lang == "ta":
                    offline_msg = "இணைய இணைப்பு இல்லாததால் இப்போதைய தகவல்களைப் பெற முடியவில்லை."
                elif detected_lang == "tanglish":
                    offline_msg = "Internet connection illatha nala ippo current updates edukka mudiyala bro."
                else:
                    offline_msg = "I am unable to retrieve current information because there is no internet connection right now."
                self.conversation.add_user_turn(user_text)
                self.conversation.add_assistant_turn(offline_msg)
                return offline_msg

            search_results = self.web_searcher.search(cmd_text, max_results=4)
            if search_results:
                import datetime
                from ai.prompt_manager import web_search_response_prompt
                web_ctx = self.source_processor.format_sources(search_results)
                today_str = datetime.date.today().strftime("%A, %B %d, %Y")
                prompt = web_search_response_prompt(
                    user_text=user_text,
                    search_results=web_ctx,
                    lang=detected_lang,
                    current_date=today_str,
                )
                response_text = self.gemini.generate_response(prompt, conversation_history=self.conversation.get_history())
                self.conversation.add_user_turn(user_text)
                self.conversation.add_assistant_turn(response_text)
                return response_text
            else:
                log.info("Web search yielded 0 results for query: %r", cmd_text)
                if detected_lang == "ta":
                    no_results_msg = f"'{user_text}' பற்றிய சமீபத்திய தகவல்கள் எதுவும் இணையத்தில் கிடைக்கவில்லை."
                elif detected_lang == "tanglish":
                    no_results_msg = f"'{user_text}' pathi latest web updates edhuvum kedaikala bro."
                else:
                    no_results_msg = f"I searched the web for current updates on '{user_text}', but could not find recent reports."
                self.conversation.add_user_turn(user_text)
                self.conversation.add_assistant_turn(no_results_msg)
                return no_results_msg

        # Gemini Reasoning for Standard Conversation
        if context_blocks:
            full_context = "\n\n".join(context_blocks)
            prompt = (
                f"User Request: \"{user_text}\"\n\n"
                f"{full_context}\n\n"
                f"LANGUAGE & STYLE INSTRUCTION: {lang_instruction}\n"
                "INSTRUCTIONS:\n"
                "- Answer the user accurately using the retrieved context.\n"
                "- Cite document names/pages clearly.\n"
                "- Keep spoken response concise, natural, and friendly (1-3 sentences).\n"
            )
            response_text = self.gemini.generate_response(prompt, conversation_history=self.conversation.get_history())
        else:
            history = self.conversation.get_history()
            prompt = (
                f"User Message: \"{cmd_text}\"\n\n"
                f"LANGUAGE & STYLE INSTRUCTION: {lang_instruction}\n"
                "INSTRUCTIONS:\n"
                "- Respond naturally and helpfully to the user.\n"
                "- Keep it concise (1-3 sentences) and conversational for voice TTS.\n"
                "- Do NOT use markdown bullet points, code blocks, or raw URLs in spoken turns.\n"
            )
            response_text = self.gemini.generate_response(prompt, history)

        self.conversation.add_user_turn(user_text)
        self.conversation.add_assistant_turn(response_text)
        return response_text

    def _build_task_response(self, steps: list[TaskStep]) -> str:
        succ_messages = [s.result_message for s in steps if s.state == TaskState.SUCCESS]
        fail_messages = [s.result_message for s in steps if s.state == TaskState.FAILED]

        parts = []
        if succ_messages:
            parts.append(" ".join(succ_messages))
        if fail_messages:
            parts.append(f"Task incomplete: {' '.join(fail_messages)}")

        return " ".join(parts) if parts else "Task completed."
