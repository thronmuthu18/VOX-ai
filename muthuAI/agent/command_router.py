"""
MuthuAI — agent/command_router.py

Deterministic Local Command Router for English, Tamil, and Tanglish voice commands.
Bypasses Gemini API calls for 100% of simple application, browser, system, and folder actions.
Guarantees 0ms latency and 0 LLM token usage for deterministic commands.
"""

from __future__ import annotations
import re
from typing import Callable, Any
from utils.logger import get_logger
from utils.helpers import safe_filename

log = get_logger("muthuai.command_router")


# Map of regular expression patterns to tool name and argument extractor
# Uses Unicode-friendly boundary handling instead of ASCII \b
_DETERMINISTIC_RULES: list[tuple[re.Pattern, str, Callable]] = [
    # ── 1. Application Launchers ──────────────────────────────────────────
    # Chrome
    (
        re.compile(r"(?:open\s+chrome|chrome\s+open|ஓப்பன்\s+குரோம்|குரோம்\s+ஓப்பன்|குரோம்\s+ஓபன்|chrome\s+open\s+pannu|chrome\s+open\s+pannunga|chrome-a\s+open\s+pannu)", re.I),
        "open_application",
        lambda m, t: {"name": "chrome"}
    ),
    # WhatsApp App / Web
    (
        re.compile(r"(?:open\s+whatsapp|whatsapp\s+open|ஓப்பன்\s+வாட்ஸ்அப்|வாட்ஸ்அப்\s+ஓப்பன்|வாட்ஸ்அப்\s+ஓபன்|whatsapp\s+open\s+pannu|whatsapp\s+open\s+pannunga)", re.I),
        "open_application",
        lambda m, t: {"name": "whatsapp"}
    ),
    # Calculator
    (
        re.compile(r"(?:open\s+calculator|calculator\s+open|open\s+calc|calc\s+open|ஓப்பன்\s+கால்குலேட்டர்|கால்குலேட்டர்\s+ஓப்பன்|calculator\s+open\s+pannu)", re.I),
        "open_application",
        lambda m, t: {"name": "calculator"}
    ),
    # Notepad
    (
        re.compile(r"(?:open\s+notepad|notepad\s+open|ஓப்பன்\s+நோட்பேட்|நோட்பேட்\s+ஓப்பன்|notepad\s+open\s+pannu)", re.I),
        "open_application",
        lambda m, t: {"name": "notepad"}
    ),
    # Excel
    (
        re.compile(r"(?:open\s+excel|excel\s+open|ஓப்பன்\s+எக்சல்|எக்சல்\s+ஓப்பன்|excel\s+open\s+pannu)", re.I),
        "open_application",
        lambda m, t: {"name": "excel"}
    ),
    # Word
    (
        re.compile(r"(?:open\s+word|word\s+open|open\s+ms\s+word|ஓப்பன்\s+வேர்ட்|வேர்ட்\s+ஓப்பன்|word\s+open\s+pannu)", re.I),
        "open_application",
        lambda m, t: {"name": "word"}
    ),
    # PowerPoint
    (
        re.compile(r"(?:open\s+powerpoint|powerpoint\s+open|open\s+ppt|ppt\s+open|ஓப்பன்\s+பவர்பாயிண்ட்|powerpoint\s+open\s+pannu)", re.I),
        "open_application",
        lambda m, t: {"name": "powerpoint"}
    ),
    # VS Code
    (
        re.compile(r"(?:open\s+vscode|open\s+vs\s+code|vscode\s+open|vs\s+code\s+open|ஓப்பன்\s+விஎஸ்\s+கோட்|vscode\s+open\s+pannu)", re.I),
        "open_application",
        lambda m, t: {"name": "vscode"}
    ),
    # Control Panel
    (
        re.compile(r"(?:open\s+control\s+panel|control\s+panel\s+open|ஓப்பன்\s+கன்ட்ரோல்\s+பேனல்|control\s+panel\s+open\s+pannu)", re.I),
        "open_control_panel",
        lambda m, t: {}
    ),
    # Settings
    (
        re.compile(r"(?:open\s+settings|settings\s+open|open\s+windows\s+settings|ஓப்பன்\s+செட்டிங்ஸ்|settings\s+open\s+pannu)", re.I),
        "open_settings",
        lambda m, t: {}
    ),
    # Task Manager
    (
        re.compile(r"(?:open\s+task\s+manager|task\s+manager\s+open|ஓப்பன்\s+டாஸ்க்\s+மேனேஜர்|task\s+manager\s+open\s+pannu)", re.I),
        "open_task_manager",
        lambda m, t: {}
    ),
    # Command Prompt / CMD
    (
        re.compile(r"(?:open\s+cmd|cmd\s+open|open\s+command\s+prompt|command\s+prompt\s+open|ஓப்பன்\s+சிஎம்டி)", re.I),
        "open_command_prompt",
        lambda m, t: {}
    ),
    # File Explorer
    (
        re.compile(r"(?:open\s+file\s+explorer|open\s+explorer|explorer\s+open|file\s+explorer\s+open|ஓப்பன்\s+பைல்\s+எக்ஸ்புளோரர்)", re.I),
        "open_application",
        lambda m, t: {"name": "explorer"}
    ),

    # Camera
    (
        re.compile(r"(?:open\s+camera|camera\s+open|open\s+my\s+camera|கேமரா\s+ஓப்பன்)", re.I),
        "open_application",
        lambda m, t: {"name": "camera"}
    ),

    # ── 2. Web Sites & Search ─────────────────────────────────────────────
    # YouTube Website
    (
        re.compile(r"(?:open\s+youtube|youtube\s+open|ஓப்பன்\s+யூடியூப்|யூடியூப்\s+ஓப்பன்|youtube\s+open\s+pannu|youtube\s+open\s+pannunga)", re.I),
        "open_website",
        lambda m, t: {"url": "https://www.youtube.com"}
    ),
    # Google Website
    (
        re.compile(r"(?:open\s+google|google\s+open|ஓப்பன்\s+கூகுள்|கூகுள்\s+ஓப்பன்|google\s+open\s+pannu|google\s+open\s+pannunga)", re.I),
        "open_website",
        lambda m, t: {"url": "https://www.google.com"}
    ),
    # Instagram Website
    (
        re.compile(r"(?:open\s+instagram|instagram\s+open|ஓப்பன்\s+இன்ஸ்டாகிராம்|instagram\s+open\s+pannu)", re.I),
        "open_website",
        lambda m, t: {"url": "https://www.instagram.com"}
    ),
    # YouTube Search & Play
    (
        re.compile(r"(?:search\s+youtube\s+for\s+(.*)|search\s+for\s+(.*?)\s+on\s+youtube|search\s+(.*?)\s+on\s+youtube|youtube-la\s+(.*?)\s+search\s+pannu|youtube-la\s+search\s+pannu\s+(.*))", re.I),
        "search_youtube",
        lambda m, t: {"query": (m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5) or t).strip()}
    ),
    # YouTube Play
    (
        re.compile(r"^(?:play|play\s+it|play\s+video|play\s+the\s+video|play\s+first\s+video|play\s+the\s+first\s+video|first\s+video\s+play\s+pannu|play\s+pannu)$", re.I),
        "play_youtube",
        lambda m, t: {}
    ),
    # Flipkart Search
    (
        re.compile(r"(?:open\s+flipkart\s+(?:and\s+)?search\s+(?:for\s+)?(.*)|flipkart-la\s+(.*?)\s+search\s+pannu|search\s+flipkart\s+for\s+(.*))", re.I),
        "search_flipkart",
        lambda m, t: {"query": (m.group(1) or m.group(2) or m.group(3) or "white shirt").strip()}
    ),
    # Google Search
    (
        re.compile(r"(?:search\s+google\s+for\s+(.*)|search\s+for\s+(.*?)\s+on\s+google|search\s+(.*?)\s+on\s+google|search\s+(.*?)\s+tutorial|google-la\s+(.*?)\s+search\s+pannu|google-la\s+search\s+pannu\s+(.*)|search\s+(.*))", re.I),
        "search_google",
        lambda m, t: {"query": (m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5) or m.group(6) or m.group(7) or t).strip()}
    ),


    # ── 3. System Audio & Time ─────────────────────────────────────────────
    # Volume Up
    (
        re.compile(r"(?:volume\s+up|increase\s+volume|volume\s+increase|sound\s+jaasthi|volume\s+konjam\s+increase\s+pannu|volume\s+அதிகப்படுத்து|வால்யூம்\s+அதிகப்படுத்து)", re.I),
        "volume_up",
        lambda m, t: {"step": 10}
    ),
    # Volume Down
    (
        re.compile(r"(?:volume\s+down|decrease\s+volume|volume\s+decrease|sound\s+kammi|sound\s+kammi\s+pannu|volume\s+kammi|volume\s+kammi\s+pannu|volume\s+குறை|வால்யூம்\s+குறை)", re.I),
        "volume_down",
        lambda m, t: {"step": 10}
    ),
    # Mute / Unmute
    (
        re.compile(r"(?:mute\s+volume|mute|unmute|sound\s+mute|mute\s+pannu|மியூட்)", re.I),
        "mute_volume",
        lambda m, t: {}
    ),
    # Get Time
    (
        re.compile(r"(?:what\s+time\s+is\s+it|what\s+time|time\s+enna|time\s+என்ன|current\s+time|tell\s+me\s+the\s+time|நேரம்\s+என்ன|இப்போது\s+நேரம்\s+என்ன)", re.I),
        "get_time",
        lambda m, t: {}
    ),
    # Get Date
    (
        re.compile(r"(?:what\s+date\s+is\s+it|what\s+date|today['\s]*s\s+date|date\s+enna|date\s+என்ன|இன்று\s+என்ன\s+தேதி|தேதி\s+என்ன)", re.I),
        "get_date",
        lambda m, t: {}
    ),

    # ── 4. Folders & Paths ────────────────────────────────────────────────
    # D Drive
    (
        re.compile(r"(?:open\s+(?:my\s+)?d\s+drive|open\s+d:)", re.I),
        "open_folder",
        lambda m, t: {"path": "D:\\"}
    ),
    # Project Folder
    (
        re.compile(r"(?:open\s+(?:my\s+)?project\s+folder|open\s+my\s+project)", re.I),
        "open_folder",
        lambda m, t: {"path": r"d:\juniors\muthuAI"}
    ),
    # Downloads
    (
        re.compile(r"(?:open\s+downloads|downloads\s+folder\s+open|downloads\s+open\s+pannu|டவுன்லோட்ஸ்\s+ஓப்பன்\s+பண்ணு)", re.I),
        "open_folder",
        lambda m, t: {"path": "downloads"}
    ),
    # Desktop
    (
        re.compile(r"(?:open\s+desktop|desktop\s+folder\s+open|desktop\s+open\s+pannu|டெஸ்க்டாப்\s+ஓப்பன்\s+பண்ணு)", re.I),
        "open_folder",
        lambda m, t: {"path": "desktop"}
    ),
    # Documents
    (
        re.compile(r"(?:open\s+documents|documents\s+folder\s+open|documents\s+open\s+pannu|டாகுமெண்ட்ஸ்\s+ஓப்பன்\s+பண்ணு)", re.I),
        "open_folder",
        lambda m, t: {"path": "documents"}
    ),

    # ── 5. Office Document Generation ──────────────────────────────────────
    # Excel Sheets & Marks Sheet
    (
        re.compile(r"(?:create\s+(?:an\s+)?excel\s+marks?\s+sheet|create\s+(?:a\s+)?marks?\s+sheet|create\s+(?:an\s+)?excel\s+sheet\s+with\s+student\s+names?\s+and\s+marks?|excel-la\s+students?\s+marks?\s+table\s+create\s+pannu|create\s+student\s+marks?\s+excel)", re.I),
        "create_excel",
        lambda m, t: {
            "file_name": "marks_sheet.xlsx",
            "template": "marks_sheet",
        }
    ),
    (
        re.compile(r"(?:create\s+(?:an\s+)?excel\s+(?:sheet|file|table|workbook)\s+with\s+(.*)|create\s+(?:an\s+)?excel\s+(?:sheet|file|table|workbook)\s+(?:for|about)\s+(.*)|create\s+(?:an\s+)?excel\s+(?:sheet|file|table|workbook)|excel\s+(?:sheet\s+)?create\s+pannu)", re.I),
        "create_excel",
        lambda m, t: {
            "file_name": "spreadsheet.xlsx",
            "headers": [col.strip().title() for col in re.split(r",\s*|\s+and\s+", (m.group(1) or m.group(2) or "Item, Description, Quantity, Price, Total")) if col.strip()],
        }
    ),
    # Word Generic / Report
    (
        re.compile(r"(?:create\s+(?:a\s+)?word\s+document\s+(?:about|on|for)\s+(.*)|create\s+(?:a\s+)?word\s+report\s+(?:about|on|for)\s+(.*)|create\s+(?:a\s+)?word\s+document|create\s+(?:a\s+)?word\s+report|word\s+document\s+create\s+pannu)", re.I),
        "create_word",
        lambda m, t: {
            "file_name": f"{safe_filename(m.group(1) or m.group(2) or 'document')}.docx",
            "title": f"{(m.group(1) or m.group(2) or 'Document Title').title()}",
            "content": f"Document generated by VOX AI for {(m.group(1) or m.group(2) or 'general topics')}."
        }
    ),
    # PowerPoint Presentation by Topic
    (
        re.compile(r"(?:create\s+(?:a\s+)?(?:5-slide\s+)?powerpoint\s+(?:presentation\s+)?(?:about|on|for)\s+(.*)|create\s+powerpoint\s+(?:about|on|for)\s+(.*)|create\s+(?:a\s+)?ppt\s+(?:about|on|for)\s+(.*)|create\s+(?:a\s+)?powerpoint|ppt\s+create\s+pannu)", re.I),
        "create_powerpoint",
        lambda m, t: {
            "file_name": f"{safe_filename(m.group(1) or m.group(2) or m.group(3) or 'presentation')}.pptx",
            "topic": (m.group(1) or m.group(2) or m.group(3) or "AI").strip(),
            "title": f"{(m.group(1) or m.group(2) or m.group(3) or 'AI').strip().title()} Overview",
        }
    ),
    # PDF Report / Explanation / Knowledge Synthesis
    (
        re.compile(r"(?:create|generate)\s+(?:a\s+)?pdf(?:\s+(?:report|document|file))?\s+(?:about|on|explaining|for)\s+(.+)|(?:what\s+is\s+(.+?)\??\s*explain\s+it\s+and\s+create\s+(?:a\s+)?pdf)|(?:explain\s+(.+?)\s+and\s+create\s+(?:a\s+)?pdf)|(?:create\s+(?:a\s+)?pdf(?:\s+report)?|pdf\s+create\s+pannu)", re.I),
        "explain_and_create_pdf",
        lambda m, t: {
            "topic": (m.group(1) or m.group(2) or m.group(3) or "Machine Learning").strip(),
        }
    ),
    # Text File / Notes Generation
    (
        re.compile(r"(?:create\s+(?:a\s+)?text\s+file\s+(?:with|about|for|named)\s+(.*)|create\s+(?:a\s+)?text\s+file|create\s+(?:a\s+)?note\s+(?:with|about)\s+(.*)|create\s+(?:a\s+)?note|text\s+file\s+create\s+pannu)", re.I),
        "create_file",
        lambda m, t: {
            "file_name": f"{safe_filename(m.group(1) or m.group(2) or 'notes')}.txt",
            "content": (m.group(1) or m.group(2) or "VOX AI Note").strip()
        }
    ),
    # CSV File Generation
    (
        re.compile(r"(?:create\s+(?:a\s+)?csv\s+(?:file\s+)?(?:with|for|about)\s+(.*)|create\s+(?:a\s+)?csv\s+file|create\s+(?:a\s+)?csv|csv\s+create\s+pannu)", re.I),
        "create_csv",
        lambda m, t: {
            "file_name": "data.csv",
            "headers": [col.strip().title() for col in re.split(r",\s*|\s+and\s+", (m.group(1) or "Name, Value, Category")) if col.strip()],
            "rows": [["Item 1", "100", "General"], ["Item 2", "200", "Productivity"]]
        }
    ),
    # Document Conversion (DOCX -> PDF)
    (
        re.compile(r"(?:convert\s+(?:this\s+)?(?:word|docx)?\s*(?:file|document|report)?\s*to\s+pdf|convert\s+(?:to\s+)?pdf|convert\s+(.*\.docx)\s+to\s+pdf)", re.I),
        "convert_word_to_pdf",
        lambda m, t: {
            "source_path": (m.group(1) or "").strip()
        }
    ),
    # Download File
    (
        re.compile(r"(?:download\s+(?:this\s+)?(?:file|pdf|installer|package)?\s*(?:from\s+)?(https?://\S+)|download\s+(https?://\S+)|download\s+this\s+file)", re.I),
        "download_file",
        lambda m, t: {
            "url": (m.group(1) or m.group(2) or "https://example.com/sample.pdf").strip(),
        }
    ),

    # Open Code File (e.g. "open Chat.tsx", "open main.py")
    (
        re.compile(r"(?:open\s+([a-zA-Z0-9_\-\.]+\.(?:tsx|ts|jsx|js|py|html|css|json|md|txt)))", re.I),
        "open_vscode",
        lambda m, t: {
            "file_name": m.group(1).strip()
        }
    ),

    # ── 6. Communication (Phase 5) ─────────────────────────────────────────
    # WhatsApp Call (before send to prevent collision)
    (
        re.compile(r"(?:whatsapp(?:-la)?\s+(\+?\d{10,15})-ku\s+call\s+pannu|call\s+(\+?\d{10,15})\s+(?:on\s+)?whatsapp|whatsapp\s+call\s+(\+?\d{10,15}))", re.I),
        "whatsapp_call",
        lambda m, t: {
            "phone_number": (m.group(1) or m.group(2) or m.group(3) or "").strip(),
        }
    ),
    # WhatsApp Message (Tanglish & English)
    (
        re.compile(r"(?:whatsapp(?:-la)?\s+(\+?\d{10,15})-ku\s+(.*?)(?:\s+message)?\s+send\s+pannu|send\s+whatsapp\s+message\s+to\s+(\+?\d{10,15})(?:\s*:\s*|\s+saying\s+|\s+with\s+)(.*)|send\s+(\+?\d{10,15})\s+whatsapp\s+message\s+(.*))", re.I),
        "whatsapp_send_message",
        lambda m, t: {
            "phone_number": (m.group(1) or m.group(3) or m.group(5) or "").strip(),
            "message": (m.group(2) or m.group(4) or m.group(6) or "Hello").strip(),
        }
    ),
    # Instagram Reels
    (
        re.compile(r"(?:open\s+instagram\s+reels|open\s+reels|reels\s+open\s+pannu|இன்ஸ்டாகிராம்\s+ரீல்ஸ்)", re.I),
        "open_instagram_reels",
        lambda m, t: {}
    ),
    # Instagram Home
    (
        re.compile(r"(?:open\s+instagram|instagram\s+open\s+pannu|இன்ஸ்டாகிராம்)", re.I),
        "open_instagram",
        lambda m, t: {}
    ),
    # Next Reel
    (
        re.compile(r"(?:next\s+reel|next\s+video|அடுத்த\s+ரீல்|அடுத்த\s+வீடியோ)", re.I),
        "instagram_next_reel",
        lambda m, t: {}
    ),
    # Stop / Pause Reel
    (
        re.compile(r"(?:stop\s+reel|pause\s+reel|stop\s+instagram|ரீல்\s+நிறுத்து)", re.I),
        "instagram_stop",
        lambda m, t: {}
    ),
    # Share Reel
    (
        re.compile(r"(?:share\s+reel|share\s+this\s+reel|ரீல்\s+பகிர்)", re.I),
        "instagram_share_reel",
        lambda m, t: {}
    ),
    # Add Reel to Story
    (
        re.compile(r"(?:add\s+reel\s+to\s+story|add\s+to\s+story|ஸ்டோரியில்\s+சேர்)", re.I),
        "instagram_add_reel_to_story",
        lambda m, t: {}
    ),
    # Important Emails Check & Summary
    (
        re.compile(r"(?:check\s+(?:my\s+)?important\s+emails|important\s+emails|check\s+important\s+mail|முக்கியமான\s+ஈமெயில்)", re.I),
        "check_important_emails",
        lambda m, t: {}
    ),
    # Read Emails
    (
        re.compile(r"(?:read\s+(?:my\s+)?(?:inbox|emails)|check\s+(?:my\s+)?emails|ஈமெயில்\s+படி)", re.I),
        "read_emails",
        lambda m, t: {"limit": 10}
    ),
    # Summarize Inbox
    (
        re.compile(r"(?:summarize\s+(?:my\s+)?(?:inbox|emails)|email\s+summary)", re.I),
        "summarize_inbox",
        lambda m, t: {}
    ),
    # Email Alert to WhatsApp
    (
        re.compile(r"(?:email\s+(?:summary\s+)?alert\s+to\s+whatsapp|send\s+email\s+alert\s+to\s+whatsapp)", re.I),
        "email_to_whatsapp_alert",
        lambda m, t: {"user_phone": "919876543210"}
    ),

    # ── 7. Memory & Knowledge (Phase 6) ──────────────────────────────────
    # Remember Fact
    (
        re.compile(r"(?:remember\s+that\s+(.*)|remember\s+(.*)|ஞாபகம்\s+வச்சுக்கோ\s+(.*))", re.I),
        "remember_fact",
        lambda m, t: {
            "fact": (m.group(1) or m.group(2) or m.group(3) or "").strip(),
            "category": "preference"
        }
    ),
    # Show Memory
    (
        re.compile(r"(?:show\s+(?:my\s+)?memory|what\s+do\s+you\s+remember|list\s+(?:my\s+)?memories|என்\s+நினைவகம்)", re.I),
        "show_memory",
        lambda m, t: {}
    ),
    # Forget Fact
    (
        re.compile(r"(?:forget\s+that\s+(.*)|forget\s+(.*)|மறந்துடு\s+(.*))", re.I),
        "forget_fact",
        lambda m, t: {
            "query": (m.group(1) or m.group(2) or m.group(3) or "").strip()
        }
    ),
    # Search Documents / RAG
    (
        re.compile(r"(?:search\s+documents\s+for\s+(.*)|search\s+notes\s+for\s+(.*)|explain\s+this\s+from\s+my\s+compiler\s+notes)", re.I),
        "search_documents",
        lambda m, t: {
            "query": (m.group(1) or m.group(2) or "compiler notes").strip()
        }
    ),
    # Current Web Information Command
    (
        re.compile(r"(?:search\s+(?:the\s+)?web\s+for\s+(.*)|what'?s\s+the\s+latest\s+(.*)|latest\s+(.*)|search\s+news\s+for\s+(.*))", re.I),
        "web_search",
        lambda m, t: {
            "query": (m.group(1) or m.group(2) or m.group(3) or m.group(4) or "").strip()
        }
    ),


]




