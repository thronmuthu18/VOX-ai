# CHAMP — Production Startup & Run Guide

---

## 1. Prerequisites & Environment

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.10 or higher
- **Microphone**: Working audio input device configured as Windows default
- **Speakers**: Audio output device configured as Windows default
- **Internet**: Active network connection for Gemini API, Google STT, Edge TTS, and Web Search

---

## 2. Configuration Setup (`.env`)

Verify that `.env` exists in the root directory `d:\juniors\muthuAI\.env` with the following variables:

```env
# Primary LLM API Key (Required)
GEMINI_API_KEY=your_gemini_api_key_here

# Voice Pipeline Configuration
CHAMP_WAKE_PHRASE=bro
CHAMP_DEFAULT_LANGUAGE=en
CHAMP_TTS_VOICE_EN=en-IN-PrabhatNeural
CHAMP_TTS_VOICE_TA=ta-IN-ValluvarNeural

# Optional Search API Keys (Google News RSS & DuckDuckGo run without keys)
# TAVILY_API_KEY=
# SERPAPI_API_KEY=

# Optional Email IMAP Integration
# EMAIL_USER=your_email@gmail.com
# EMAIL_PASSWORD=your_app_password
```

---

## 3. Dependency Installation

If setting up on a new environment:
```powershell
cd d:\juniors\muthuAI
pip install -r requirements.txt
playwright install chromium
```

---

## 4. How to Launch CHAMP

### Method 1: Interactive Batch Launcher (Recommended)
Double-click [`run_champ.bat`](file:///d:/juniors/muthuAI/run_champ.bat) or run from PowerShell:
```powershell
.\run_champ.bat
```

### Method 2: Direct Python Launch
```powershell
cd d:\juniors\muthuAI
python app/main.py
```

### Method 3: System Diagnostics & Health Check
```powershell
python diagnostics.py
```

---

## 5. Running the Test Suites

### Complete 30-Benchmark Agent Test Suite
```powershell
python tests/test_complete_30_benchmarks.py
```

### Current Information & Web Search Test Suite
```powershell
python tests/test_web_search_comprehensive.py
```

### Subsystem Verification Test
```powershell
python tests/audit_system.py
```

---

## 6. Supported Voice Commands Examples

- **Conversation (English)**: *"Bro, what is machine learning?"*
- **Conversation (Tamil)**: *"Bro, செயற்கை நுண்ணறிவு என்றால் என்ன?"*
- **Conversation (Tanglish)**: *"Bro, cloud computing pathi brief-ah explain pannu."*
- **Current News**: *"Bro, what is the latest technology news today?"*
- **Local News**: *"Bro, what happened in Tamil Nadu today?"*
- **Application Launching**: *"Bro, open Chrome."* / *"Bro, open Calculator."* / *"Bro, open VS Code."*
- **Browser Automation**: *"Bro, open YouTube and search Python tutorial."*
- **Office Automation**: *"Bro, create an Excel sheet with Name, Age and Marks."*
- **Document Creation**: *"Bro, create a PDF report about Neural Networks."*
- **Audio Control**: *"Bro, volume up."* / *"Bro, volume down."*
- **File System**: *"Bro, open D drive."*
