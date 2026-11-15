# CHAMP — Complete Execution Flow & Request Lifecycle

This document traces the exact step-by-step execution path of every user interaction within the CHAMP architecture.

---

## 1. High-Level Lifecycle Diagram

```
                              USER SPOKEN INPUT
                                      │
                                      ▼
                        VOICE ACTIVITY DETECTION (VAD)
                          (webrtcvad / PyAudio 16kHz)
                                      │
                                      ▼
                          SPEECH-TO-TEXT (STT)
                         (Google Speech API / Vosk)
                                      │
                                      ▼
                          WAKE WORD DETECTOR
                   ("Bro" / "Hey Bro" / "ப்ரோ" / "Hi Bro")
                        [NO BRO = NO ACTION RULE]
                                      │
                                      ▼
                          LANGUAGE CLASSIFIER
                        (Tamil / English / Tanglish)
                                      │
                                      ▼
                          COMMAND NORMALIZER
                      (strip wake word, clean punctuation)
                                      │
                                      ▼
                          CONTEXT RESOLVER
                   (resolve "it", "the file", active app)
                                      │
                                      ▼
                            INTENT ROUTER
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
    [MODE A: CONVERSATION]   [CURRENT INFO / FRESHNESS]    [MODE B: ACTION]
          │                           │                           │
   Check Personal Memory       DNS & Internet Probe      Deterministic Regex Match?
          │                           │                     ├── Yes: 0ms Direct Plan
   Check RAG Keywords?                ▼                     └── No : Gemini Tool Planner
     ├── Yes: ChromaDB        Google News RSS / DDG               │
     └── No : Bypass                  │                           ▼
          │                           ▼                     TaskQueue Graph
          ▼                  Source Deduplication        (task_001, task_002, deps)
     Gemini LLM                       │                           │
  (Spoken Prompt)                     ▼                           ▼
          │                  Date-Aware Grounding       DependencyAwareExecutor
          │                   (ai/prompt_manager.py)              │
          │                           │                     Policy / Risk Check
          │                           ▼                           ├── SAFE: Auto
          │                      Gemini LLM                       └── DANGEROUS: Confirm
          │                           │                           │
          │                           │                           ▼
          │                           │                    Tool Registry (96)
          │                           │                           │
          │                           │                           ▼
          │                           │                    Output Validation
          │                           │                    (File > 0 bytes / Process)
          └───────────────────────────┼───────────────────────────┘
                                      │
                                      ▼
                            RESPONSE GENERATOR
                                      │
                                      ▼
                            MICROSOFT EDGE TTS
                     (ta-IN-ValluvarNeural / en-IN-PrabhatNeural)
                                      │
                                      ▼
                           PYGAME AUDIO PLAYBACK
                         (with Barge-In Interruption)
```

---

## 2. Detailed Execution Pathways

### Path 1: Pure Conversational Q&A (Mode A)
**Example**: *"Bro, what is cloud computing?"*
1. **Audio Capture**: User voice is recorded and VAD detects speech termination.
2. **STT**: Converted to `"Bro, what is cloud computing?"`.
3. **Wake Word**: `"Bro"` detected and authenticated.
4. **Language Detection**: Classifies as English (`en`).
5. **Intent Router**: Identifies pure informational query; routes to `IntentMode.CONVERSATION`.
6. **LLM Synthesis**: Gemini receives the conversation history and generates a natural 2-sentence explanation.
7. **Audio Playback**: Edge TTS streams audio chunks to pygame mixer.

---

### Path 2: Live Current Information / Freshness
**Example**: *"Bro, what is the latest AI news?"*
1. **Wake Word & Language**: `"Bro"` authenticated; English detected.
2. **Freshness Detection**: `is_freshness_query()` flags `"latest"`.
3. **Connectivity Probe**: `check_internet_connectivity()` verifies DNS and internet socket in `<30ms`.
4. **Search Cascade**: `WebSearcher` queries Google News RSS feed for `"latest AI news developments September 2026"`, returning 4 date-tagged verified news snippets.
5. **Grounded Prompting**: `ai.prompt_manager.web_search_response_prompt` injects current date and source snippets into Gemini with strict anti-hallucination instructions.
6. **Gemini Grounding**: Synthesizes verified answer citing reputable sources.
7. **TTS Output**: Speaks response and prints full source links to terminal.

---

### Path 3: Single-Step Deterministic Action (Mode B)
**Example**: *"Bro, open Calculator."*
1. **Command Router**: Matches 0ms regex rule: `r"open\s+(?:the\s+)?calculator"`.
2. **Plan**: `{"tool": "open_application", "arguments": {"name": "calculator"}}` with 0 LLM latency.
3. **Executor**: `DependencyAwareExecutor` calls `tools.application_tools.open_application("calculator")`.
4. **Path Discovery**: Resolved to `calc.exe` and launched via `subprocess.Popen`.
5. **Verification**: `StepValidator` verifies process creation and window existence.
6. **Response**: *"Calculator opened successfully."* $\to$ Edge TTS.

---

### Path 4: Multi-Step Dependent Task (Mode B)
**Example**: *"Bro, open Chrome, open YouTube, and search Python tutorial."*
1. **Command Decomposition**: `VoiceAgentPlanner` splits command into a 2-step task graph:
   - `task_001`: `open_application(name="chrome")` [dependencies: []]
   - `task_002`: `search_google(query="Python tutorial")` [dependencies: ["task_001"]]
2. **Execution Step 1**: Chrome launched via Windows Registry `App Paths` (`chrome.exe`). Status: `SUCCESS`.
3. **Execution Step 2**: Prerequisite `task_001` passed $\to$ Playwright launches and navigates to Google search results for `"Python tutorial"`. Status: `SUCCESS`.
4. **Failure Safeguard**: If `task_001` had failed, `task_002` would be marked `BLOCKED` with truthful error reporting.
5. **Response**: *"Done. All steps completed successfully."*

---

### Path 5: High-Impact Action with Security Confirmation
**Example**: *"Bro, send WhatsApp message to +919876543210 saying Hello from CHAMP."*
1. **Router**: Matches WhatsApp messaging intent.
2. **Policy Engine**: Inspects tool permission (`DANGEROUS`).
3. **Interactive Confirmation**: Suspends execution and prompts user:  
   `"This action will send WhatsApp message 'Hello from CHAMP' to +919876543210. Are you sure you want to proceed? Confirm (yes/no):"`
4. **User Verification**: User inputs `"yes"`.
5. **Execution**: Playwright opens WhatsApp Web / protocol and initiates message transmission.
