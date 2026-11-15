# CHAMP — Complete File Inventory & Architecture Scan

**Project**: CHAMP AI Personal Assistant (Windows Real Computer-Use Voice Agent)  
**Total Files Scanned**: 120+ source and configuration files  
**Python Runtime**: Python 3.10+ on Windows 11 (x64)  
**Date**: September 3, 2026  

---

## 1. Top-Level Entry Points & Scripts

### `app/main.py`
- **Path**: `d:/juniors/muthuAI/app/main.py`
- **Purpose**: Main production application entry point and real-time voice assistant loop.
- **Used By**: `launcher.py`, `run_champ.bat`, user CLI.
- **Dependencies**: `voice.voice_pipeline`, `agent.orchestrator`, `ai.gemini_client`, `tools.setup_default_registry`.
- **Current Status**: **VERIFIED / OPERATIONAL**.
- **Problems**: None. Handles graceful shutdown on SIGINT/Ctrl+C.
- **Connections**: Glues audio input $\to$ STT $\to$ Language Detection $\to$ Orchestrator $\to$ TTS $\to$ Audio Output.

### `launcher.py`
- **Path**: `d:/juniors/muthuAI/launcher.py`
- **Purpose**: System bootstrap script that checks environment, runs diagnostics, and launches `app/main.py`.
- **Used By**: `run_champ.bat`.
- **Dependencies**: `diagnostics.py`, `app.main`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `diagnostics.py`
- **Path**: `d:/juniors/muthuAI/diagnostics.py`
- **Purpose**: System health check verifying Python version, `.env` file, Gemini API key, microphone, internet connectivity, and dependencies.
- **Used By**: `launcher.py`, standalone diagnostics check.
- **Dependencies**: `urllib`, `os`, `sys`, `socket`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

---

## 2. Voice & Speech Pipeline

### `voice/voice_pipeline.py`
- **Path**: `d:/juniors/muthuAI/voice/voice_pipeline.py`
- **Purpose**: Real-time voice pipeline coordinator managing continuous listening, VAD, STT, wake word detection, and audio playback.
- **Used By**: `app/main.py`.
- **Dependencies**: `voice.audio_input`, `voice.stt`, `voice.tts`, `voice.wake_word`, `voice.language_detector`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `voice/audio_input.py`
- **Path**: `d:/juniors/muthuAI/voice/audio_input.py`
- **Purpose**: Microphone capture and voice activity detection using PyAudio and WebRTC VAD.
- **Used By**: `voice/voice_pipeline.py`.
- **Dependencies**: `pyaudio`, `webrtcvad`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `voice/stt.py`
- **Path**: `d:/juniors/muthuAI/voice/stt.py`
- **Purpose**: Speech-to-text recognition using Google Speech Recognition API with automatic language fallback.
- **Used By**: `voice/voice_pipeline.py`.
- **Dependencies**: `speech_recognition`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `voice/tts.py`
- **Path**: `d:/juniors/muthuAI/voice/tts.py`
- **Purpose**: High-quality multilingual Text-to-Speech synthesis via Microsoft Edge TTS (`ta-IN-ValluvarNeural` for Tamil, `en-IN-PrabhatNeural` for English/Tanglish) with pygame mixer playback.
- **Used By**: `voice/voice_pipeline.py`, `agent/orchestrator.py`.
- **Dependencies**: `edge_tts`, `pygame`.
- **Current Status**: **VERIFIED / OPERATIONAL**. Supports barge-in interruption.

### `voice/wake_word.py`
- **Path**: `d:/juniors/muthuAI/voice/wake_word.py`
- **Purpose**: Fast regex-based wake word detection for `"Bro"`, `"Hey Bro"`, `"Hi Bro"`, and Tamil Unicode `"ப்ரோ"`.
- **Used By**: `voice/voice_pipeline.py`, `agent/orchestrator.py`.
- **Dependencies**: `re`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `voice/language_detector.py`
- **Path**: `d:/juniors/muthuAI/voice/language_detector.py`
- **Purpose**: 4-Tier language detector classifying text into English (`en`), Tamil (`ta`), and Tanglish (`tanglish`).
- **Used By**: `voice/voice_pipeline.py`, `agent/orchestrator.py`, `ai/prompt_manager.py`.
- **Dependencies**: `re`, `unicodedata`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

