# CHAMP — Architecture & Subsystem Audit Report

**Date**: September 3, 2026  
**Project**: CHAMP (MuthuAI) Windows AI Personal Computer Agent  
**Auditor**: Senior Python AI-Agent Engineer  

---

## 1. System Entry Point
- **Location**: [`app/main.py`](file:///d:/juniors/muthuAI/app/main.py), [`launcher.py`](file:///d:/juniors/muthuAI/launcher.py), [`run_champ.bat`](file:///d:/juniors/muthuAI/run_champ.bat)
- **Role**: Initializes all production subsystems (Gemini, Memory, RAG, Web, Browser, Office, Tools, Safety, Agent Orchestrator), runs health checks, calibrates microphone, and manages the continuous voice interaction loop (Standby vs Active mode with barge-in support).

---

## 2. Voice Pipeline & Audio Capture
- **Location**: [`voice/voice_pipeline.py`](file:///d:/juniors/muthuAI/voice/voice_pipeline.py), [`voice/audio_input.py`](file:///d:/juniors/muthuAI/voice/audio_input.py), [`voice/vad.py`](file:///d:/juniors/muthuAI/voice/vad.py)
- **Role**: Real-time microphone capture at 16kHz mono, energy-based voice activity detection (VAD), dynamic calibration, and silence thresholding for low latency turn-taking.

---

## 3. Speech-to-Text (STT) Layer
- **Location**: [`voice/stt.py`](file:///d:/juniors/muthuAI/voice/stt.py), [`voice/recognizer.py`](file:///d:/juniors/muthuAI/voice/recognizer.py)
- **Role**: Abstract `STTProvider` interface implemented by `GoogleSpeechSTTProvider` with multilingual recognition support for English (`en-IN`, `en-US`), Tamil (`ta-IN`), and mixed Tanglish speech.

---

## 4. Wake Word Engine
- **Location**: [`voice/wake_word.py`](file:///d:/juniors/muthuAI/voice/wake_word.py)
- **Role**: Detects wake word `"Bro"` / `"ப்ரோ"` at the start of utterances. Enforces strict rule: No Bro = Standby (no accidental triggers). Extracts inline command payloads.

---

## 5. Multilingual Language Detection
- **Location**: [`voice/language_detector.py`](file:///d:/juniors/muthuAI/voice/language_detector.py)
- **Role**: 4-tier language classification (Explicit Override -> Tamil Unicode script -> Tanglish vocabulary -> English). Manages context inheritance across follow-up turns.

---

## 6. Gemini LLM Integration
- **Location**: [`ai/gemini_client.py`](file:///d:/juniors/muthuAI/ai/gemini_client.py), [`ai/response_generator.py`](file:///d:/juniors/muthuAI/ai/response_generator.py), [`ai/prompt_manager.py`](file:///d:/juniors/muthuAI/ai/prompt_manager.py)
- **Role**: `google-genai` client integration (`gemini-2.0-flash` / `gemini-flash-lite-latest`), system prompt management, temperature control, function declarations, and grounded response synthesis.

---

## 7. Conversation Manager
- **Location**: [`ai/conversation.py`](file:///d:/juniors/muthuAI/ai/conversation.py)
- **Role**: In-memory multi-turn conversational history management with sliding-window truncation (max 10 turns) to prevent context blowup and preserve prompt speed.

---

## 8. Agent Orchestrator
- **Location**: [`agent/orchestrator.py`](file:///d:/juniors/muthuAI/agent/orchestrator.py)
- **Role**: Master coordinator. Passes raw text to Command Normalizer -> Intent Router -> Mode A (Conversation) or Mode B (Action). Dispatches multi-step tasks to `VoiceAgentPlanner` + `DependencyAwareExecutor` and single-step tasks to `TaskExecutor`.

---

## 9. Task Planner & Decomposer
- **Location**: [`ai/planner.py`](file:///d:/juniors/muthuAI/ai/planner.py), [`planner/voice_planner.py`](file:///d:/juniors/muthuAI/planner/voice_planner.py)
- **Role**: Decomposes natural language commands (English, Tamil, Tanglish) into structured `TaskQueue` graphs with explicit sequential dependencies, action names, and argument schemas.

---

## 10. Tool Registry
- **Location**: [`tools/registry.py`](file:///d:/juniors/muthuAI/tools/registry.py), [`tools/setup_registry.py`](file:///d:/juniors/muthuAI/tools/setup_registry.py), [`tools/__init__.py`](file:///d:/juniors/muthuAI/tools/__init__.py), [`tools/base.py`](file:///d:/juniors/muthuAI/tools/base.py)
- **Role**: Central catalogue supporting 79+ modular tools with `BaseTool` / `ToolDefinition`, parameter schemas, risk levels (`SAFE`, `MODERATE`, `DANGEROUS`, `BLOCKED`), and safe execution sandboxing.

---

## 11. Tool Executor & Dependency Engine
- **Location**: [`agent/executor.py`](file:///d:/juniors/muthuAI/agent/executor.py), [`executor/dependency_executor.py`](file:///d:/juniors/muthuAI/executor/dependency_executor.py)
- **Role**: Sequential and dependency-aware task graph execution. Halts downstream dependent tasks on failure, handles single retries, integrates policy confirmation, and collects telemetry metrics.

---

## 12. Browser Automation Layer
- **Location**: [`browser/manager.py`](file:///d:/juniors/muthuAI/browser/manager.py), [`browser/interaction.py`](file:///d:/juniors/muthuAI/browser/interaction.py), [`browser/discovery.py`](file:///d:/juniors/muthuAI/browser/discovery.py), [`tools/browser_tools.py`](file:///d:/juniors/muthuAI/tools/browser_tools.py)
- **Role**: Playwright-based browser lifecycle manager for Chrome and Edge. Supports URL navigation, DOM element clicking, typing, scrolling, Google search, YouTube search, and first-video playback.

---

## 13. Windows Automation Layer
- **Location**: [`desktop/desktop_controller.py`](file:///d:/juniors/muthuAI/desktop/desktop_controller.py), [`desktop/window_manager.py`](file:///d:/juniors/muthuAI/desktop/window_manager.py), [`automation/windows_controller.py`](file:///d:/juniors/muthuAI/automation/windows_controller.py)
- **Role**: Window management via `pywin32` and `pygetwindow`. Supports window activation, minimization, maximization, restoration, closing, and process tracking.

---

## 14. Keyboard Automation
- **Location**: [`desktop/keyboard_controller.py`](file:///d:/juniors/muthuAI/desktop/keyboard_controller.py), [`tools/windows/input.py`](file:///d:/juniors/muthuAI/tools/windows/input.py)
- **Role**: Virtual typing, hotkeys (`Ctrl+C`, `Ctrl+V`, `Alt+Tab`), and individual key presses (`Enter`, `Escape`, `Tab`) via `pyautogui` with safety margins.

---

## 15. Mouse Automation
- **Location**: [`desktop/mouse_controller.py`](file:///d:/juniors/muthuAI/desktop/mouse_controller.py), [`tools/windows/input.py`](file:///d:/juniors/muthuAI/tools/windows/input.py)
- **Role**: Cursor movement, left/right/double click, and mouse scroll operations via `pyautogui`.

---

## 16. Application Launcher
- **Location**: [`tools/application_tools.py`](file:///d:/juniors/muthuAI/tools/application_tools.py), [`tools/windows/application.py`](file:///d:/juniors/muthuAI/tools/windows/application.py)
- **Role**: Resolves Windows application paths through Windows Registry (`App Paths`), standard Program Files directories, user AppData, system PATH (`where`), and shell protocols (`ms-settings:`).

---

## 17. File System Tools
- **Location**: [`tools/file_tools.py`](file:///d:/juniors/muthuAI/tools/file_tools.py), [`tools/windows/filesystem.py`](file:///d:/juniors/muthuAI/tools/windows/filesystem.py)
- **Role**: Safe file and folder operations: `open_folder`, `open_file`, `read_file`, `list_files`, `create_folder`, `delete_file`, `search_files`, `edit_file`.

---

## 18. Office Automation Layer
- **Location**: [`tools/office_tools.py`](file:///d:/juniors/muthuAI/tools/office_tools.py), [`office/excel/`](file:///d:/juniors/muthuAI/office/excel/), [`office/word/`](file:///d:/juniors/muthuAI/office/word/), [`office/powerpoint/`](file:///d:/juniors/muthuAI/office/powerpoint/), [`office/pdf/`](file:///d:/juniors/muthuAI/office/pdf/)
- **Role**:
  - **Excel**: `openpyxl` workbook generation with headers, formulas, cell styles, borders, and student marks sheet templates.
  - **Word**: `python-docx` document creation with styled headings, paragraphs, and formatted tables.
  - **PowerPoint**: `python-pptx` presentation generation with slide layouts, bullet points, and title cards.
  - **PDF**: `reportlab` multi-page document and table generation.

---

## 19. WhatsApp Integration
- **Location**: [`communication/whatsapp.py`](file:///d:/juniors/muthuAI/communication/whatsapp.py), [`tools/communication_tools.py`](file:///d:/juniors/muthuAI/tools/communication_tools.py)
- **Role**: International phone number validation (`+91...`), URL protocol launching (`https://web.whatsapp.com/send?phone=...` and `whatsapp:` protocol), message typing, and send verification.

---

## 20. Email Integration
- **Location**: [`communication/email.py`](file:///d:/juniors/muthuAI/communication/email.py), [`tools/communication_tools.py`](file:///d:/juniors/muthuAI/tools/communication_tools.py)
- **Role**: IMAP inbox reading, categorization (work, urgent, newsletter, personal), summary generation, and dispatch to WhatsApp alerts.

---

## 21. Instagram Integration
- **Location**: [`communication/instagram.py`](file:///d:/juniors/muthuAI/communication/instagram.py), [`tools/communication_tools.py`](file:///d:/juniors/muthuAI/tools/communication_tools.py)
- **Role**: Instagram web navigation, Reels feed launching, next reel scrolling, and pause/stop controls via Playwright.

---

## 22. YouTube Integration
- **Location**: [`browser/interaction.py`](file:///d:/juniors/muthuAI/browser/interaction.py), [`tools/browser_tools.py`](file:///d:/juniors/muthuAI/tools/browser_tools.py)
- **Role**: Direct YouTube search URL construction, video renderer DOM element extraction, first video URL identification, navigation, and video player verification.

---

## 23. Web Search Engine
- **Location**: [`retrieval/web_search.py`](file:///d:/juniors/muthuAI/retrieval/web_search.py), [`tools/browser_tools.py`](file:///d:/juniors/muthuAI/tools/browser_tools.py)
- **Role**: Multi-provider search cascade: Google News RSS (real-time, date-stamped, primary news publications) + DuckDuckGo HTML scraping + Playwright search fallback.

---

## 24. Document Intelligence (RAG)
- **Location**: [`rag/pipeline.py`](file:///d:/juniors/muthuAI/rag/pipeline.py), [`rag/retrieval/retriever.py`](file:///d:/juniors/muthuAI/rag/retrieval/retriever.py), [`rag/storage/vector_store.py`](file:///d:/juniors/muthuAI/rag/storage/vector_store.py)
- **Role**: User document ingestion (PDF, DOCX, TXT), sentence-transformer embedding, ChromaDB vector indexing, and cosine similarity chunk retrieval for personal notes.

---

## 25. Personal & Task Memory
- **Location**: [`memory/personal_memory.py`](file:///d:/juniors/muthuAI/memory/personal_memory.py), [`memory/desktop_context.py`](file:///d:/juniors/muthuAI/memory/desktop_context.py), [`memory/task_memory.py`](file:///d:/juniors/muthuAI/memory/task_memory.py), [`memory/long_term_memory.py`](file:///d:/juniors/muthuAI/memory/long_term_memory.py)
- **Role**: Persistent JSON fact storage (`remember_fact`, `forget_fact`, `show_memory`), active application window tracking, and context resolution for pronoun/app references.

---

## 26. Current-Information Retrieval
- **Location**: [`retrieval/web_search.py`](file:///d:/juniors/muthuAI/retrieval/web_search.py), [`retrieval/source_processor.py`](file:///d:/juniors/muthuAI/retrieval/source_processor.py), [`ai/prompt_manager.py`](file:///d:/juniors/muthuAI/ai/prompt_manager.py)
- **Role**: Multilingual freshness query detection (English, Tamil, Tanglish), date injection (`August 31 / September 2026`), structured source formatting, and grounded anti-hallucination prompt generation.

---

## 27. PDF Document Generation
- **Location**: [`tools/office_tools.py`](file:///d:/juniors/muthuAI/tools/office_tools.py), [`office/pdf/creator.py`](file:///d:/juniors/muthuAI/office/pdf/creator.py)
- **Role**: ReportLab PDF document generation with styled title headers, multi-column tables, AI summaries, and disk verification.

---

## 28. n8n Discovery & Workflow Integration
- **Location**: [`n8n/discovery/`](file:///d:/juniors/muthuAI/n8n/discovery/)
- **Role**: Local n8n node capability scanner, JSON parser, and workflow trigger mechanism. MCP is not present or required; the core architecture operates entirely natively.

---

## 29. Configuration
- **Location**: [`config/settings.py`](file:///d:/juniors/muthuAI/config/settings.py)
- **Role**: Centralized environment variable management, path resolution, TTS voice selection, logging levels, and audio device parameters.

---

## 30. Environment Variables
- **Location**: [`.env`](file:///d:/juniors/muthuAI/.env), [`.env.example`](file:///d:/juniors/muthuAI/.env.example)
- **Role**: Secure storage for `GEMINI_API_KEY`, `AGENT_NAME`, `TTS_VOICE_TAMIL`, `TTS_VOICE_ENGLISH`, `TTS_RATE`, `LOG_LEVEL`. Zero secrets committed to Git.

---

## 31. Test Suites
- **Location**: [`tests/`](file:///d:/juniors/muthuAI/tests/)
- **Role**: 50+ unit and integration test files covering tools, browser automation, desktop control, office tools, multi-step planning, RAG, web search, and voice pipeline.

---

## 32. Health & Diagnostics
- **Location**: [`diagnostics.py`](file:///d:/juniors/muthuAI/diagnostics.py), [`monitoring/health.py`](file:///d:/juniors/muthuAI/monitoring/health.py), [`monitoring/metrics.py`](file:///d:/juniors/muthuAI/monitoring/metrics.py)
- **Role**: Startup checks for Gemini API key, network connectivity, disk storage, and microphone access. Telemetry metric aggregation for execution duration and tool success rates.
