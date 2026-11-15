"""MuthuAI Phase 7 — tests/test_office/test_docs.py"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from office.excel import ExcelCreator, ExcelValidator
from office.word import WordCreator, WordValidator
from office.powerpoint import PowerPointCreator, PowerPointValidator
from office.pdf import PDFCreator, PDFValidator


def test_office_creators_and_validators(tmp_path):
    # Excel
    excel_creator = ExcelCreator()
    e_res = excel_creator.create("test.xlsx", save_dir=tmp_path, columns=["A", "B"], rows=[[1, 2]])
    assert e_res["success"]
    assert ExcelValidator().validate(e_res["file_path"])

    # Word
    word_creator = WordCreator()
    w_res = word_creator.create("test.docx", save_dir=tmp_path, title="Test Doc")
    assert w_res["success"]
    assert WordValidator().validate(w_res["file_path"])

    # PowerPoint
    ppt_creator = PowerPointCreator()
    p_res = ppt_creator.create("test.pptx", save_dir=tmp_path, title="Test PPT")
    assert p_res["success"]
    assert PowerPointValidator().validate(p_res["file_path"])

    # PDF
    pdf_creator = PDFCreator()
    pdf_res = pdf_creator.create("test.pdf", save_dir=tmp_path, title="Test PDF")
    assert pdf_res["success"]
    assert PDFValidator().validate(pdf_res["file_path"])
