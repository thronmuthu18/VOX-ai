# CHAMP — Capability Inventory
> Auto-discovered from source code inspection, 2026-08-28

## Project Overview
| Property | Value |
|---|---|
| Name | CHAMP (Character-based AI/Human Multimodal Platform) |
| Location | `d:\juniors\muthuAI` |
| Python | 3.10.0 (win32) |
| Architecture | Modular; 29 packages, 39+ top-level files |
| Agent Name | CHAMP (env: AGENT_NAME) |
| Wake Word | "bro" (+ variants: champ, peter, புரோ, ப்ரோ) |
| Primary Model | gemini-flash-lite-latest |

---

## Module Map

| Module | Path | Purpose |
|---|---|---|
| `agent` | `agent/` | Orchestrator, command router, intent router, executor |
| `ai` | `ai/` | Gemini client, AgentPlanner, conversation, prompt manager |
| `voice` | `voice/` | Wake word, STT, VAD, language detector, session, pipeline |
| `speech` | `speech/` | Edge-TTS (CancellableTTSPlayer), voice manager |
| `task_queue` | `task_queue/` | Task model (PENDING/RUNNING/SUCCESS/FAILED/BLOCKED/CANCELLED) + TaskQueue |
| `tools` | `tools/` | 40+ tools (see below) |
| `browser` | `browser/` | Playwright BrowserController, discovery, interaction, navigation |
| `communication` | `communication/` | WhatsApp, Instagram, Email |
| `memory` | `memory/` | PersonalMemoryStore, ConversationMemory, LongTermMemory, UserMemory |
| `rag` | `rag/` | RAG pipeline: ingestion, chunking, embeddings, ChromaDB |
| `retrieval` | `retrieval/` | DuckDuckGo/SerpAPI web search |
| `office` | `office/` | Excel/Word/PowerPoint/PDF creators + validators |
| `files` | `files/` | FileWorkspaceManager (create/copy/move/rename) |
| `safety` | `safety/` | PolicyEngine, permissions, confirmation |
| `desktop` | `desktop/` | DesktopController, KeyboardController, MouseController, WindowManager |
| `automation` | `automation/` | BrowserController, PyAutoGUI, WindowsController |
| `n8n` | `n8n/` | n8n workflow discovery |
| `config` | `config/` | Settings, environment |
| `utils` | `utils/` | Logger, helpers, errors |
| `diagnostics` | `diagnostics.py` | Startup diagnostics |

---

## Discovered Tools (40 Registered)

### Windows — Application & System
| # | Tool Name | Module | Description |
|---|---|---|---|
| 1 | `open_application` | `tools/windows/application.py` | Launch any Windows app by name |
| 2 | `list_applications` | `tools/windows/application.py` | List installed applications |
| 3 | `open_folder` | `tools/windows/filesystem.py` | Open a folder in Explorer |
| 4 | `open_file` | `tools/windows/filesystem.py` | Open a file with default program |
| 5 | `delete_file` | `tools/windows/filesystem.py` | Delete a file (HIGH IMPACT) |
| 6 | `delete_folder` | `tools/windows/filesystem.py` | Delete a folder (HIGH IMPACT) |
| 7 | `volume_up` | `tools/windows/system.py` | Increase system volume |
| 8 | `volume_down` | `tools/windows/system.py` | Decrease system volume |
| 9 | `mute_volume` | `tools/windows/system.py` | Toggle mute |
| 10 | `get_time` | `tools/windows/system.py` | Get current time |
| 11 | `get_date` | `tools/windows/system.py` | Get current date |
| 12 | `open_command_prompt` | `tools/windows/system.py` | Open CMD |
| 13 | `open_control_panel` | `tools/windows/system.py` | Open Control Panel |
| 14 | `open_settings` | `tools/windows/system.py` | Open Windows Settings |
| 15 | `open_task_manager` | `tools/windows/system.py` | Open Task Manager |
| 16 | `list_processes` | `tools/windows/process.py` | List running processes |
| 17 | `terminate_process` | `tools/windows/process.py` | Kill a process (HIGH IMPACT) |
| 18 | `keyboard_action` | `tools/windows/input.py` | Keyboard: press/shortcut/type |
| 19 | `mouse_action` | `tools/windows/input.py` | Mouse: click/move/scroll |

### Browser & Web
| # | Tool Name | Module | Description |
|---|---|---|---|
| 20 | `open_browser` | `tools/browser/open_browser.py` | Open Chrome or Edge |
| 21 | `open_website` | `tools/browser/open_website.py` | Navigate to site by name/URL |
| 22 | `search_web` | `tools/browser/search_web.py` | DuckDuckGo/web search |
| 23 | `search_google` | `tools/browser_tools.py` | Google search |
| 24 | `browser_click` | `tools/browser/browser_click.py` | Click element |
| 25 | `browser_type` | `tools/browser/browser_type.py` | Type in browser field |
| 26 | `browser_scroll` | `tools/browser/browser_scroll.py` | Scroll browser page |
| 27 | `browser_read` | `tools/browser/browser_read.py` | Read page content |
| 28 | `search_youtube` | `tools/browser/youtube_tools.py` | YouTube search |
| 29 | `play_youtube` | `tools/browser/youtube_tools.py` | Play first YouTube result |
| 30 | `whatsapp_send_message` | `tools/browser/whatsapp_tools.py` | Send WhatsApp message (HIGH IMPACT) |
| 31 | `instagram_reels_scroll` | `tools/browser/instagram_tools.py` | Scroll Instagram Reels |