---

## 3. AI & Reasoning Layer

### `ai/gemini_client.py`
- **Path**: `d:/juniors/muthuAI/ai/gemini_client.py`
- **Purpose**: Google GenAI SDK integration (`google-genai` package) with automatic backoff retry on 503/429 errors.
- **Used By**: `agent/orchestrator.py`, `ai/planner.py`, `tools/office_tools.py`.
- **Dependencies**: `google-genai`, `dotenv`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `ai/conversation.py`
- **Path**: `d:/juniors/muthuAI/ai/conversation.py`
- **Purpose**: Multi-turn conversation history manager with sliding context window and role attribution.
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: standard Python types.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `ai/prompt_manager.py`
- **Path**: `d:/juniors/muthuAI/ai/prompt_manager.py`
- **Purpose**: System prompt templates for conversation, task planning, web search response grounding, and document explanation.
- **Used By**: `agent/orchestrator.py`, `ai/planner.py`, `retrieval/web_search.py`.
- **Dependencies**: `datetime`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `ai/planner.py`
- **Path**: `d:/juniors/muthuAI/ai/planner.py`
- **Purpose**: Gemini-driven tool call generator for converting natural language queries into executable tool action plans.
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: `ai.gemini_client`, `tools.registry`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

---

## 4. Agent, Orchestration & Planning Layer

### `agent/orchestrator.py`
- **Path**: `d:/juniors/muthuAI/agent/orchestrator.py`
- **Purpose**: Master turn controller: parses wake words, resolves context, classifies Mode A (Conversation) vs Mode B (Action), invokes web search/RAG, and directs execution.
- **Used By**: `app/main.py`, test suite.
- **Dependencies**: `agent.command_router`, `agent.intent_router`, `retrieval.web_search`, `executor.dependency_executor`, `rag.pipeline`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `agent/command_router.py`
- **Path**: `d:/juniors/muthuAI/agent/command_router.py`
- **Purpose**: 0ms deterministic regex router bypassing LLM for common application, office, browser, and system commands.
- **Used By**: `agent/orchestrator.py`, `agent/intent_router.py`.
- **Dependencies**: `re`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `agent/intent_router.py`
- **Path**: `d:/juniors/muthuAI/agent/intent_router.py`
- **Purpose**: Classifies incoming query into `IntentMode.ACTION` or `IntentMode.CONVERSATION`.
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: `agent.command_router`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `planner/voice_planner.py`
- **Path**: `d:/juniors/muthuAI/planner/voice_planner.py`
- **Purpose**: Decomposes complex spoken commands into directed acyclic task graphs (`TaskQueue`) with dependency tracking.
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: `planner.task_model`, `task_queue.queue`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `executor/dependency_executor.py`
- **Path**: `d:/juniors/muthuAI/executor/dependency_executor.py`
- **Purpose**: Executes task graph sequentially, checking prerequisites, validating output, and blocking dependent tasks on failure.
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: `tools.registry`, `agent.validator`, `safety.policy`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

---

## 5. Tool Registry & Tool Modules

### `tools/__init__.py` & `tools/setup_registry.py`
- **Path**: `d:/juniors/muthuAI/tools/__init__.py`, `d:/juniors/muthuAI/tools/setup_registry.py`
- **Purpose**: Central tool registry registering 96 modular tools covering all system and application automation.
- **Used By**: `ai/planner.py`, `agent/orchestrator.py`, `executor/dependency_executor.py`.
- **Dependencies**: individual tool files in `tools/`.
- **Current Status**: **VERIFIED / OPERATIONAL (96 Tools Active)**.

