# CHAMP — Complete Tool Inventory & Registry Catalog

**Tool Architecture**: Unified Registry (`tools.registry.ToolRegistry` + `tools.setup_registry.setup_tools`)  
**Total Registered Tools**: **96 Tools**  
**Permission Models**: `SAFE`, `MODERATE`, `DANGEROUS` (with mandatory confirmation prompts)  

---

## 1. System & Audio Tools (`tools/system_tools.py`, `tools/windows/system.py`)

| Tool Name | Purpose | Parameters | Risk / Permission | Execution Method | Verification |
|---|---|---|---|---|---|
| `volume_up` | Increase master audio volume | `step: int = 10` | `SAFE` | Windows Kernel `VK_VOLUME_UP` keybd_event | pycaw / return dict |
| `volume_down` | Decrease master audio volume | `step: int = 10` | `SAFE` | Windows Kernel `VK_VOLUME_DOWN` keybd_event | pycaw / return dict |
| `mute_volume` | Mute system master volume | none | `SAFE` | Windows Kernel `VK_VOLUME_MUTE` keybd_event | pycaw endpoint |
| `unmute_volume` | Unmute system master volume | none | `SAFE` | Windows Kernel `VK_VOLUME_MUTE` keybd_event | pycaw endpoint |
| `set_volume` | Set volume percentage | `level: int` | `SAFE` | pycaw endpoint scalar volume | pycaw endpoint |
| `take_screenshot` | Capture full display screenshot | `save_path: str` | `SAFE` | PyAutoGUI / PIL image grab | Disk file check |
| `get_system_info` | Read CPU/RAM/Battery metrics | none | `SAFE` | `psutil` system metrics | Return structured data |
| `stop_media` | Stop active multimedia | none | `SAFE` | `VK_MEDIA_STOP` event | Return status |
| `pause_media` | Play/pause active multimedia | none | `SAFE` | `VK_MEDIA_PLAY_PAUSE` event | Return status |

---

## 2. Windows Application Launcher Tools (`tools/application_tools.py`, `tools/windows/application.py`)

| Tool Name | Purpose | Parameters | Risk / Permission | Execution Method | Verification |
|---|---|---|---|---|---|
| `open_application` | Launch desktop applications | `name: str` | `SAFE` | Registry `App Paths` + Program Files + User AppData + `whatsapp:` protocol | Process verification (`psutil`) |
| `list_running_applications` | List active user windows | none | `SAFE` | `pywin32` EnumWindows | Non-empty window list |

---

## 3. Browser & Navigation Tools (`tools/browser_tools.py`, `browser/interaction.py`)

| Tool Name | Purpose | Parameters | Risk / Permission | Execution Method | Verification |
|---|---|---|---|---|---|
| `open_browser` | Launch Playwright Chrome/Edge | none | `SAFE` | `playwright.sync_api` | Browser context alive |
| `open_website` | Navigate to specific URL | `url: str` | `SAFE` | `page.goto(url)` | Page URL & Title check |
| `search_google` | Execute Google Search | `query: str` | `SAFE` | `page.goto("google.com/search?q=...")` | DOM search results loaded |
| `search_youtube` | Execute YouTube Search | `query: str` | `SAFE` | `page.goto("youtube.com/results?search_query=...")` | Video card elements present |
| `play_first_youtube_result`| Play first search video | `query: str` | `SAFE` | Click first `#contents ytd-video-renderer` | Video player element active |
| `click` / `browser_click` | Click DOM element | `selector: str` | `SAFE` | `page.locator(selector).click()` | Element state change |
| `type_text` / `browser_type`| Type into DOM input | `selector: str, text: str` | `SAFE` | `page.locator(selector).fill(text)` | Input value check |
| `press_key` | Send keyboard key to browser | `key: str` | `SAFE` | `page.keyboard.press(key)` | DOM focus state |
| `scroll` / `browser_scroll` | Scroll browser viewport | `direction: str, amount: int` | `SAFE` | `page.mouse.wheel(...)` | Viewport offset change |
| `back` / `forward` / `refresh` | History navigation | none | `SAFE` | `page.go_back()`, `page.reload()` | URL / ready state |
| `find_text` / `browser_read` | Read webpage content | `selector: str` | `SAFE` | `page.inner_text(...)` | Non-empty text |

---

## 4. Office & Document Automation Tools (`tools/office_tools.py`)

| Tool Name | Purpose | Parameters | Risk / Permission | Execution Method | Verification |
|---|---|---|---|---|---|
| `create_excel` | Generate formatted `.xlsx` | `file_name, headers, rows` | `MODERATE` | `openpyxl` with formulas & table styles | File exists on disk & `size > 0` |
| `create_word` | Generate formatted `.docx` | `file_name, title, content` | `MODERATE` | `python-docx` with headings & styles | File exists on disk & `size > 0` |
| `create_powerpoint` | Generate `.pptx` presentation | `file_name, title, topic` | `MODERATE` | `python-pptx` with 4-slide layout | File exists on disk & `size > 0` |
| `create_pdf` | Generate PDF document | `file_name, title, content` | `MODERATE` | `reportlab.platypus` SimpleDocTemplate | File exists on disk & `size > 0` |
| `explain_and_create_pdf` | LLM topic synthesis + PDF | `topic: str` | `MODERATE` | Gemini synthesis + ReportLab PDF | File exists on disk & `size > 0` |

