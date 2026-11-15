# CHAMP — Installation Guide

This document outlines the step-by-step instructions to install and configure **CHAMP** (Windows AI Personal Agent) on a fresh Windows system.

---

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **Python Version**: Python 3.10, 3.11, or 3.12 (64-bit).
- **Microphone**: Working default recording microphone.
- **Audio Speakers / Headphones**: Working audio playback device.
- **Internet Connection**: Required for Gemini API, Edge TTS, Playwright, and Web Retrieval.

---

## Step 1: Clone or Download the Codebase

Extract or clone the project repository to your desired folder (e.g. `D:\juniors\muthuAI` or `C:\Users\YourName\CHAMP`).

```powershell
cd D:\juniors\muthuAI
```

---

## Step 2: Automated Windows Installation (`setup.bat`)

For the easiest setup experience, run the provided automated setup script:

```cmd
setup.bat
```

`setup.bat` will automatically:
1. Create a isolated Python virtual environment (`venv`).
2. Upgrade `pip`.
3. Install all dependencies from `requirements.txt`.
4. Install Playwright Chromium browser binaries (`playwright install chromium`).
5. Execute system diagnostics to verify your environment.

---

## Manual Installation (Alternative)

If you prefer installing dependencies manually, execute the following commands in PowerShell or Command Prompt:

```powershell
# 1. Create Virtual Environment
python -m venv venv

# 2. Activate Virtual Environment
.\venv\Scripts\activate.ps1

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install Dependencies
pip install -r requirements.txt

# 5. Install Playwright Browsers
playwright install chromium
```

---

## Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```
2. Open `.env` in a text editor (Notepad, VS Code, etc.).
3. Insert your **Google Gemini API Key**:
   ```env
   GEMINI_API_KEY=AIzaSy...your_real_key_here...
   ```
4. Save the file.

---

## Step 4: Run System Diagnostics

Verify your installation by running the diagnostics script:

```powershell
python diagnostics.py
```

If all checks report `✓ OK`, CHAMP is ready to launch!

---

## Step 5: Launch CHAMP

To start CHAMP, execute:

```cmd
run_champ.bat
```
Or run directly with Python:
```powershell
python launcher.py
```
