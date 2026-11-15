"""
CHAMP — tests/test_office/test_files.py
Unit tests for Excel, Word, PowerPoint, PDF creators and workspace managers.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from office.excel import ExcelCreator, ExcelValidator
from office.word import WordCreator, WordValidator
from office.powerpoint import PowerPointCreator, PowerPointValidator
from office.pdf import PDFCreator, PDFValidator


def test_excel_creation(tmp_path):
    creator = ExcelCreator()
    res = creator.create(
        file_name="test_students.xlsx",
        save_dir=tmp_path,
        sheet_name="Grades",
        columns=["Student", "Score"],
        rows=[["Alice", 92], ["Bob", 88]],
        add_average_row=True
    )
    assert res["success"] is True
    assert Path(res["file_path"]).exists()
    assert ExcelValidator().validate(res["file_path"]) is True


def test_word_creation(tmp_path):
    creator = WordCreator()
    res = creator.create(
        file_name="test_report.docx",
        save_dir=tmp_path,
        title="Quarterly Report",
        headings=[("Overview", "Sales grew by 15% this quarter.")],
        bullet_points=["Q1 Goals met", "Team expanded"]
    )
    assert res["success"] is True
    assert Path(res["file_path"]).exists()
    assert WordValidator().validate(res["file_path"]) is True