---

## 5. File System Tools (`tools/file_tools.py`)

| Tool Name | Purpose | Parameters | Risk / Permission | Execution Method | Verification |
|---|---|---|---|---|---|
| `open_folder` | Open directory in Explorer | `path: str` | `SAFE` | `os.startfile(path)` | Directory presence check |
| `open_file` | Open file with default app | `path: str` | `SAFE` | `os.startfile(path)` | File presence check |
| `read_file` | Read text file contents | `path: str` | `SAFE` | `Path(path).read_text()` | Non-empty return string |
| `list_files` | List directory contents | `path: str` | `SAFE` | `os.listdir(path)` | File list returned |
| `create_folder` | Create new directory | `path: str` | `SAFE` | `Path(path).mkdir(parents=True)` | Directory exists on disk |
| `delete_file` | Delete file from disk | `path: str` | `DANGEROUS` | `Path(path).unlink()` (with confirmation) | File absent on disk |
| `delete_folder` | Delete directory from disk | `path: str` | `DANGEROUS` | `shutil.rmtree(path)` (with confirmation) | Directory absent on disk |
| `search_files` | Search files by pattern | `query, root` | `SAFE` | `Path(root).rglob(query)` | Matches returned |
| `edit_file` | Append or replace file text | `path, content, mode` | `MODERATE` | File write buffer | File updated on disk |

---

## 6. Communication Tools (`tools/communication_tools.py`, `communication/`)

| Tool Name | Purpose | Parameters | Risk / Permission | Execution Method | Verification |
|---|---|---|---|---|---|
| `whatsapp_send_message` | Send WhatsApp message | `phone_number, message` | `DANGEROUS` | Playwright WhatsApp Web / Protocol (Confirmation required) | QR check / Message element |
| `whatsapp_call` | Initiate WhatsApp call | `phone_number` | `DANGEROUS` | WhatsApp protocol launcher | Call interface active |
| `read_emails` | Read IMAP inbox messages | `limit, unread_only` | `SAFE` | `imaplib.IMAP4_SSL` | Structured email array |
| `check_important_emails`| Categorize & summarize inbox | none | `SAFE` | Email categorization engine | Summary string |
| `summarize_inbox` | Generate inbox overview | none | `SAFE` | Gemini inbox summarizer | Spoken summary |
| `open_instagram` | Open Instagram in browser | none | `SAFE` | Playwright `instagram.com` | Instagram loaded |
| `open_instagram_reels` | Navigate to Instagram Reels | none | `SAFE` | Playwright `instagram.com/reels` | Reels viewport active |
| `instagram_scroll` / `next_reel` | Next reel navigation | none | `SAFE` | Page keyboard `ArrowDown` | Video transition |

---

## 7. Desktop UI & Input Tools (`tools/desktop_tools.py`)

| Tool Name | Purpose | Parameters | Risk / Permission | Execution Method | Verification |
|---|---|---|---|---|---|
| `desktop_window_control` | Minimize/Maximize/Close window | `action, title` | `SAFE` | `pywin32` ShowWindow/CloseWindow | Window state change |
| `operate_notepad_ui` | Launch Notepad & type text | `text: str` | `SAFE` | `subprocess.Popen` + PyAutoGUI write | Window title check |
| `operate_calculator_ui` | Perform calculation via UI | `expression: str` | `SAFE` | `calc.exe` + PyAutoGUI sendkeys | Window title check |
| `desktop_press_key` | Send low-level key stroke | `key: str` | `SAFE` | PyAutoGUI `press` | Return status |
| `desktop_hotkey` | Send hotkey combo (e.g. ctrl+c)| `keys: list[str]` | `SAFE` | PyAutoGUI `hotkey` | Return status |
| `desktop_mouse_click` | Low-level coordinate click | `x, y, button` | `SAFE` | PyAutoGUI `click` | Return status |
| `desktop_mouse_scroll` | Low-level mouse scroll | `clicks: int` | `SAFE` | PyAutoGUI `scroll` | Return status |
| `desktop_move_mouse` | Low-level cursor movement | `x, y` | `SAFE` | PyAutoGUI `moveTo` | Return status |

---

## 8. Code & Developer Tools (`tools/code_tools.py`)

| Tool Name | Purpose | Parameters | Risk / Permission | Execution Method | Verification |
|---|---|---|---|---|---|
| `open_vscode` | Launch VS Code in directory | `path: str = "."` | `SAFE` | `Code.exe` launcher | Process check |
| `edit_code` | Apply code diff to source file | `file_path, old_code, new_code` | `MODERATE` | Target replacement | Disk verification |
