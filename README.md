# 🎙️ VOX AI — Intelligent Voice-Controlled Personal AI Assistant

<p align="center">
  <b>Your Voice. Your Intelligence. Your Control.</b>
</p>

<p align="center">
  An AI-powered Windows desktop personal assistant designed to understand natural language, interact with applications, automate computer tasks, and simplify everyday digital workflows.
</p>

<p align="center">
  <a href="https://github.com/thronmuthu18/VOX-ai">GitHub Repository</a>
</p>

---

## 📌 About VOX AI

**VOX AI** is an intelligent, voice-controlled personal assistant designed for Windows desktop environments.

Unlike traditional chatbots that primarily provide text-based answers, VOX AI aims to connect artificial intelligence with real-world computer operations.

Users can interact naturally through voice commands and request assistance with application control, browser automation, web search, file management, and document generation.

Powered by Google's Gemini AI, VOX AI combines conversational intelligence with an extensible agent-based task execution architecture.

The system is designed to support **English, Tamil, and Tanglish**, making computer interaction more natural and accessible.

## ✨ Key Features

### 🎤 1. Voice Interaction
- Natural voice-based interaction.
- Wake-word activation using "Bro".
- Speech-to-text processing.
- Text-to-speech responses.
- English, Tamil, and Tanglish interaction.

### 🧠 2. AI Intelligence
- Gemini AI integration.
- Natural language understanding.
- Context-aware conversations.
- Intent detection.
- Task planning and decomposition.

### 🖥️ 3. Windows Desktop Automation
Designed to support:
- Application launching.
- Keyboard and mouse interaction.
- Window management.
- File Explorer operations.
- Windows desktop interaction.

### 🌐 4. Browser Automation
Designed to support:
- Opening Chrome.
- Navigating websites.
- Google searches.
- YouTube searches.
- Browser interaction and navigation.

### 📂 5. File Management
Designed to support:
- Creating files and folders.
- Reading and organizing files.
- Moving and copying files.
- Download management.
- File operations through natural-language commands.

### 📄 6. AI Document Generation
Planned document-generation workflows include:

| Format | Extension |
|---|---|
| PDF | `.pdf` |
| Word | `.docx` |
| Excel | `.xlsx` |
| PowerPoint | `.pptx` |
| Text | `.txt` |
| CSV | `.csv` |

### 🔎 7. Web Search & RAG
- Live web information retrieval.
- Local document retrieval.
- Retrieval-Augmented Generation (RAG).
- AI-powered information synthesis.

### 💬 8. Communication Automation
Designed integrations include:
- WhatsApp messaging.
- Email reading and summarization.
- Information extraction.
- User-controlled communication workflows.

### 🎨 9. Futuristic Visual Interface
VOX AI includes a dedicated visual assistant concept featuring:

- Animated AI core.
- Listening and speaking states.
- Processing animations.
- Blue, violet, and pink color palette.
- Fullscreen conversation interface.
- Compact floating task interface.

---

## ⚙️ System Architecture

VOX AI follows a modular, agent-based architecture.

```text
             USER
               |
               v
         VOICE INPUT
               |
               v
       WAKE WORD DETECTION
               |
               v
       SPEECH RECOGNITION
               |
               v
        GEMINI AI ENGINE
               |
               v
         INTENT ROUTER
               |
        +------+------+
        |             |
        v             v
   CONVERSATION    TASK REQUEST
        |             |
        |             v
        |        TASK PLANNER
        |             |
        |             v
        |        TOOL REGISTRY
        |             |
        |             v
        |        TOOL EXECUTOR
        |             |
        |      +------+------+------+
        |      |      |      |      |
        |   WINDOWS BROWSER FILES   WEB
        |      |      |      |      |
        |      +------+------+------+
        |             |
        |             v
        |        VERIFICATION
        |             |
        +------+------+
               |
               v
         AI RESPONSE
               |
               v
          TEXT-TO-SPEECH
               |
               v
            VOX AI UI
```

### Core Execution Principle

**UNDERSTAND → PLAN → EXECUTE → VERIFY → RESPOND**

VOX AI is designed to report task completion only after the corresponding operation has been executed and verified.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| AI Engine | Google Gemini |
| AI SDK | Google Gen AI SDK |
| Speech Recognition | SpeechRecognition |
| Text-to-Speech | Edge TTS |
| Audio Processing | Pygame |
| Desktop Automation | PyAutoGUI |
| Computer Vision | OpenCV |
| Visual Interface | Python / Tkinter |
| Development Environment | VS Code |
| Version Control | Git & GitHub |

*Technology availability and integration depend on the current project configuration.*

---

## 📁 Project Architecture

The project is organized into modular components.

```text
VOX-ai/
│
├── app/
│   └── Application entry and orchestration
│
├── agent/
│   └── AI agent and task planning
│
├── tools/
│   └── Tool registry and execution modules
│
├── voice/
│   └── Voice input and processing
│
├── speech/
│   └── Speech output and TTS
│
├── retrieval/
│   └── Web search and retrieval
│
├── visual_ui/
│   └── VOX AI visual interface
│
├── config/
│   └── Application configuration
│
├── tests/
│   └── Project tests
│
├── .env.example
├── .gitignore
├── launcher.py
├── diagnostics.py
├── requirements.txt
└── README.md
```