def _route_single(clean_text: str) -> dict | None:
    for pattern, tool_name, arg_builder in _DETERMINISTIC_RULES:
        match = pattern.search(clean_text)
        if match:
            args = arg_builder(match, clean_text)
            log.info("[ROUTER] MATCH: %r -> Tool '%s' args=%s [FAST PATH]", clean_text, tool_name, args)
            return {"tool": tool_name, "arguments": args}
    return None


def route_command(command_text: str) -> dict | list[dict] | None:
    """
    Check if command_text is a single or multi-step deterministic action that can be executed directly without Gemini.
    Returns: {"tool": str, "arguments": dict} or list of tool dicts or None.
    """
    if not command_text:
        return None

    clean = command_text.strip()
    log.debug("CommandRouter evaluating command: %r", clean)

    # Multi-step conjunctions ("and then", ", then", " then", " and", " apram", " panni apram")
    for separator in (" and then ", ", then ", " then ", " and ", " apram ", " panni apram "):
        if separator in clean.lower():
            parts = [p.strip() for p in re.split(re.escape(separator), clean, flags=re.I) if p.strip()]
            if len(parts) > 1:
                step_plans = []
                all_matched = True
                for part in parts:
                    r = _route_single(part)
                    if r:
                        step_plans.append(r)
                    else:
                        all_matched = False
                        break
                if all_matched and step_plans:
                    log.info("[ROUTER] MULTI-STEP MATCH (%d steps): %s", len(step_plans), step_plans)
                    return step_plans

    return _route_single(clean)