### `tools/application_tools.py` & `tools/windows/application.py`
- **Path**: `d:/juniors/muthuAI/tools/application_tools.py`, `d:/juniors/muthuAI/tools/windows/application.py`
- **Purpose**: Windows application launcher resolving binaries via Windows Registry `App Paths`, Program Files, AppData, and Shell protocols.
- **Used By**: `open_application` tool.
- **Dependencies**: `winreg`, `subprocess`, `os`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `tools/browser_tools.py` & `browser/interaction.py`
- **Path**: `d:/juniors/muthuAI/tools/browser_tools.py`, `d:/juniors/muthuAI/browser/interaction.py`
- **Purpose**: Playwright-based browser controller for Google search, YouTube navigation, video playback, DOM reading, and clicking.
- **Used By**: `search_google`, `open_website`, `search_youtube`, `play_youtube`, `click`, `type_text`.
- **Dependencies**: `playwright.sync_api`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `tools/office_tools.py`
- **Path**: `d:/juniors/muthuAI/tools/office_tools.py`
- **Purpose**: Production Office document generation for Excel (`openpyxl`), Word (`python-docx`), PowerPoint (`python-pptx`), and PDF (`reportlab`).
- **Used By**: `create_excel`, `create_word`, `create_powerpoint`, `create_pdf`, `explain_and_create_pdf`.
- **Dependencies**: `openpyxl`, `docx`, `pptx`, `reportlab`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `tools/windows/system.py` & `tools/system_tools.py`
- **Path**: `d:/juniors/muthuAI/tools/windows/system.py`, `d:/juniors/muthuAI/tools/system_tools.py`
- **Purpose**: System volume, screenshot, media control, and hardware info using Windows API `keybd_event` virtual keys.
- **Used By**: `volume_up`, `volume_down`, `mute_volume`, `take_screenshot`.
- **Dependencies**: `ctypes`, `pywin32`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `tools/communication_tools.py` & `communication/whatsapp.py` & `communication/email.py`
- **Path**: `d:/juniors/muthuAI/tools/communication_tools.py`, `d:/juniors/muthuAI/communication/whatsapp.py`, `d:/juniors/muthuAI/communication/email.py`
- **Purpose**: WhatsApp Web / Protocol messaging and IMAP email inbox reading/categorization.
- **Used By**: `whatsapp_send_message`, `read_emails`, `check_important_emails`.
- **Dependencies**: `playwright`, `imaplib`, `email`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

---

## 6. Information Retrieval & Knowledge Systems

### `retrieval/web_search.py`
- **Path**: `d:/juniors/muthuAI/retrieval/web_search.py`
- **Purpose**: Multi-provider live web search engine (Google News RSS, DuckDuckGo, Headless Browser) with date-aware injection and DNS connectivity diagnostics.
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: `urllib`, `xml.etree.ElementTree`, `ddgs`, `requests`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `rag/pipeline.py` & `rag/retrieval/retriever.py`
- **Path**: `d:/juniors/muthuAI/rag/pipeline.py`, `d:/juniors/muthuAI/rag/retrieval/retriever.py`
- **Purpose**: Local document vector search engine using ChromaDB and `sentence-transformers/all-MiniLM-L6-v2`.
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: `chromadb`, `sentence_transformers`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

---

## 7. Memory & Context

### `memory/personal_memory.py`
- **Path**: `d:/juniors/muthuAI/memory/personal_memory.py`
- **Purpose**: Persistent JSON user profile, preferences, and facts store.
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: `json`, `pathlib`.
- **Current Status**: **VERIFIED / OPERATIONAL**.

### `memory/desktop_context.py` & `memory/context_resolver.py`
- **Path**: `d:/juniors/muthuAI/memory/desktop_context.py`, `d:/juniors/muthuAI/memory/context_resolver.py`
- **Purpose**: Tracks active application context and resolves anaphoric references (e.g. *"it"*, *"the file"*, *"this video"*).
- **Used By**: `agent/orchestrator.py`.
- **Dependencies**: standard Python types.
- **Current Status**: **VERIFIED / OPERATIONAL**.

---

## 8. Safety, Security & Confirmation

### `safety/policy.py` & `safety/confirmation.py` & `safety/permissions.py`
- **Path**: `d:/juniors/muthuAI/safety/policy.py`, `d:/juniors/muthuAI/safety/confirmation.py`, `d:/juniors/muthuAI/safety/permissions.py`
- **Purpose**: Enforces permission levels (`SAFE`, `MODERATE`, `DANGEROUS`) and interactive confirmation prompts before executing high-impact actions (WhatsApp messaging, file deletion).
- **Used By**: `executor/dependency_executor.py`, `agent/orchestrator.py`.
- **Dependencies**: standard Python types.
- **Current Status**: **VERIFIED / OPERATIONAL**.
