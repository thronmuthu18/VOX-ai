"""
MuthuAI — tools/setup_registry.py
Registers all tools into the ToolRegistry.
Import and call setup_tools() at startup.
"""

from tools.registry import ToolRegistry
from tools.base import ToolDefinition, PermissionLevel
import tools.system_tools as sys_t
import tools.application_tools as app_t
import tools.file_tools as file_t
import tools.browser_tools as browser_t
import tools.office_tools as office_t
import tools.media_tools as media_t
import tools.desktop_tools as desk_t
import tools.code_tools as code_t
import tools.communication_tools as comm_t
from utils.logger import get_logger

log = get_logger(__name__)


# ── Lazy tool wrappers (avoid circular import / forward-reference) ─────────────

def _web_search_tool(query: str, max_results: int = 5) -> dict:
    from retrieval.web_search import WebSearcher
    from utils.helpers import ok, fail
    try:
        results = WebSearcher().search(query, max_results=max_results)
        return ok(f"Found {len(results)} web results.", data={"results": results})
    except Exception as exc:
        return fail(str(exc))


def _search_documents_tool(query: str, top_k: int = 5) -> dict:
    from rag.retrieval.retriever import RAGRetriever
    from utils.helpers import ok, fail
    try:
        retriever = RAGRetriever()
        chunks = retriever.retrieve(query, top_k=top_k)
        if not chunks:
            return fail(f"No relevant content found in your indexed documents for '{query}'.")
        return ok(f"Found {len(chunks)} document chunks.", data={"chunks": chunks})
    except Exception as exc:
        return fail(str(exc))


def _remember_fact_tool(fact: str = "", category: str = "preference", **kwargs) -> dict:
    from memory.personal_memory import PersonalMemoryStore
    from utils.helpers import ok, fail
    if not fact:
        return fail("Please specify what you want me to remember.")
    store = PersonalMemoryStore()
    record = store.remember(content=fact, category=category)
    if record:
        return ok(f"Saved to long-term memory: '{fact}'.", data={"record": record})
    return fail("Could not save memory (contains sensitive secrets or credentials).")


def _forget_fact_tool(query: str = "", **kwargs) -> dict:
    from memory.personal_memory import PersonalMemoryStore
    from utils.helpers import ok, fail
    if not query:
        return fail("Please specify which memory to forget.")
    store = PersonalMemoryStore()
    deleted = store.forget(query)
    if deleted:
        return ok(f"Removed from long-term memory: {', '.join(deleted)}.", data={"deleted": deleted})
    return fail(f"No matching memory found for '{query}'.")


def _show_memory_tool(**kwargs) -> dict:
    from memory.personal_memory import PersonalMemoryStore
    from utils.helpers import ok
    store = PersonalMemoryStore()
    memories = store.get_all()
    if not memories:
        return ok("No long-term memories saved yet.", data={"memories": []})
    text = "\n".join([f"- [{m.get('category', 'fact')}] {m['content']}" for m in memories])
    return ok(f"Saved memories:\n{text}", data={"memories": memories})


def _index_document_tool(file_path: str = "", path: str = "", **kwargs) -> dict:
    from rag.pipeline import RAGPipeline
    from utils.helpers import ok, fail
    target = file_path or path or "data/documents"
    pipeline = RAGPipeline()
    return pipeline.ingest(target)