*This is a conceptual overview. Refer to the actual repository for the complete directory structure.*

---

## 💻 System Requirements

Recommended environment:

- Windows 10 / Windows 11
- Python 3.10 or compatible project-supported version
- Microphone
- Speakers or headphones
- Internet connection
- Google Gemini API key
- VS Code (recommended)

---

## 🚀 Installation Guide

### Step 1 — Clone the Repository

Open PowerShell or Command Prompt.

```bash
git clone https://github.com/thronmuthu18/VOX-ai.git
```

### Step 2 — Navigate to the Project

```bash
cd VOX-ai
```

### Step 3 — Create a Virtual Environment

```bash
python -m venv .venv
```

### Step 4 — Activate the Environment

```bash
.venv\Scripts\activate
```

### Step 5 — Install Dependencies

```bash
python -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

### Step 6 — Configure Environment Variables

Create a `.env` file in the project root.

Add the required configuration using the variable names defined in `.env.example`.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**Security:** Never upload your actual `.env` file, API keys, passwords, or access tokens to GitHub.

### Step 7 — Run VOX AI

Use the project's configured startup launcher.

The repository's existing launcher and batch-file configuration should be followed. Check the project documentation and startup scripts for the exact entry point.

---

## 🎙️ Example Voice Commands

Examples of the intended interaction:

| Command | Expected Action |
|---|---|
| Hey Bro | Activate VOX AI |
| Bro, open Chrome | Launch Chrome |
| Bro, open YouTube | Navigate to YouTube |
| Bro, search Python tutorials | Search for tutorials |
| Bro, create a PDF | Generate a PDF document |
| Bro, open Calculator | Launch Calculator |
| Bro, explain machine learning | AI conversation |
| Bro, search the web for AI news | Retrieve current information |

Commands may be expressed in English, Tamil, or Tanglish.

---

## 📂 Default Workspace

VOX AI uses the following project-level default workspace convention:

```text
M:\
│
├── Downloads\
│
├── Generated\
│   ├── PDF\
│   ├── Word\
│   ├── Excel\
│   ├── PowerPoint\
│   ├── Text\
│   └── Images\
│
├── Projects\
├── Workspace\
└── Temp\
```

Generated and downloaded files should use `M:\` by default unless the user explicitly requests another location.

---

## 🎨 Visual Assistant Modes

VOX AI is designed with two primary display modes.

**1. Fullscreen Conversation Mode**
- Normal AI conversations.
- Listening and speaking.
- Questions and explanations.
- Confirmation requests.

**2. Compact Task Mode**
- Actual desktop task execution.
- Browser automation.
- Application launching.
- File generation.
- Multi-step workflows.

The compact assistant appears at the bottom-right of the screen while tasks execute.

After execution and verification, the interface returns to fullscreen.

---

## 🔐 Security & Privacy

Security is an important part of the project.

- API keys must remain in environment variables.
- Never commit `.env` files.
- Sensitive operations should require confirmation.
- Destructive file operations should be handled carefully.
- External communication should be user-controlled.
- Task completion must be based on actual execution results.

---

## 🧪 Development Status

VOX AI is under active development.

The project already contains modular components for voice interaction, AI conversation, task planning, tool integration, retrieval, and visual interaction.

However, the integration and reliability of all end-to-end execution workflows remain under development.

| Area | Development Status |
|---|---|
| AI Conversation | Working |
| Voice Interaction | Implemented |
| Gemini Integration | Implemented |
| Visual Assistant | Under Development |
| Tool Registry & Execution | Integration in Progress |
| Windows Automation | Requires End-to-End Validation |
| Browser Automation | Requires End-to-End Validation |
| File Generation | Requires End-to-End Validation |
| Multi-Step Task Execution | Integration in Progress |
| Execution Verification | Under Development |

---

## 🔮 Future Improvements

- More reliable autonomous task execution.
- Improved multi-step agent workflows.
- Better Tamil and Tanglish speech recognition.
- Advanced Windows desktop automation.
- Reliable browser interaction.
- End-to-end PDF and Office document generation.
- Improved memory and RAG capabilities.
- Better task verification and recovery.
- Enhanced visual AI experience.
- Additional tool integrations.

---

## 🤝 Contributing

Contributions, suggestions, and ideas are welcome.

If you would like to improve VOX AI:

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes.
4. Test your changes.
5. Submit a Pull Request.

---

## 👨‍💻 Developer

**Muthu**

Project: VOX AI – Intelligent Voice-Controlled Personal AI Assistant

GitHub: [@thronmuthu18](https://github.com/thronmuthu18)

Repository: [VOX-ai](https://github.com/thronmuthu18/VOX-ai)

---

<p align="center">
  <b>VOX AI</b>
  <br/>
  Your Voice. Your Intelligence. Your Control.
  <br/><br/>
  Built to make computer interaction smarter, simpler, and more natural.
</p>
