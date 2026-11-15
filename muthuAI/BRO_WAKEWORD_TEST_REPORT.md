# CHAMP — BRO Wake-Word & Command Execution Report

**Date & Time**: 2026-11-15 17:22:00  
**Active Wake Word**: `BRO` / `bro`  
**Overall Verdict**: 🟢 PRODUCTION READY  
**Pass Rate**: 100.0% (41/41 Passed)  

---

## 1. Summary Statistics

| Metric | Count |
|---|---|
| Total Tests | 41 |
| ✅ Passed | 41 |
| ❌ Failed | 0 |
| 🔒 Blocked | 0 |
| Pass Rate | 100.0% |

---

## 2. Test Execution Details

| Category | Input Phrase | Wake Detected? | Extracted Command | Intent | Expected | Actual | Result | Latency |
|---|---|---|---|---|---|---|---|---|
| Wake-Word Positive | `bro` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 0ms |
| Wake-Word Positive | `hey bro` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 0ms |
| Wake-Word Positive | `hi bro` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 1ms |
| Wake-Word Positive | `hello bro` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 0ms |
| Wake-Word Positive | `come on bro` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 0ms |
| Wake-Word Positive | `wake up bro` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 0ms |
| Wake-Word Positive | `bro come here` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 0ms |
| Wake-Word Positive | `bro listen` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 1ms |
| Wake-Word Positive | `hey bro listen` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 0ms |
| Wake-Word Positive | `okay bro` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 0ms |
| Wake-Word Positive | `Hey bro, open YouTube.` | True | `open YouTube` | WAKE_WORD_ACTIVATION | activated=True, cmd='open YouTube' | activated=True, cmd='open YouTube' | ✅ PASS | 0ms |
| Wake-Word Positive | `Bro, open Chrome.` | True | `open Chrome` | WAKE_WORD_ACTIVATION | activated=True, cmd='open Chrome' | activated=True, cmd='open Chrome' | ✅ PASS | 0ms |
| Wake-Word Positive | `Hi bro, open Google.` | True | `open Google` | WAKE_WORD_ACTIVATION | activated=True, cmd='open Google' | activated=True, cmd='open Google' | ✅ PASS | 1ms |
| Wake-Word Positive | `Come on bro, open Excel.` | True | `open Excel` | WAKE_WORD_ACTIVATION | activated=True, cmd='open Excel' | activated=True, cmd='open Excel' | ✅ PASS | 0ms |
| Wake-Word Positive | `Bro, send a WhatsApp message.` | True | `send a WhatsApp message` | WAKE_WORD_ACTIVATION | activated=True, cmd='send a WhatsApp message' | activated=True, cmd='send a WhatsApp message' | ✅ PASS | 0ms |
| Wake-Word Positive | `Hey bro, search YouTube for Python tutorial.` | True | `search YouTube for Python tutorial` | WAKE_WORD_ACTIVATION | activated=True, cmd='search YouTube for Python tutorial' | activated=True, cmd='search YouTube for Python tutorial' | ✅ PASS | 0ms |
| Wake-Word Positive | `Bro, open VS Code.` | True | `open VS Code` | WAKE_WORD_ACTIVATION | activated=True, cmd='open VS Code' | activated=True, cmd='open VS Code' | ✅ PASS | 0ms |
| Wake-Word Positive | `Bro, open Google Sheets.` | True | `open Google Sheets` | WAKE_WORD_ACTIVATION | activated=True, cmd='open Google Sheets' | activated=True, cmd='open Google Sheets' | ✅ PASS | 0ms |
| Wake-Word Positive | `புரோ` | True | `` | WAKE_WORD_ACTIVATION | activated=True, cmd='' | activated=True, cmd='' | ✅ PASS | 1ms |
| Wake-Word Positive | `ப்ரோ ஓப்பன் குரோம்` | True | `ஓப்பன் குரோம்` | WAKE_WORD_ACTIVATION | activated=True, cmd='ஓப்பன் குரோம்' | activated=True, cmd='ஓப்பன் குரோம்' | ✅ PASS | 0ms |
| Wake-Word Positive | `ஹே பிரோ open Chrome` | True | `open Chrome` | WAKE_WORD_ACTIVATION | activated=True, cmd='open Chrome' | activated=True, cmd='open Chrome' | ✅ PASS | 0ms |
| Wake-Word Negative | `Open YouTube.` | False | `` | IGNORE_SPEECH | activated=False (Remain Idle) | activated=False | ✅ PASS | 0ms |
| Wake-Word Negative | `What is machine learning?` | False | `` | IGNORE_SPEECH | activated=False (Remain Idle) | activated=False | ✅ PASS | 0ms |
| Wake-Word Negative | `Open Chrome.` | False | `` | IGNORE_SPEECH | activated=False (Remain Idle) | activated=False | ✅ PASS | 0ms |
| Wake-Word Negative | `Send a WhatsApp message.` | False | `` | IGNORE_SPEECH | activated=False (Remain Idle) | activated=False | ✅ PASS | 0ms |
| Wake-Word Negative | `Good morning everyone.` | False | `` | IGNORE_SPEECH | activated=False (Remain Idle) | activated=False | ✅ PASS | 0ms |
| Wake-Word Negative | `Increase system volume.` | False | `` | IGNORE_SPEECH | activated=False (Remain Idle) | activated=False | ✅ PASS | 0ms |
| Wake-Word Negative | `Search Python tutorial.` | False | `` | IGNORE_SPEECH | activated=False (Remain Idle) | activated=False | ✅ PASS | 0ms |
| Wake-Word Negative | `Open Microsoft Word.` | False | `` | IGNORE_SPEECH | activated=False (Remain Idle) | activated=False | ✅ PASS | 0ms |
| Application Launch | `Bro, open Chrome` | True | `open Chrome` | ACTION | Chrome opened successfully | Chrome opened successfully. | ✅ PASS | 410ms |
| Application Launch | `Bro, open Notepad` | True | `open Notepad` | ACTION | Notepad opened successfully | Notepad opened successfully. | ✅ PASS | 354ms |
| Application Launch | `Bro, open Calculator` | True | `open Calculator` | ACTION | Calculator opened successfully | Calculator opened successfully. | ✅ PASS | 313ms |
| Application Launch | `Bro, open File Explorer` | True | `open File Explorer` | ACTION | File Explorer opened successfully | File Explorer opened successfully. | ✅ PASS | 317ms |
| Application Launch | `Parameter alias check (name/app_name)` | True | `open notepad` | ACTION | Both 'name' and 'app_name' succeed | r1=True, r2=True | ✅ PASS | 681ms |
| Tanglish / Tamil | `Bro, YouTube open pannu.` | True | `YouTube open pannu` | ACTION | Extracted: YouTube open pannu. | cmd=YouTube open pannu | ✅ PASS | 0ms |
| Tanglish / Tamil | `Hey bro, Chrome open panni Google-la Python search pannu.` | True | `Chrome open panni Google-la Python search pannu` | ACTION | Extracted: Chrome open panni Google-la Python search pannu. | cmd=Chrome open panni Google-la Python search pannu | ✅ PASS | 0ms |
| Tanglish / Tamil | `Bro, WhatsApp-la indha number-ku message anuppu.` | True | `WhatsApp-la indha number-ku message anuppu` | ACTION | Extracted: WhatsApp-la indha number-ku message anuppu. | cmd=WhatsApp-la indha number-ku message anuppu | ✅ PASS | 1ms |
| Tanglish / Tamil | `Hi bro, volume konjam increase pannu.` | True | `volume konjam increase pannu` | ACTION | Extracted: volume konjam increase pannu. | cmd=volume konjam increase pannu | ✅ PASS | 0ms |
| Tanglish / Tamil | `Bro, enoda Excel file open pannu.` | True | `enoda Excel file open pannu` | ACTION | Extracted: enoda Excel file open pannu. | cmd=enoda Excel file open pannu | ✅ PASS | 0ms |
| WhatsApp Parsing | `Bro, WhatsApp-la 9876543210-ku 'I will call you later' message send pannu.` | True | `WhatsApp-la 9876543210-ku 'I will call you later' message send pannu` | WHATSAPP_SEND | Recipient=9876543210, Msg='I will call you later' | recipient_in_cmd=True, msg_in_cmd=True | ✅ PASS | 1ms |
| Current Web Info | `Bro, what's the latest AI news?` | True | `what's the latest AI news` | WEB_SEARCH_ANSWER | Live search results returned | 2 search results returned | ✅ PASS | 694ms |

---

## 3. Architecture & Verification Summary

1. **Wake-Word Pipeline**: `BRO` is active and configured as default across `.env`, `environment.py`, and `voice/wake_word.py`.
2. **Negative Speech Filtering**: Speech without the `BRO` keyword is safely ignored in standby mode without making unnecessary LLM calls.
3. **Command Extraction**: Activation phrases like `Hey bro, `, `Hi bro, `, `Come on bro, ` are cleanly stripped before passing commands to tools.
4. **Application Launching**: Robust `launch_application()` locates Chrome across `%ProgramFiles%`, `%ProgramFiles(x86)%`, and `%LocalAppData%` without failing on `chrome.exe` PATH lookup.
5. **Parameter Aliases**: `open_application` and `open_folder` accept `name`/`app_name` and `path`/`folder_name` seamlessly.

---

*Report generated by test_bro_wakeword_pipeline.py*