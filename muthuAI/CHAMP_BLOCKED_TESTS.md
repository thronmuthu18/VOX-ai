# CHAMP — Blocked Tests Report
> Generated: 2026-08-28

## Total Blocked: 17 tests

All blocked tests have explicit `@pytest.mark.skip(reason="BLOCKED: ...")` decorators.
These cannot be executed without real hardware, credentials, or external accounts.

---

## BLOCKED-01 — Live STT (English)
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_stt_live_english |
| **Blocked Reason** | Requires microphone input — no audio device in test environment |
| **How to Unblock** | Run on a machine with a microphone. Say "what time is it" and verify STT returns the text. |
| **Expected Behavior** | STT returns non-empty string |

## BLOCKED-02 — Live STT (Tamil)
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_stt_live_tamil |
| **Blocked Reason** | Requires microphone input + Tamil speech |
| **How to Unblock** | Say "என்ன நேரம்" and verify STT returns Tamil/Tanglish text |
| **Expected Behavior** | STT returns non-empty string with Tamil or Latin characters |

## BLOCKED-03 — Live TTS (English)
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_tts_live_english |
| **Blocked Reason** | Requires audio output device (speakers) |
| **How to Unblock** | Call `speak("Hello, I am CHAMP")` and verify audio plays |
| **Expected Behavior** | Audio plays without error, no TTS crash |

## BLOCKED-04 — Live TTS (Tamil)
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_tts_live_tamil |
| **Blocked Reason** | Requires audio output device + Tamil voice |
| **How to Unblock** | Call `speak("வணக்கம்")` with Tamil voice and verify |
| **Expected Behavior** | Tamil audio plays using ta-IN-PallaviNeural voice |

## BLOCKED-05 — Browser Open Chrome
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_browser_open_chrome |
| **Blocked Reason** | Requires Chrome installed + display |
| **Prerequisite** | `playwright install chromium` must be run |
| **How to Unblock** | Run `OpenBrowserTool().execute(browser="chrome")` on a display machine |
| **Expected Behavior** | Chrome launches and browser_manager.page is not None |

## BLOCKED-06 — YouTube Search + Play
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_youtube_search_and_play |
| **Blocked Reason** | Requires Chrome + network + display |
| **How to Unblock** | Full browser session: open Chrome → YouTube → search "Python tutorial" → play first video |
| **Expected Behavior** | Video plays, URL contains `watch?v=` |

## BLOCKED-07 — WhatsApp Send (Live)
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_whatsapp_send_message_live |
| **Blocked Reason** | Requires WhatsApp QR code login — automated QR bypass forbidden |
| **Security Note** | Agent must NEVER bypass WhatsApp login, CAPTCHA, or 2FA |
| **How to Unblock** | Manual test: scan QR on WhatsApp Web, then send to authorized test number |
| **Expected Behavior** | Message appears in WhatsApp conversation |

## BLOCKED-08 — Instagram Reels (Live)
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_instagram_reels_live |
| **Blocked Reason** | Requires Instagram account login |
| **How to Unblock** | Login to Instagram in browser session, then test reels scrolling |
| **Expected Behavior** | Reels scroll, video changes |

## BLOCKED-09 — Email Inbox Read
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_email_inbox_read |
| **Blocked Reason** | Requires IMAP credentials in .env |
| **How to Unblock** | Add EMAIL_ADDRESS and EMAIL_PASSWORD (or APP_PASSWORD) to .env |
| **Expected Behavior** | Returns list of recent emails with sender, subject, date |

## BLOCKED-10 — Gemini Live Conversation
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_gemini_live_conversation |
| **Blocked Reason** | GEMINI_API_KEY in .env not loaded in shell test environment |
| **How to Unblock** | Run `python -c "from ai.gemini_client import GeminiClient; c=GeminiClient(); print(c.generate_response('what is 2+2', []))"` |
| **Expected Behavior** | Returns "4" or similar correct answer |

## BLOCKED-11 — Web Search (Live)
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_web_search_live |
| **Blocked Reason** | Requires network access (DuckDuckGo/SerpAPI) |
| **How to Unblock** | Run `WebSearchTool().execute(query="Python tutorial")` with network |
| **Expected Behavior** | Returns list of search results with URLs and snippets |

## BLOCKED-12 — Camera Open
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_camera_open |
| **Blocked Reason** | Requires camera hardware and display |
| **How to Unblock** | Run on machine with camera: `OpenApplicationTool().execute(name="camera")` |
| **Expected Behavior** | Camera app opens |

## BLOCKED-13 — Flipkart Purchase
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_flipkart_purchase |
| **Blocked Reason** | ⚠️ FINANCIAL ACTION — NEVER AUTO-EXECUTE |
| **Security Rule** | Agent MUST stop before final order/payment and ask for explicit confirmation |
| **How to Test (Manual)** | Navigate to Flipkart cart page and verify agent STOPS at checkout with confirmation prompt |
| **Expected Behavior** | Agent says: "I've added the item to cart. Should I proceed to checkout?" — DOES NOT proceed without YES |

## BLOCKED-14 — n8n Workflow Trigger
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_n8n_workflow_trigger |
| **Blocked Reason** | n8n server not running locally |
| **How to Unblock** | Start n8n: `npx n8n start`, configure webhook URL in CHAMP settings |
| **Expected Behavior** | Workflow triggers and returns success |

## BLOCKED-15 — VS Code Open + Edit
| Property | Value |
|---|---|
| **Test ID** | TestBlockedFeatures::test_vscode_open_and_edit |
| **Blocked Reason** | VS Code not in PATH in test environment |
| **How to Unblock** | Ensure `code` command is in PATH, run: "open VS Code and open main.py" |
| **Expected Behavior** | VS Code opens with the requested file |

## BLOCKED-16 — WhatsApp Send (Communication Module)
| Property | Value |
|---|---|
| **Test ID** | TestCommunicationTools::test_whatsapp_send_live |
| **Blocked Reason** | Real WhatsApp account required |
| **Same as** | BLOCKED-07 |

## BLOCKED-17 — Email Send (Communication Module)
| Property | Value |
|---|---|
| **Test ID** | TestCommunicationTools::test_email_send_live |
| **Blocked Reason** | Email credentials required |
| **Same as** | BLOCKED-09 |

---

## How to Unblock All

```bash
# 1. Playwright Chromium
playwright install chromium

# 2. Email Integration
echo "EMAIL_ADDRESS=your@email.com" >> .env
echo "EMAIL_PASSWORD=your_app_password" >> .env

# 3. n8n
npx n8n start

# 4. Run live tests (hardware/account required)
python -m pytest tests/champ_complete_qa.py -m "not skip" -v
```
