"""
MuthuAI Phase 5 — tests/test_phase5_office.py

Unit tests for Phase 5 Office Automation (Excel, Word, PowerPoint, PDF), File Workspace, and Output Validation.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from office.excel import ExcelCreator, ExcelValidator, ExcelReader
from office.word import WordCreator, WordValidator
from office.powerpoint import PowerPointCreator, PowerPointValidator
from office.pdf import PDFCreator, PDFValidator
from files.manager import FileWorkspaceManager
from tools import setup_default_registry


def test_excel_creation_reading_and_validation(tmp_path):
    creator = ExcelCreator()
    res = creator.create(
        file_name="student_marks.xlsx",
        save_dir=tmp_path,
        columns=["Name", "Age", "Department", "Mark"],
        rows=[
            ["Alice", 20, "CSE", 95],
            ["Bob", 21, "ECE", 88],
            ["Charlie", 22, "EEE", 92]
        ],
        add_average_row=True
    )
    assert res["success"]
    file_path = res["file_path"]

    # Validate output
    validator = ExcelValidator()
    assert validator.validate(file_path, expected_columns=["Name", "Age", "Department", "Mark"])

    # Read output
    reader = ExcelReader()
    data = reader.read(file_path)
    assert data["success"]
    assert data["row_count"] >= 3
    assert "Name" in data["columns"]


def test_word_creation_and_validation(tmp_path):
    creator = WordCreator()
    res = creator.create(
        file_name="project_report.docx",
        save_dir=tmp_path,
        title="MuthuAI Project Report",
        headings=[("Introduction", "MuthuAI is a voice-controlled Windows desktop agent."), ("Features", "Supports Office automation and RAG.")],
        bullet_points=["Voice control", "Office automation", "Document RAG"],
        table_data=[["Module", "Status"], ["Excel", "Ready"], ["Word", "Ready"]]
    )
    assert res["success"]
    file_path = res["file_path"]

    validator = WordValidator()
    assert validator.validate(file_path)


def test_powerpoint_creation_and_validation(tmp_path):
    creator = PowerPointCreator()
    res = creator.create(
        file_name="ai_overview.pptx",
        save_dir=tmp_path,
        title="Artificial Intelligence Overview",
        subtitle="Presented by MuthuAI",
        slides=[
            {"title": "Introduction to AI", "content": "AI enables computers to simulate human intelligence.", "bullets": ["Machine Learning", "Deep Learning"]},
            {"title": "Applications", "bullets": ["Natural Language Processing", "Computer Vision", "Robotics"]}
        ]
    )
    assert res["success"]
    assert res["slide_count"] == 3  # Title slide + 2 content slides
    file_path = res["file_path"]

    validator = PowerPointValidator()
    assert validator.validate(file_path, expected_min_slides=3)


def test_pdf_creation_and_validation(tmp_path):
    creator = PDFCreator()
    res = creator.create(
        file_name="summary.pdf",
        save_dir=tmp_path,
        title="MuthuAI Executive Summary",
        paragraphs=["This report summarizes Phase 5 Office Automation capabilities."]
    )
    assert res["success"]
    file_path = res["file_path"]

    validator = PDFValidator()
    assert validator.validate(file_path)


def test_file_workspace_manager(tmp_path):
    mgr = FileWorkspaceManager()

    # Directory creation
    d_res = mgr.create_directory(tmp_path / "project_folder")
    assert d_res["success"]

    # File copy
    f1 = tmp_path / "test1.txt"
    f1.write_text("Hello workspace", encoding="utf-8")
    c_res = mgr.copy_file(f1, tmp_path / "project_folder")
    assert c_res["success"]
    assert (tmp_path / "project_folder" / "test1.txt").exists()

    # File rename
    r_res = mgr.rename_file(tmp_path / "project_folder" / "test1.txt", "test1_renamed.txt")
    assert r_res["success"]
    assert (tmp_path / "project_folder" / "test1_renamed.txt").exists()


def test_phase5_office_tools_registry():
    registry = setup_default_registry()
    assert len(registry) >= 40
    assert registry.has("create_excel")
    assert registry.has("read_excel")
    assert registry.has("create_word")
    assert registry.has("create_powerpoint")
    assert registry.has("create_pdf")
    assert registry.has("create_directory")
    assert registry.has("copy_file")
    assert registry.has("move_file")
    assert registry.has("rename_file")
