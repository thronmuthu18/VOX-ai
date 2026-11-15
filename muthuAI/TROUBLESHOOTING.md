# CHAMP — Troubleshooting & FAQ

Solutions for common issues encountered during setup or runtime.

---

## 1. Speech Recognition Errors

### Symptom: `Cannot access microphone` or PyAudio Error
- **Cause**: PyAudio or SpeechRecognition cannot access your default recording device.
- **Fix**:
  1. Open Windows **Sound Settings** (`Win + I` → System → Sound).
  2. Under **Input**, verify your microphone is selected and responsive.
  3. Ensure app permission for microphone access is enabled (`Win + I` → Privacy & Security → Microphone → Enable "Let desktop apps access your microphone").

### Symptom: Speech not recognized or timing out
- **Cause**: Background noise or low microphone volume.
- **Fix**:
  1. Adjust your microphone input volume in Windows settings.
  2. Speak clearly into the microphone after hearing the wake-up prompt.

---

## 2. Gemini API Errors

### Symptom: `I'm unable to connect to Gemini — API key error.`
- **Cause**: `GEMINI_API_KEY` is missing or invalid in `.env`.
- **Fix**:
  1. Verify `.env` exists in the root project folder.
  2. Verify `GEMINI_API_KEY=AIza...` contains a valid key from Google AI Studio.
  3. Avoid quotes around the key unless special characters require them.

---

## 3. Browser & Automation Issues

### Symptom: Playwright browser error or executable missing
- **Cause**: Playwright Chromium browser binaries are not installed.
- **Fix**:
  ```powershell
  playwright install chromium
  ```

### Symptom: WhatsApp Web requires QR code scan
- **Cause**: CHAMP opens WhatsApp Web in a fresh browser session.
- **Fix**: Scan the QR code using your phone's WhatsApp app (Settings → Linked Devices → Link a Device). CHAMP will retain your session for subsequent messages.

---

## 4. Text-to-Speech (TTS) Issues

### Symptom: No audio response / Pygame mixer init warning
- **Cause**: Windows audio output is muted, disconnected, or used exclusively by another application.
- **Fix**:
  1. Check system volume and audio playback device.
  2. Restart CHAMP.

---

## 5. Running Diagnostics

Run `diagnostics.py` to get an automated status report of all system components:

```powershell
python diagnostics.py
```
