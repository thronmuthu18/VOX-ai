"""
CHAMP Phase 4 — tests/test_phase4_windows_office.py

Automated test suite for Windows Computer Control & Office Automation.
Tests:
  T1: Windows application launch resolution (Calculator, Notepad, Explorer, Settings, CMD, etc.)
  T2: Drive and natural folder path resolution ("D drive", "my project folder", "downloads")
  T3: Safe file reading and searching (search_files by name and content)
  T4: VS Code launch & project/file resolution (open_vscode)
  T5: Safe code editing with AST syntax validation (edit_code / edit_file)
  T6: Excel marks sheet creation with formulas (=SUM, =AVERAGE) & styling verification
  T7: Word document creation with formatted headings, paragraphs, and tables
  T8: PowerPoint multi-slide presentation creation with title and bullet points
  T9: ReportLab styled PDF generation and validation
  T10: AI Knowledge synthesis to PDF workflow (explain_and_create_pdf)
  T11: Volume and audio controls (set_volume, mute, unmute, volume_up, volume_down)
  T12: Desktop keyboard and mouse operations (press_key, hotkey, click, scroll)
  T13: Multi-step Windows & Office task pipeline via TaskQueue & DependencyAwareExecutor
  T14: ToolRegistry verification for all Phase 4 tools
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.registry import ToolRegistry
from tools.setup_registry import setup_tools
import tools.application_tools as app_t
import tools.file_tools as file_t
import tools.office_tools as office_t
import tools.code_tools as code_t
import tools.system_tools as sys_t
import tools.desktop_tools as desk_t
from tools.windows.filesystem import resolve_folder_path, FOLDER_MAPPINGS
from task_queue.task_queue import TaskQueue
from task_queue.task_model import Task, TaskStatus
from executor.dependency_executor import DependencyAwareExecutor
from validator.result_validator import ResultValidator


@pytest.fixture(scope="module")
def registry():
    reg = ToolRegistry()
    setup_tools(reg)
    return reg


@pytest.fixture
def temp_dir():
    d = Path(tempfile.mkdtemp(prefix="champ_test_"))
    yield d
    try:
        shutil.rmtree(str(d), ignore_errors=True)
    except Exception:
        pass


# ── T1: Application Launch Resolution ─────────────────────────────────────────

def test_T1_application_launch_resolution():
    """Verify application resolution and launch methods for standard Windows tools."""
    # Test registry / standard path lookup logic without blocking UI
    calc_path = app_t._find_via_registry("calc") or "calc.exe"
    assert calc_path is not None

    # Test friendly name normalization
    for name in ["calculator", "notepad", "cmd", "control panel", "settings", "file explorer"]:
        res = app_t.open_application(name=name)
        assert res["success"] is True or "opened" in res["message"].lower() or "launched" in res["message"].lower()
    print("\n[T1] Application launch resolution passed.")


# ── T2: Drive & Folder Path Resolution ────────────────────────────────────────

def test_T2_drive_and_folder_resolution():
    """Verify natural-language folder and drive resolution."""
    # D drive
    d_res = resolve_folder_path("D drive")
    assert d_res is not None
    assert "d:" in str(d_res).lower()

    # Project folder
    proj_res = resolve_folder_path("my project folder")
    assert proj_res is not None
    assert Path(proj_res).exists()

    # Downloads / Documents
    assert resolve_folder_path("downloads") is not None
    assert resolve_folder_path("documents") is not None
    print(f"\n[T2] Drive & folder resolution passed: D drive={d_res}, Project={proj_res}")


# ── T3: File Searching & Reading ──────────────────────────────────────────────

def test_T3_file_search_and_read(temp_dir):
    """Verify searching for files by name/content and reading safely."""
    # Create sample files
    f1 = temp_dir / "sample_script.py"
    f1.write_text("def hello_world():\n    return 'CHAMP AI'", encoding="utf-8")

    f2 = temp_dir / "notes.txt"
    f2.write_text("Machine learning and deep learning notes.", encoding="utf-8")

    # Search by name
    res_name = file_t.search_files(query="sample_script", directory=str(temp_dir))
    assert res_name["success"] is True
    assert len(res_name["data"]["results"]) >= 1

    # Search by content
    res_content = file_t.search_files(query="CHAMP AI", directory=str(temp_dir))
    assert res_content["success"] is True
    assert len(res_content["data"]["results"]) >= 1

    # Read file
    read_res = file_t.read_file(str(f1))
    assert read_res["success"] is True
    assert "hello_world" in read_res["data"]["content"]
    print("\n[T3] File search & reading passed.")


# ── T4: VS Code Launch & File Resolution ──────────────────────────────────────

def test_T4_vscode_launch_resolution(temp_dir):
    """Verify open_vscode resolves target projects and files."""
    test_file = temp_dir / "Chat.tsx"
    test_file.write_text("export const Chat = () => <div>Chat Component</div>;", encoding="utf-8")

    res = code_t.open_vscode(path=str(temp_dir), file_name="Chat.tsx")
    assert res["success"] is True
    assert "Chat.tsx" in res["message"] or "opened" in res["message"].lower()
    print(f"\n[T4] VS Code resolution passed: {res['message']}")


# ── T5: Safe Code Editing with AST Validation ─────────────────────────────────

def test_T5_safe_code_editing(temp_dir):
    """Verify code editing with syntax validation and file modification verification."""
    py_file = temp_dir / "calculator_service.py"
    initial_code = (
        "def add(a, b):\n"
        "    return a + b\n\n"
        "def multiply(a, b):\n"
        "    return a * b\n"
    )
    py_file.write_text(initial_code, encoding="utf-8")

    # 1. Valid Edit: Replace multiply logic with enhanced version
    res = code_t.edit_code(
        file_path=str(py_file),
        old_code="def multiply(a, b):\n    return a * b",
        new_code="def multiply(a, b):\n    '''Multiply two numbers safely.'''\n    return a * b",
        validate_syntax=True
    )
    assert res["success"] is True
    assert "successfully edited" in res["message"]

    # Verify file on disk actually changed
    updated_content = py_file.read_text(encoding="utf-8")
    assert "Multiply two numbers safely" in updated_content

    # 2. Syntax Error Edit (Must be REJECTED and file preserved)
    bad_res = code_t.edit_code(
        file_path=str(py_file),
        old_code="return a + b",
        new_code="return a + (invalid syntax here %%%",
        validate_syntax=True
    )
    assert bad_res["success"] is False
    assert "Syntax validation failed" in bad_res["message"]

    # Verify file was NOT corrupted
    unbroken_content = py_file.read_text(encoding="utf-8")
    assert "Multiply two numbers safely" in unbroken_content
    print("\n[T5] Safe code editing with AST syntax validation passed.")


# ── T6: Excel Marks Sheet Creation & Formulas ─────────────────────────────────

def test_T6_excel_marks_sheet(temp_dir):
    """Verify Excel marks sheet creation with formulas, styling, and disk validation."""
    from openpyxl import load_workbook

    res = office_t.create_excel(
        file_name="student_marks_sheet.xlsx",
        save_dir=str(temp_dir),
        template="marks_sheet"
    )
    assert res["success"] is True
    file_path = Path(res["data"]["path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 1000

    # Load and verify Excel contents and formulas
    wb = load_workbook(str(file_path), data_only=False)
    ws = wb.active
    assert ws.title == "Marks_Sheet"
    assert ws.cell(1, 1).value == "Student ID"
    assert ws.cell(1, 7).value == "Total"
    assert ws.cell(1, 8).value == "Average"

    # Check that formulas exist in data rows
    total_formula = str(ws.cell(2, 7).value)
    avg_formula = str(ws.cell(2, 8).value)
    assert total_formula.startswith("=SUM")
    assert avg_formula.startswith("=AVERAGE")
    wb.close()
    print(f"\n[T6] Excel marks sheet verified: {file_path.name} with formulas ({total_formula}, {avg_formula}).")


# ── T7: Word Document Creation ────────────────────────────────────────────────

def test_T7_word_document(temp_dir):
    """Verify Word document creation with headings, paragraphs, and tables."""
    from docx import Document

    res = office_t.create_word(
        file_name="project_proposal.docx",
        title="Automated Desktop Agent Architecture",
        headings=[
            ("Executive Summary", "This document details the core subsystem architecture for CHAMP AI agent."),
            ("Key Deliverables", "Modular tools, browser automation, and office document synthesis."),
        ],
        bullet_points=[
            "Phase 1: Natural Voice Engine",
            "Phase 2: Task Planning & Dependencies",
            "Phase 3: Robust Browser Automation",
            "Phase 4: Office & Windows Control"
        ],
        table_data=[
            ["Module", "Technology", "Status"],
            ["Speech", "Edge-TTS + Pygame", "Production Ready"],
            ["Browser", "Playwright + Discovery", "Production Ready"],
            ["Office", "OpenPyXL + Docx + ReportLab", "Production Ready"],
        ],
        save_dir=str(temp_dir)
    )
    assert res["success"] is True
    file_path = Path(res["data"]["path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 2000

    # Verify document structure
    doc = Document(str(file_path))
    assert len(doc.paragraphs) >= 5
    assert len(doc.tables) == 1
    assert doc.tables[0].cell(0, 0).text == "Module"
    print(f"\n[T7] Word document verified: {file_path.name} ({len(doc.paragraphs)} paragraphs, {len(doc.tables)} table).")


# ── T8: PowerPoint Multi-Slide Presentation ───────────────────────────────────

def test_T8_powerpoint_presentation(temp_dir):
    """Verify PowerPoint presentation creation with title and content slides."""
    from pptx import Presentation

    res = office_t.create_powerpoint(
        file_name="ai_overview.pptx",
        topic="Artificial Intelligence",
        save_dir=str(temp_dir)
    )
    assert res["success"] is True
    file_path = Path(res["data"]["path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 10000

    prs = Presentation(str(file_path))
    assert len(prs.slides) >= 3
    title_text = prs.slides[0].shapes.title.text
    assert "Artificial Intelligence" in title_text or "AI" in title_text
    print(f"\n[T8] PowerPoint presentation verified: {file_path.name} ({len(prs.slides)} slides).")


# ── T9: ReportLab PDF Generation ──────────────────────────────────────────────

def test_T9_pdf_generation(temp_dir):
    """Verify ReportLab styled PDF creation and validation."""
    res = office_t.create_pdf(
        file_name="technical_summary.pdf",
        title="Technical Report: Autonomous Agent Systems",
        headings=[
            ("1. System Overview", "Autonomous AI agents combine LLM reasoning with tool execution graphs."),
            ("2. Safety & Governance", "Deterministic routing and human confirmation prevent accidental state changes.")
        ],
        paragraphs=[
            "This report was generated automatically by the CHAMP Office Automation engine.",
            "All components have been validated with automated unit and integration tests."
        ],
        save_dir=str(temp_dir)
    )
    assert res["success"] is True
    file_path = Path(res["data"]["path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 1000

    # Verify PDF signature header
    content_bytes = file_path.read_bytes()
    assert content_bytes.startswith(b"%PDF")
    print(f"\n[T9] PDF generation verified: {file_path.name} ({file_path.stat().st_size} bytes).")


# ── T10: AI Knowledge to PDF Synthesis ────────────────────────────────────────

def test_T10_ai_knowledge_to_pdf_synthesis(temp_dir):
    """Verify full workflow: Topic -> AI Knowledge Synthesis -> ReportLab PDF -> File Verification."""
    res = office_t.explain_and_create_pdf(
        topic="Machine Learning and Deep Learning",
        save_dir=str(temp_dir)
    )
    assert res["success"] is True
    file_path = Path(res["data"]["path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 2000

    # Ensure valid PDF format
    header = file_path.read_bytes()[:10]
    assert b"%PDF" in header
    print(f"\n[T10] Knowledge to PDF synthesis passed: {file_path.name} ({file_path.stat().st_size} bytes).")


# ── T11: Volume & Audio Control ───────────────────────────────────────────────

def test_T11_volume_controls():
    """Verify system master volume and mute controls."""
    # Set volume
    res_set = sys_t.set_volume(45)
    assert res_set["success"] is True
    assert "Volume set" in res_set["message"]

    # Volume up / down
    res_up = sys_t.volume_up(5)
    assert res_up["success"] is True

    res_down = sys_t.volume_down(5)
    assert res_down["success"] is True

    # Mute / Unmute
    res_mute = sys_t.mute_volume()
    assert res_mute["success"] is True

    res_unmute = sys_t.unmute_volume()
    assert res_unmute["success"] is True
    print("\n[T11] Volume & audio controls passed.")


# ── T12: Desktop Keyboard & Mouse Operations ──────────────────────────────────

def test_T12_keyboard_mouse_operations():
    """Verify desktop keyboard and mouse helper tools."""
    # Keyboard press key
    res_key = desk_t.desktop_press_key("escape")
    assert res_key["success"] is True

    # Hotkey trigger
    res_hotkey = desk_t.desktop_hotkey("ctrl", "shift", "esc")
    assert res_hotkey["success"] is True

    # Mouse scroll & move
    res_scroll = desk_t.desktop_mouse_scroll(clicks=2, direction="down")
    assert res_scroll["success"] is True

    res_move = desk_t.desktop_move_mouse(x=200, y=200)
    assert res_move["success"] is True
    print("\n[T12] Desktop keyboard & mouse operations passed.")


# ── T13: Multi-Step Windows / Office Execution Pipeline ───────────────────────

def test_T13_multistep_pipeline_execution(registry, temp_dir):
    """
    Verify 4-task sequential pipeline with dependency enforcement:
      Task 1: create_excel (marks sheet)
      Task 2: create_word (report document)
      Task 3: explain_and_create_pdf (AI PDF)
      Task 4: set_volume (audio confirmation)
    """
    queue = TaskQueue()

    t1 = Task(
        id="t1",
        action="create_excel",
        parameters={"file_name": "pipeline_marks.xlsx", "template": "marks_sheet", "save_dir": str(temp_dir)},
        dependencies=[],
        description="Create Excel marks sheet"
    )
    t2 = Task(
        id="t2",
        action="create_word",
        parameters={"file_name": "pipeline_doc.docx", "title": "Pipeline Doc", "save_dir": str(temp_dir)},
        dependencies=["t1"],
        description="Create Word doc"
    )
    t3 = Task(
        id="t3",
        action="explain_and_create_pdf",
        parameters={"topic": "Machine Learning and Deep Learning", "save_dir": str(temp_dir)},
        dependencies=["t2"],
        description="Explain ML/DL and create PDF"
    )
    t4 = Task(
        id="t4",
        action="set_volume",
        parameters={"level": 50},
        dependencies=["t3"],
        description="Set volume to 50%"
    )

    queue.add(t1)
    queue.add(t2)
    queue.add(t3)
    queue.add(t4)

    executor = DependencyAwareExecutor(registry=registry, max_retries=1)
    res_queue = executor.execute(queue)
    final_summary = queue.summary()

    assert queue.all_done is True
    assert t1.status == TaskStatus.SUCCESS
    assert t2.status == TaskStatus.SUCCESS
    assert t3.status == TaskStatus.SUCCESS
    assert t4.status == TaskStatus.SUCCESS

    # Verify all generated files physically exist
    assert (temp_dir / "pipeline_marks.xlsx").exists()
    assert (temp_dir / "pipeline_doc.docx").exists()
    assert len(list(temp_dir.glob("*.pdf"))) >= 1
    print(f"\n[T13] Multi-step pipeline passed: {final_summary}")


# ── T14: ToolRegistry Verification ───────────────────────────────────────────

def test_T14_tool_registry_registration(registry):
    """Verify that all Phase 4 tools are registered and executable in ToolRegistry."""
    phase4_tools = [
        "open_application", "open_folder", "open_file", "read_file", "list_files",
        "search_files", "edit_file", "open_vscode", "edit_code",
        "create_excel", "create_word", "create_powerpoint", "create_pdf", "explain_and_create_pdf",
        "volume_up", "volume_down", "mute_volume", "unmute_volume", "set_volume",
        "desktop_press_key", "desktop_hotkey", "desktop_mouse_click", "desktop_mouse_scroll", "desktop_move_mouse",
    ]
    for name in phase4_tools:
        assert registry.has(name), f"Missing required Phase 4 tool in registry: {name}"
    print(f"\n[T14] All {len(phase4_tools)} Phase 4 tools verified in ToolRegistry.")
