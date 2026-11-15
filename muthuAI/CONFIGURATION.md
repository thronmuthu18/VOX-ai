# CHAMP — Configuration Guide

This guide details all available configuration variables and settings in CHAMP.

---

## Environment Variables (`.env`)

All runtime settings and secrets are loaded from the `.env` file at the root of the project.

| Key | Default | Description |
|-----|---------|-------------|
| `GEMINI_API_KEY` | *(Required)* | Google Gemini API key obtained from Google AI Studio. |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model variant used for intent planning and reasoning. |
| `AGENT_NAME` | `CHAMP` | Identity name used in prompts, logs, and spoken greetings. |
| `WAKE_WORD_ENABLED` | `true` | Enables active wake-word monitoring (`"champ"`, `"hey champ"`, etc.). |
| `WAKE_WORD` | `champ` | Wake phrase keyword. |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `DOCUMENTS_DIR` | `data/documents` | Folder path for document indexing (PDF, DOCX, TXT). |
| `CHROMA_DB_DIR` | `data/chroma_db` | Storage path for ChromaDB vector embeddings. |
| `REQUIRE_CONFIRMATION_FOR_DANGEROUS` | `true` | Requires explicit voice/text confirmation for high-impact actions (file deletion, WhatsApp messages, process termination). |

---

## System Configuration (`config/settings.py`)

Constants and parameters tuned for voice recognition and speech output:

- **Recognition Languages**: `["ta-IN", "en-IN"]` (Tamil and English).
- **Listen Timeout**: `10` seconds (silence threshold before returning to standby).
- **Phrase Limit**: `20` seconds (maximum duration for a single continuous utterance).
- **Tamil TTS Voice**: `ta-IN-PallaviNeural` (Microsoft Edge Neural Voice).
- **English TTS Voice**: `en-IN-NeerjaNeural` (Microsoft Edge Neural Voice).
- **Max Conversation Memory**: `10` turns (rolling context window).

---

## Security & Privacy Policy

1. **No API Keys in Source Code**: Secrets are never hardcoded. All keys are loaded exclusively from `.env`.
2. **Telemetry Protection**: API keys, passwords, authentication tokens, and private documents are redacted before logging.
3. **Action Confirmation**: Operations classified as `CONFIRM_REQUIRED` (such as `whatsapp_send_message`, `delete_file`, `terminate_process`) require explicit user confirmation before execution.