### RAG & Memory
| # | Tool Name | Module | Description |
|---|---|---|---|
| 32 | `index_document` | `tools/rag/index_document.py` | Index document into ChromaDB |
| 33 | `search_knowledge` | `tools/rag/search_knowledge.py` | Search indexed documents |
| 34 | `remember_fact` | `tools/memory/remember_fact.py` | Store a fact in personal memory |
| 35 | `forget_fact` | `tools/memory/forget_fact.py` | Remove a fact from memory |
| 36 | `show_memory` | `tools/memory/show_memory.py` | Show all stored facts |

### Office & File Productivity
| # | Tool Name | Module | Description |
|---|---|---|---|
| 37 | `create_excel` | `tools/office/excel_tools.py` | Create xlsx with columns/rows/formulas |
| 38 | `read_excel` | `tools/office/excel_tools.py` | Read an xlsx file |
| 39 | `create_word` | `tools/office/word_tools.py` | Create docx document |
| 40 | `create_powerpoint` | `tools/office/powerpoint_tools.py` | Create pptx presentation |
| 41 | `create_pdf` | `tools/office/pdf_tools.py` | Create PDF report |
| 42 | `create_directory` | `tools/office/file_tools.py` | Create folder |
| 43 | `copy_file` | `tools/office/file_tools.py` | Copy file |
| 44 | `move_file` | `tools/office/file_tools.py` | Move file |
| 45 | `rename_file` | `tools/office/file_tools.py` | Rename file |

---

## Voice Pipeline
```
Microphone
  → PyAudio (audio_input.py)
  → VAD (vad.py) — Voice Activity Detection
  → Google Web Speech API (STT)
  → WakeWordDetector (wake_word.py)
  → CommandRouter (command_router.py) — deterministic 0ms
  → AgentPlanner (ai/planner.py) — Gemini if not deterministic
  → TaskQueue (task_queue/) — dependency-aware execution
  → ToolRegistry.execute()
  → ResultValidator
  → Edge-TTS (speech/tts.py — CancellableTTSPlayer)
  → Pygame mixer → Speaker
```

## Language Support
| Language | STT | TTS Voice | Router |
|---|---|---|---|
| English | ✅ en-IN | `en-IN-NeerjaExpressiveNeural` | ✅ Full |
| Tamil | ✅ ta-IN | `ta-IN-PallaviNeural` | ✅ Unicode patterns |
| Tanglish | ✅ ta-IN + en-IN | `ta-IN-PallaviNeural` | ✅ Romanised patterns |

## Communication Capabilities
| Feature | Module | Status |
|---|---|---|
| WhatsApp send (Playwright) | `communication/whatsapp.py` | BLOCKED (QR login required) |
| WhatsApp call | `communication/whatsapp.py` | BLOCKED (QR login required) |
| Instagram Reels scroll | `communication/instagram.py` | BLOCKED (account required) |
| Email read/classify | `communication/email.py` | BLOCKED (IMAP credentials required) |
| Email → WhatsApp alert | `agent/command_router.py` | BLOCKED (both accounts required) |

## Safety & Policy
| Tool | Classification | Requires Confirmation |
|---|---|---|
| `delete_file` | HIGH_IMPACT | ✅ YES |
| `delete_folder` | HIGH_IMPACT | ✅ YES |
| `terminate_process` | HIGH_IMPACT | ✅ YES |
| `send_email` | HIGH_IMPACT | ✅ YES |
| `whatsapp_send_message` | HIGH_IMPACT | ✅ YES |
| `submit_form` | HIGH_IMPACT | ✅ YES |
| `purchase_product` | HIGH_IMPACT | ✅ YES |
| `execute_shell` | HIGH_IMPACT | ✅ YES |
| All others | SAFE | No |

## Configuration
| Variable | Default | Status |
|---|---|---|
| `GEMINI_API_KEY` | (required) | PRESENT |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | PRESENT |
| `AGENT_NAME` | `CHAMP` | PRESENT |
| `WAKE_WORD` | `bro` | PRESENT |
| `TTS_VOICE_TAMIL` | `ta-IN-PallaviNeural` | PRESENT |
| `TTS_VOICE_ENGLISH` | `en-IN-NeerjaExpressiveNeural` | PRESENT |
| `TTS_RATE` | `+12%` | PRESENT |
| `SERPAPI_KEY` | (optional, DDG fallback) | MISSING (acceptable) |