def setup_tools(registry: ToolRegistry) -> None:
    """Register all MuthuAI tools into the provided registry."""

    tools_to_register: list[ToolDefinition] = [

        # ── System ──────────────────────────────────────────
        ToolDefinition(
            name="volume_up",
            description="Increase the system volume by a given step (default 5%).",
            parameters={"type": "object", "properties": {"step": {"type": "integer", "default": 5}}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.volume_up,
            aliases=["increase volume", "louder"],
        ),
        ToolDefinition(
            name="volume_down",
            description="Decrease the system volume by a given step (default 5%).",
            parameters={"type": "object", "properties": {"step": {"type": "integer", "default": 5}}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.volume_down,
            aliases=["decrease volume", "quieter"],
        ),
        ToolDefinition(
            name="mute_volume",
            description="Mute the system audio.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.mute_volume,
        ),
        ToolDefinition(
            name="unmute_volume",
            description="Unmute the system audio.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.unmute_volume,
        ),
        ToolDefinition(
            name="set_volume",
            description="Set system master volume to an exact percentage (0-100).",
            parameters={
                "type": "object",
                "properties": {"level": {"type": "integer", "default": 50, "description": "Volume percentage (0-100)."}},
                "required": ["level"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.set_volume,
        ),
        ToolDefinition(
            name="get_system_info",
            description="Get Windows system information (CPU, RAM, OS version, current time).",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.get_system_info,
        ),
        ToolDefinition(
            name="take_screenshot",
            description="Capture a screenshot of the entire screen and save to Desktop.",
            parameters={"type": "object", "properties": {"save_dir": {"type": "string", "default": "~\\Desktop"}}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.take_screenshot,
        ),
        ToolDefinition(
            name="stop_media",
            description="Stop currently playing media.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.stop_media,
        ),
        ToolDefinition(
            name="pause_media",
            description="Pause or resume currently playing media.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=sys_t.pause_media,
        ),

        # ── Applications ────────────────────────────────────
        ToolDefinition(
            name="open_application",
            description=(
                "Launch a Windows application by its friendly name. "
                "Examples: chrome, firefox, vscode, notepad, excel, word, powerpoint, "
                "cmd, powershell, calculator, control panel, task manager, vlc, spotify, zoom, teams, whatsapp."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Friendly application name."},
                    "app_name": {"type": "string", "description": "Friendly application name alias."}
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=app_t.open_application,
        ),
        ToolDefinition(
            name="open_control_panel",
            description="Open Windows Control Panel.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=app_t.open_control_panel,
        ),
        ToolDefinition(
            name="open_settings",
            description="Open Windows Settings.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=app_t.open_settings,
        ),
        ToolDefinition(
            name="open_calculator",
            description="Open Windows Calculator.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=app_t.open_calculator,
        ),
        ToolDefinition(
            name="open_notepad",
            description="Open Windows Notepad.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=app_t.open_notepad,
        ),
        ToolDefinition(
            name="open_command_prompt",
            description="Open Windows Command Prompt (CMD).",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=app_t.open_command_prompt,
        ),
        ToolDefinition(
            name="open_camera",
            description="Open Windows Camera.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=app_t.open_camera,
        ),
        ToolDefinition(
            name="open_task_manager",
            description="Open Windows Task Manager.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=app_t.open_task_manager,
        ),

        # ── Files & Folders ─────────────────────────────────
        ToolDefinition(
            name="open_folder",
            description=(
                "Open a folder in Windows Explorer. Understands shortcuts like "
                "'D drive', 'desktop', 'downloads', 'documents', 'D:\\\\my project'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Folder path or natural-language shortcut."},
                    "folder_name": {"type": "string", "description": "Folder path or natural-language shortcut alias."}
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=file_t.open_folder,
        ),
        ToolDefinition(
            name="open_file",
            description="Open a file with its default Windows application.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=file_t.open_file,
        ),
        ToolDefinition(
            name="read_file",
            description="Read and return the text content of a file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_chars": {"type": "integer", "default": 5000},
                },
                "required": ["path"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=file_t.read_file,
        ),
        ToolDefinition(
            name="list_files",
            description="List files and folders in a directory.",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string"},
                    "pattern": {"type": "string", "default": "*"},
                },
                "required": ["directory"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=file_t.list_files,
        ),
        ToolDefinition(
            name="create_folder",
            description="Create a new folder at the given path.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=file_t.create_folder,
        ),
        ToolDefinition(
            name="create_file",
            description="Create or write a text or code file at the given path with content and verify creation.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Target file path."},
                    "content": {"type": "string", "default": "", "description": "File content."},
                    "overwrite": {"type": "boolean", "default": True},
                },
                "required": ["path"],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=file_t.create_file,
            aliases=["write_file", "create_text_file"],
        ),
        ToolDefinition(
            name="create_csv",
            description="Create a CSV file with headers and rows at the specified path and verify creation.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Target CSV file path."},
                    "headers": {"type": "array", "items": {"type": "string"}, "default": []},
                    "rows": {"type": "array", "default": []},
                },
                "required": ["path"],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=file_t.create_csv,
        ),
        ToolDefinition(
            name="download_file",
            description="Download a file from a URL to the permanent workspace (M:\\Downloads\\) and verify physical existence.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL of the file to download."},
                    "filename": {"type": "string", "default": "", "description": "Optional destination filename."},
                    "destination": {"type": "string", "default": "", "description": "Optional custom destination path."},
                },
                "required": ["url"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=file_t.download_file,
        ),
        ToolDefinition(
            name="save_image",
            description="Save or export an image to M:\\Generated\\Images\\ and verify physical existence.",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "default": "", "description": "Image filename (.png)."},
                    "prompt": {"type": "string", "default": "", "description": "Description/prompt for image."},
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=file_t.save_image,
        ),
        ToolDefinition(
            name="delete_file",
            description="DANGEROUS: Delete a file permanently. Requires user confirmation.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            permission_level=PermissionLevel.DANGEROUS,
            handler=file_t.delete_file,
        ),
        ToolDefinition(
            name="search_files",
            description="Search for files in a directory matching a query in filename or content.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "directory": {"type": "string", "default": "", "description": "Search root directory."},
                    "pattern": {"type": "string", "default": "*"},
                },
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=file_t.search_files,
        ),
        ToolDefinition(
            name="edit_file",
            description="Safely edit a file by replacing old_text with new_text (reads first, validates syntax).",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path."},
                    "old_text": {"type": "string", "description": "Existing text to replace."},
                    "new_text": {"type": "string", "description": "New replacement text."},
                    "validate_syntax": {"type": "boolean", "default": True},
                },
                "required": ["path", "old_text", "new_text"],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=file_t.edit_file,
        ),
        ToolDefinition(
            name="open_vscode",
            description="Open Visual Studio Code with a project directory or specific file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "", "description": "Project directory or file path."},
                    "file_name": {"type": "string", "default": "", "description": "Specific file to open in VS Code."},
                    "target": {"type": "string", "default": "", "description": "Target project or file alias."},
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=code_t.open_vscode,
            aliases=["code", "launch_vscode", "vscode"],
        ),
        ToolDefinition(
            name="edit_code",
            description="Safely edit a source code file (reads target, validates syntax, verifies save).",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "default": ""},
                    "file_name": {"type": "string", "default": ""},
                    "old_code": {"type": "string", "description": "Target snippet to replace."},
                    "new_code": {"type": "string", "description": "New replacement snippet."},
                    "validate_syntax": {"type": "boolean", "default": True},
                },
                "required": ["old_code", "new_code"],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=code_t.edit_code,
            aliases=["edit_code_file"],
        ),
        ToolDefinition(
            name="delete_folder",
            description="DANGEROUS: Delete a folder and all its contents. Requires user confirmation.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            permission_level=PermissionLevel.DANGEROUS,
            handler=file_t.delete_folder,
        ),

        # ── Browser (Phase 3 Automation) ────────────────────
        ToolDefinition(
            name="open_browser",
            description="Launch or focus the controlled web browser (Chrome or Edge).",
            parameters={
                "type": "object",
                "properties": {
                    "browser_type": {"type": "string", "default": "chrome", "description": "Browser to launch ('chrome' or 'edge')."},
                    "headless": {"type": "boolean", "default": False, "description": "Run in background if true."},
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.open_browser,
        ),
        ToolDefinition(
            name="open_website",
            description="Open a website URL or shortcut (google, youtube, instagram, github, flipkart, etc.) in the browser.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL or site shortcut name (e.g. 'google', 'youtube', 'https://example.com')."},
                    "website_name": {"type": "string", "description": "Optional friendly site name."},
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.open_website,
        ),
        ToolDefinition(
            name="search_google",
            description="Search Google for a query and open results in the browser.",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search term to look up on Google."}},
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.search_google,
        ),
        ToolDefinition(
            name="search_youtube",
            description="Search YouTube for a query and open the results page.",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Topic, video, or lecture to search on YouTube."}},
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.search_youtube,
        ),
        ToolDefinition(
            name="play_youtube",
            description="Search YouTube for a query, click the first video, and start playback.",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Video topic, lecture, or song to play on YouTube."}},
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.play_youtube,
        ),
        ToolDefinition(
            name="click",
            description="Click a link, button, search result, or DOM element on the active webpage.",
            parameters={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Selector, button text, link text, or 'first result'."},
                    "selector": {"type": "string", "description": "Optional CSS selector."},
                    "text": {"type": "string", "description": "Optional text to click."},
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.click,
            aliases=["browser_click"],
        ),
        ToolDefinition(
            name="browser_click",
            description="Click an element on the webpage by text or selector.",
            parameters={
                "type": "object",
                "properties": {"target": {"type": "string"}},
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.browser_click,
        ),
        ToolDefinition(
            name="type",
            description="Type text into a search box, form field, or active input on the webpage.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type."},
                    "selector": {"type": "string", "description": "Optional input field selector."},
                    "press_enter": {"type": "boolean", "default": False, "description": "Press Enter key after typing."},
                },
                "required": ["text"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.type_text,
            aliases=["browser_type"],
        ),
        ToolDefinition(
            name="browser_type",
            description="Type text into an input field on the open webpage.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "selector": {"type": "string", "default": ""},
                    "press_enter": {"type": "boolean", "default": False},
                },
                "required": ["text"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.browser_type,
        ),
        ToolDefinition(
            name="press_key",
            description="Press a keyboard key on the active webpage (e.g. 'Enter', 'Tab', 'Escape', 'ArrowDown').",
            parameters={
                "type": "object",
                "properties": {"key": {"type": "string", "default": "Enter"}},
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.press_key,
        ),
        ToolDefinition(
            name="scroll",
            description="Scroll the active browser window up or down.",
            parameters={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "default": "down", "description": "'down' or 'up'"},
                    "amount": {"type": "integer", "default": 500, "description": "Pixels to scroll."},
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.scroll,
            aliases=["browser_scroll"],
        ),
        ToolDefinition(
            name="browser_scroll",
            description="Scroll the browser window up or down.",
            parameters={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "default": "down"},
                    "amount": {"type": "integer", "default": 500},
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.browser_scroll,
        ),
        ToolDefinition(
            name="back",
            description="Navigate back in browser history.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.back,
        ),
        ToolDefinition(
            name="forward",
            description="Navigate forward in browser history.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.forward,
        ),
        ToolDefinition(
            name="refresh",
            description="Reload the active webpage.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.refresh,
        ),
        ToolDefinition(
            name="find_text",
            description="Search for specific text or keyword on the active webpage.",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Text to find on the page."}},
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.find_text,
        ),
        ToolDefinition(
            name="get_page_state",
            description="Get the title, URL, text summary, and input elements of the active webpage.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.get_page_state,
            aliases=["browser_read"],
        ),
        ToolDefinition(
            name="browser_read",
            description="Read text content from the active webpage.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.browser_read,
        ),
        ToolDefinition(
            name="search_flipkart",
            description="Search Flipkart for a product.",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.search_flipkart,
        ),
        ToolDefinition(
            name="web_search",
            description=(
                "Search the web for current, live, or recent information. "
                "Use this for news, prices, weather, live scores, or any question that requires today's data."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query keywords."},
                    "max_results": {"type": "integer", "default": 5, "description": "Maximum number of results to fetch."},
                },
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=browser_t.web_search,
            aliases=["search_web", "google_search_info", "search_news"],
        ),

        # ── Documents (RAG) ──────────────────────────────────
        ToolDefinition(
            name="search_documents",
            description=(
                "Search the user's local documents (PDFs, Word files, notes) for relevant content. "
                "Use for questions about study material, personal notes, or uploaded files."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=_search_documents_tool,
        ),

        # ── Office ───────────────────────────────────────────
        ToolDefinition(
            name="create_excel",
            description=(
                "Create an Excel spreadsheet (.xlsx) with specified headers and optional row data. "
                "Example: create_excel(filename='Students', headers=['Name','Age','Mark'], rows=[...])"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "default": "MuthuAI_Spreadsheet"},
                    "headers": {"type": "array", "items": {"type": "string"}, "default": []},
                    "rows": {"type": "array", "default": []},
                    "save_dir": {"type": "string", "default": ""},
                    "open_after": {"type": "boolean", "default": True},
                },
                "required": [],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=office_t.create_excel,
        ),
        ToolDefinition(
            name="create_word",
            description="Create a Word document (.docx) with a title and content.",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "default": "MuthuAI_Document"},
                    "title": {"type": "string", "default": ""},
                    "content": {"type": "string", "default": ""},
                    "paragraphs": {"type": "array", "default": []},
                    "save_dir": {"type": "string", "default": ""},
                    "open_after": {"type": "boolean", "default": True},
                },
                "required": [],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=office_t.create_word,
        ),
        ToolDefinition(
            name="create_powerpoint",
            description="Create a PowerPoint presentation (.pptx) with a title and multiple slides.",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "default": "MuthuAI_Presentation"},
                    "title": {"type": "string", "default": "Presentation"},
                    "slides": {"type": "array", "default": []},
                    "topic": {"type": "string", "default": ""},
                    "save_dir": {"type": "string", "default": ""},
                    "open_after": {"type": "boolean", "default": False},
                },
                "required": [],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=office_t.create_powerpoint,
        ),
        ToolDefinition(
            name="create_pdf",
            description="Create a styled PDF document (.pdf) with title, sections, and paragraphs.",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "default": "report.pdf"},
                    "file_name": {"type": "string", "default": ""},
                    "title": {"type": "string", "default": "PDF Document"},
                    "paragraphs": {"type": "array", "default": []},
                    "content": {"type": "string", "default": ""},
                    "headings": {"type": "array", "default": []},
                    "save_dir": {"type": "string", "default": ""},
                    "open_after": {"type": "boolean", "default": False},
                },
                "required": [],
            },
            permission_level=PermissionLevel.MODERATE,
            handler=office_t.create_pdf,
        ),
        ToolDefinition(
            name="explain_and_create_pdf",
            description="Explain a topic using AI knowledge and automatically generate a verified PDF document.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Subject or topic to explain and summarize into PDF."},
                    "query": {"type": "string", "default": ""},
                    "filename": {"type": "string", "default": ""},
                    "save_dir": {"type": "string", "default": ""},
                },
                "required": ["topic"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=office_t.explain_and_create_pdf,
        ),
        ToolDefinition(
            name="convert_word_to_pdf",
            description="Convert a Word document (.docx) to a PDF document (.pdf) saved in M:\\Generated\\PDF\\.",
            parameters={
                "type": "object",
                "properties": {
                    "source_path": {"type": "string", "description": "Path or filename of source Word document."},
                    "target_path": {"type": "string", "default": "", "description": "Optional destination PDF path."},
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=office_t.convert_word_to_pdf,
            aliases=["convert_document", "docx_to_pdf", "word_to_pdf"],
        ),

        # ── Media ────────────────────────────────────────────
        ToolDefinition(
            name="play_music",
            description="Play music by searching YouTube or Spotify.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "source": {"type": "string", "default": "youtube"},
                },
                "required": ["query"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=media_t.play_music,
        ),
        ToolDefinition(
            name="set_brightness",
            description="Set monitor brightness level (0–100).",
            parameters={
                "type": "object",
                "properties": {"level": {"type": "integer", "default": 70}},
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=media_t.set_brightness,
        ),

        # ── Desktop UI Control Tools (Phase 9C) ───────────────
        ToolDefinition(
            name="desktop_window_control",
            description="Control window state (activate, minimize, maximize, restore, close).",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["activate", "minimize", "maximize", "restore", "close"]},
                    "application_name": {"type": "string"},
                    "title": {"type": "string"}
                },
                "required": []
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.desktop_window_control,
        ),
        ToolDefinition(
            name="desktop_ui_type",
            description="Type text out on the active desktop application window.",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.desktop_ui_type,
        ),
        ToolDefinition(
            name="desktop_ui_click",
            description="Click a UI element by name on the active window using UI Automation or fallback.",
            parameters={
                "type": "object",
                "properties": {"element_name": {"type": "string"}},
                "required": ["element_name"]
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.desktop_ui_click,
        ),
        ToolDefinition(
            name="operate_excel_ui",
            description="Real Excel UI operation: creates table with columns & data, saves .xlsx, and verifies file size.",
            parameters={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "data_rows": {"type": "array"},
                    "file_name": {"type": "string", "default": "students.xlsx"}
                },
                "required": []
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.operate_excel_ui,
        ),
        ToolDefinition(
            name="operate_word_ui",
            description="Real Word UI operation: inserts report document text, saves .docx, and verifies file size.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "paragraphs": {"type": "array", "items": {"type": "string"}},
                    "file_name": {"type": "string", "default": "machine_learning_report.docx"}
                },
                "required": []
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.operate_word_ui,
        ),
        ToolDefinition(
            name="operate_notepad_ui",
            description="Real Notepad UI operation: opens Notepad, focuses window, and types text.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "save_file_name": {"type": "string"}
                },
                "required": []
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.operate_notepad_ui,
        ),
        ToolDefinition(
            name="operate_calculator_ui",
            description="Real Calculator UI operation: calculates mathematical expression and verifies result.",
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"]
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.operate_calculator_ui,
        ),
        ToolDefinition(
            name="desktop_press_key",
            description="Press a keyboard key (e.g. enter, tab, escape, f5).",
            parameters={
                "type": "object",
                "properties": {"key": {"type": "string", "default": "enter"}},
                "required": ["key"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.desktop_press_key,
        ),
        ToolDefinition(
            name="desktop_hotkey",
            description="Trigger a keyboard hotkey combination (e.g. 'ctrl+s', 'alt+tab', 'ctrl+c').",
            parameters={
                "type": "object",
                "properties": {"hotkey_str": {"type": "string", "description": "Hotkey string (e.g. 'ctrl+s')"}},
                "required": ["hotkey_str"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.desktop_hotkey,
            aliases=["hotkey"],
        ),
        ToolDefinition(
            name="desktop_mouse_click",
            description="Click mouse at specified screen coordinates or current cursor location.",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {"type": "string", "default": "left"}
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.desktop_mouse_click,
        ),
        ToolDefinition(
            name="desktop_mouse_scroll",
            description="Scroll mouse wheel up or down by a given number of clicks.",
            parameters={
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer", "default": 3},
                    "direction": {"type": "string", "default": "down"}
                },
                "required": [],
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.desktop_mouse_scroll,
        ),
        ToolDefinition(
            name="desktop_move_mouse",
            description="Move mouse cursor to coordinates (x, y).",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate."},
                    "y": {"type": "integer", "description": "Y coordinate."}
                },
                "required": ["x", "y"],
            },
            permission_level=PermissionLevel.SAFE,
            handler=desk_t.desktop_move_mouse,
        ),

        # ── Communication Tools (Phase 5) ────────────────────────
        ToolDefinition(
            name="whatsapp_send_message",
            description="Send a WhatsApp text message to a phone number (e.g. '9876543210', '+919876543210').",
            parameters={
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string", "description": "Recipient phone number."},
                    "message": {"type": "string", "description": "Message text."}
                },
                "required": ["phone_number", "message"]
            },
            permission_level=PermissionLevel.DANGEROUS,
            handler=comm_t.whatsapp_send_message,
            aliases=["send_whatsapp_message", "whatsapp_message"],
        ),
        ToolDefinition(
            name="whatsapp_call",
            description="Initiate a WhatsApp voice or video call to a phone number.",
            parameters={
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string", "description": "Recipient phone number."}
                },
                "required": ["phone_number"]
            },
            permission_level=PermissionLevel.DANGEROUS,
            handler=comm_t.whatsapp_call,
            aliases=["call_whatsapp"],
        ),
        ToolDefinition(
            name="open_instagram",
            description="Open Instagram home in the browser.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.open_instagram,
            aliases=["instagram"],
        ),
        ToolDefinition(
            name="open_instagram_reels",
            description="Open Instagram Reels feed in the browser.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.open_instagram_reels,
            aliases=["instagram_reels", "open_reels"],
        ),
        ToolDefinition(
            name="instagram_scroll",
            description="Scroll Instagram feed or explore page up or down.",
            parameters={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "default": "down"},
                    "amount": {"type": "integer", "default": 500}
                },
                "required": []
            },
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.instagram_scroll,
        ),
        ToolDefinition(
            name="instagram_next_reel",
            description="Navigate to the next Instagram Reel in the feed.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.instagram_next_reel,
            aliases=["next_reel"],
        ),
        ToolDefinition(
            name="instagram_stop",
            description="Stop or pause current Instagram Reel video playback.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.instagram_stop,
            aliases=["stop_reel", "pause_reel"],
        ),
        ToolDefinition(
            name="instagram_share_reel",
            description="Share the current Instagram Reel with a contact or copy link.",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "default": ""}
                },
                "required": []
            },
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.instagram_share_reel,
            aliases=["share_reel"],
        ),
        ToolDefinition(
            name="instagram_add_reel_to_story",
            description="Add the current Instagram Reel to your Story.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.instagram_add_reel_to_story,
            aliases=["add_reel_to_story", "add_to_story"],
        ),
        ToolDefinition(
            name="read_emails",
            description="Read recent emails from authorized inbox.",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "unread_only": {"type": "boolean", "default": False}
                },
                "required": []
            },
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.read_emails,
            aliases=["check_emails", "get_emails"],
        ),
        ToolDefinition(
            name="check_important_emails",
            description="Filter, analyze, and summarize important emails (interviews, action items, job offers).",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.check_important_emails,
            aliases=["important_emails", "check_my_important_emails"],
        ),
        ToolDefinition(
            name="summarize_inbox",
            description="Produce a concise summary of your email inbox.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=comm_t.summarize_inbox,
        ),
        ToolDefinition(
            name="email_to_whatsapp_alert",
            description="Analyze important emails and send an alert hint to user's WhatsApp.",
            parameters={
                "type": "object",
                "properties": {
                    "user_phone": {"type": "string", "default": "919876543210"}
                },
                "required": []
            },
            permission_level=PermissionLevel.DANGEROUS,
            handler=comm_t.email_to_whatsapp_alert,
        ),

        # ── Memory & Knowledge Tools (Phase 6) ───────────────────
        ToolDefinition(
            name="remember_fact",
            description="Save a personal fact, preference, profile item, or goal to long-term memory.",
            parameters={
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The fact or preference to remember."},
                    "category": {"type": "string", "default": "preference"}
                },
                "required": ["fact"]
            },
            permission_level=PermissionLevel.SAFE,
            handler=_remember_fact_tool,
            aliases=["remember", "save_preference", "save_memory"],
        ),
        ToolDefinition(
            name="forget_fact",
            description="Delete a saved personal memory or preference from long-term memory.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Memory query or description to forget."}
                },
                "required": ["query"]
            },
            permission_level=PermissionLevel.SAFE,
            handler=_forget_fact_tool,
            aliases=["forget", "delete_memory"],
        ),
        ToolDefinition(
            name="show_memory",
            description="Show or list all saved long-term personal preferences and memories.",
            parameters={"type": "object", "properties": {}, "required": []},
            permission_level=PermissionLevel.SAFE,
            handler=_show_memory_tool,
            aliases=["list_memories", "get_memories"],
        ),
        ToolDefinition(
            name="index_document",
            description="Ingest, chunk, and embed a document into the RAG vector database.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to document file (PDF, Word, text)."}
                },
                "required": ["file_path"]
            },
            permission_level=PermissionLevel.SAFE,
            handler=_index_document_tool,
            aliases=["index_file", "ingest_document"],
        ),
        ToolDefinition(
            name="search_knowledge",
            description="Search indexed personal documents and notes for relevant information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."}
                },
                "required": ["query"]
            },
            permission_level=PermissionLevel.SAFE,
            handler=_search_documents_tool,
            aliases=["search_notes", "query_rag"],
        ),
    ]

    for tool in tools_to_register:
        registry.register(tool)

    # ── Modular Subsystem Tools (Windows, Office, Browser, Process, Input) ──
    from tools.windows.system import GetTimeTool, GetDateTool
    from tools.windows.process import ListProcessesTool, TerminateProcessTool
    from tools.windows.input import KeyboardTool, MouseTool
    from tools.browser.search_web import SearchWebTool
    from tools.browser.instagram_tools import InstagramReelsScrollTool
    from tools.office.file_tools import CreateDirectoryTool, CopyFileTool, MoveFileTool, RenameFileTool
    from tools.office.excel_tools import ReadExcelTool
    from copy import copy

    sw = SearchWebTool()
    sw_alias = copy(sw)
    sw_alias.name = "search_web"

    modular_tools = [
        GetTimeTool(),
        GetDateTool(),
        ListProcessesTool(),
        TerminateProcessTool(),
        KeyboardTool(),
        MouseTool(),
        sw,
        sw_alias,
        InstagramReelsScrollTool(),
        ReadExcelTool(),
        CreateDirectoryTool(),
        CopyFileTool(),
        MoveFileTool(),
        RenameFileTool(),
    ]
    for tool in modular_tools:
        registry.register(tool)

    log.info("Registered %d tools.", len(registry))

