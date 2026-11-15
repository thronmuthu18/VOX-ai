# CHAMP — Windows AI Personal Agent v1.0

> A production-grade software-only Windows desktop AI agent powered by Google Gemini.  
> Controlled via natural voice in Tamil, English, and Tanglish across Windows desktop applications, Playwright browser automation, WhatsApp, Instagram Reels, RAG document intelligence, persistent personal memory, and Office file creation.

---

## Central Architecture

```
🎙️ User Voice ("Hey Champ")
         │
  Speech Recognition
         │
  Language Detection (Tamil / English / Tanglish)
         │
  Agent Orchestrator
         │
┌────────┴────────┐
↓                 ↓
Gemini          Deterministic
Reasoning            Tools
   │                 │
┌──┴──┬───┐          │
↓     ↓   ↓          ↓
Memory RAG Web   Windows / Browser / WhatsApp / Instagram / Office / Files
└──┬──┴───┘
   │
Result Validation
   │
Safety Layer (Confirmation & Path Checks)
   │
Final Response (Text + TTS Spoken Audio)
```

---

## Key Capabilities

- 🎙️ **Natural Voice Pipeline**: Continuous wake-word listening (`"Champ"`, `"Hey Champ"`), language-matched TTS responses in Tamil (`ta-IN-PallaviNeural`) and English (`en-IN-NeerjaNeural`).
- ⚡ **0ms Deterministic Fast-Path**: Direct tool execution for system volume, time/date, application launch, and browser navigation.
- 💬 **WhatsApp Automation**: Send messages to contacts via WhatsApp Web with automatic safety confirmation.
- 📱 **Instagram Reels Scrolling**: Open and autoscroll Instagram Reels in a background thread; supports immediate voice interruption via `"Stop"` or `"Cancel"`.
- 📊 **Office File Creation**: Direct Python creation of styled Excel workbooks (`.xlsx`), Word documents (`.docx`), PowerPoint presentations (`.pptx`), and PDF reports (`.pdf`).
- 📚 **Local Document Intelligence (RAG)**: Ingest, chunk, embed, and query local PDF, DOCX, TXT, and Markdown files.
- 🧠 **Persistent Long-Term Memory**: Secure JSON memory store for user profile, preferences, and facts with sensitive secret filtering.

---

## Quick Start

### 1. Automated Setup
Run `setup.bat` to create the virtual environment, install dependencies, and setup Playwright:

```cmd
setup.bat
```

### 2. Configure API Key
Create a `.env` file from `.env.example` and set your `GEMINI_API_KEY`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run Application
Launch CHAMP:

```cmd
run_champ.bat
```

---

## Project Structure

```
muthuAI/
├── agent/                  # Task plan, state tracking, execution, orchestrator
├── ai/                     # Gemini client, conversation manager, intent planner
├── browser/                # Playwright manager, controller, navigation
├── config/                 # Settings, environment configuration
├── data/                   # Documents, vector DB, long-term memory, logs
├── files/                  # File workspace manager
├── memory/                 # Personal long-term memory store
├── monitoring/             # Health checker, metrics collector
├── office/                 # Excel, Word, PowerPoint, PDF creators & validators
├── rag/                    # Ingestion pipeline, chunker, embeddings, retriever, vector store
├── safety/                 # Permission engine, action validator, confirmation handler
├── speech/                 # Edge TTS speech synthesis
├── tools/                  # Windows, Browser, WhatsApp, Instagram, RAG, Memory, Office tools
├── utils/                  # Logger, error hierarchy, helper functions
├── voice/                  # Listener, recognizer, language detector, wake word detector
├── tests/                  # Pytest test suite
├── diagnostics.py          # Pre-flight system check tool
├── setup.bat               # Windows environment installer
├── run_champ.bat           # Production launcher
├── launcher.py             # Python app launcher
├── requirements.txt        # Pinned Python dependencies
└── README.md
```

---

## Documentation

- 📖 [Installation Guide](INSTALLATION.md)
- ⚙️ [Configuration Reference](CONFIGURATION.md)
- 🔧 [Troubleshooting & FAQ](TROUBLESHOOTING.md)
