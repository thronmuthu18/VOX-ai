"""
MuthuAI Phase 5 — office/word/creator.py

Word Document (.docx) Creator using python-docx.
Supports Titles, Headings, Paragraphs, Bullet Lists, Tables, and Footers.
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger

log = get_logger("muthuai.office.word.creator")


class WordCreator:
    """
    Creates styled Word documents (.docx) with structured content.
    """

    def create(
        self,
        file_name: str = "document.docx",
        save_dir: str | Path = "data/documents",
        title: str = "",
        headings: list[tuple[str, str]] | None = None,  # [(Heading Title, Paragraph Text), ...]
        paragraphs: list[str] | None = None,
        bullet_points: list[str] | None = None,
        table_data: list[list] | None = None,
        open_after: bool = False
    ) -> dict:
        """
        Create a Word document (.docx).
        headings format: [("Section Title", "Section content text..."), ...]
        """
        save_path = Path(save_dir).resolve() / (file_name if file_name.endswith(".docx") else f"{file_name}.docx")
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from docx import Document
            from docx.shared import Pt, RGBColor, Inches
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()

            # Set margins (1 inch)
            for s in doc.sections:
                s.top_margin = Inches(1)
                s.bottom_margin = Inches(1)
                s.left_margin = Inches(1)
                s.right_margin = Inches(1)

            # Document Title
            if title:
                heading = doc.add_heading(title, level=0)
                heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if heading.runs:
                    heading.runs[0].font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)

            # General Paragraphs
            if paragraphs:
                for p in paragraphs:
                    doc.add_paragraph(p)

            # Headings with section text
            if headings:
                for h_title, h_text in headings:
                    doc.add_heading(h_title, level=1)
                    if h_text:
                        doc.add_paragraph(h_text)

            # Bullet List Points
            if bullet_points:
                for b in bullet_points:
                    doc.add_paragraph(b, style="List Bullet")

            # Table
            if table_data and len(table_data) > 0:
                rows_cnt = len(table_data)
                cols_cnt = len(table_data[0])
                table = doc.add_table(rows=rows_cnt, cols=cols_cnt)
                table.style = "Table Grid"
                for r_idx, row_items in enumerate(table_data):
                    for c_idx, val in enumerate(row_items):
                        cell = table.cell(r_idx, c_idx)
                        cell.text = str(val)

            # Footer
            footer = doc.sections[0].footer
            footer.paragraphs[0].text = f"Created by MuthuAI — {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            doc.save(str(save_path))
            log.info("Word document created: %s", save_path)

            if open_after:
                try:
                    os.startfile(str(save_path))
                except Exception:
                    pass

            return {
                "success": True,
                "file_path": str(save_path),
                "file_name": save_path.name,
                "message": f"Word document '{save_path.name}' created successfully."
            }

        except Exception as exc:
            log.error("Failed to create Word document %s: %s", save_path.name, exc)
            return {"success": False, "file_path": "", "message": f"Could not create Word document: {exc}"}
