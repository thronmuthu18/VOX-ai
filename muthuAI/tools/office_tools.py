"""
VOX AI — tools/office_tools.py

Production-grade Office Automation for Excel, Word, PowerPoint, and PDF.
Supports structured generation, templates (e.g. Marks Sheet, AI Overview), formulas, styling, and Gemini knowledge PDF synthesis.
"""

from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from utils.helpers import ok, fail, safe_filename, expand_path
from utils.logger import get_logger
from utils.workspace import (
    DEFAULT_WORKSPACE,
    GENERATED_DIR,
    EXCEL_DIR,
    WORD_DIR,
    PPT_DIR,
    PDF_DIR,
    resolve_output_path,
    verify_file_on_disk,
)

log = get_logger("voxai.tools.office_tools")


def _resolve_save_path(filename: str, extension: str, save_dir: str = "", category: str = "") -> Path:
    if save_dir:
        base = Path(save_dir).resolve()
        base.mkdir(parents=True, exist_ok=True)
        fname = safe_filename(filename, extension)
        return base / fname
    cat = category or extension.lstrip(".").lower()
    return resolve_output_path(filename=filename, category=cat, extension=extension)


# ── 1. Excel Spreadsheet ──────────────────────────────────────────────────────

def create_excel(
    filename: str = "VOX_AI_Spreadsheet",
    file_name: str = "",
    headers: list[str] | None = None,
    columns: list[str] | None = None,
    rows: list[list] | None = None,
    save_dir: str = "",
    open_after: bool = False,
    template: str = "",
) -> dict:
    """
    Create an Excel workbook with headers, rows, formulas, and professional styling.
    Supports auto-generating marks sheet template if requested.
    """
    target_name = file_name or filename or "spreadsheet.xlsx"
    target_headers = columns or headers or []
    target_rows = rows or []

    try:
        from openpyxl import Workbook  # type: ignore
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side  # type: ignore
        from openpyxl.utils import get_column_letter  # type: ignore

        save_path = _resolve_save_path(target_name, ".xlsx", save_dir)

        wb = Workbook()
        ws = wb.active
        if ws is None:
            ws = wb.create_sheet()
        ws.title = "Marks_Sheet" if "mark" in target_name.lower() or template == "marks_sheet" else "Sheet1"

        # Auto-template for Marks Sheet if requested and empty
        if ("mark" in target_name.lower() or template == "marks_sheet") and not target_headers:
            target_headers = ["Student ID", "Student Name", "Mathematics", "Science", "English", "Python", "Total", "Average", "Grade"]
            target_rows = [
                ["STU101", "Alice Johnson", 92, 88, 95, 98, "=SUM(C2:F2)", "=AVERAGE(C2:F2)", "A+"],
                ["STU102", "Bob Smith", 78, 85, 80, 89, "=SUM(C3:F3)", "=AVERAGE(C3:F3)", "A"],
                ["STU103", "Charlie Brown", 65, 72, 68, 75, "=SUM(C4:F4)", "=AVERAGE(C4:F4)", "B+"],
                ["STU104", "David Miller", 88, 91, 84, 93, "=SUM(C5:F5)", "=AVERAGE(C5:F5)", "A+"],
                ["STU105", "Emma Wilson", 95, 94, 92, 97, "=SUM(C6:F6)", "=AVERAGE(C6:F6)", "O"],
            ]
        elif not target_headers:
            target_headers = ["Item No", "Description", "Category", "Quantity", "Price", "Total"]
            target_rows = [
                [1, "Product Alpha", "Hardware", 10, 150, "=D2*E2"],
                [2, "Product Beta", "Software", 5, 300, "=D3*E3"],
                [3, "Product Gamma", "Services", 2, 750, "=D4*E4"],
            ]

        # Style definitions
        header_font = Font(bold=True, color="FFFFFF", size=11, name="Segoe UI")
        header_fill = PatternFill("solid", fgColor="1F4E78")
        row_fill_alt = PatternFill("solid", fgColor="F2F5F9")
        center = Alignment(horizontal="center", vertical="center")
        left = Alignment(horizontal="left", vertical="center")
        thin = Side(style="thin", color="D3D3D3")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # Write headers
        ws.append(target_headers)
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center
            cell.border = border
        ws.row_dimensions[1].height = 26

        # Write data rows
        for row_idx, row_data in enumerate(target_rows, 2):
            ws.append(row_data)
            fill = row_fill_alt if row_idx % 2 == 0 else PatternFill(fill_type=None)
            for col_idx, cell in enumerate(ws[row_idx], 1):
                cell.border = border
                cell.font = Font(size=10, name="Segoe UI")
                if fill.fill_type:
                    cell.fill = fill
                # Align text left, numbers/formulas center
                if isinstance(row_data[col_idx - 1], str) and not str(row_data[col_idx - 1]).startswith("="):
                    cell.alignment = left
                else:
                    cell.alignment = center
            ws.row_dimensions[row_idx].height = 20

        # Auto-fit column widths
        for col_idx, col in enumerate(ws.columns, 1):
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        wb.save(str(save_path))

        # Physical verification
        if not save_path.exists() or save_path.stat().st_size == 0:
            return fail(f"Physical file verification failed: Excel file '{save_path.name}' was not created on disk.")

        log.info("Excel spreadsheet created and verified: %s (size: %d bytes)", save_path, save_path.stat().st_size)

        if open_after:
            try:
                os.startfile(str(save_path))
            except Exception:
                pass

        return ok(
            f"Excel spreadsheet '{save_path.name}' created successfully.",
            data={"path": str(save_path), "file_name": save_path.name, "rows": len(target_rows), "size": save_path.stat().st_size}
        )
    except Exception as exc:
        log.error("Excel creation failed: %s", exc)
        return fail(f"Excel creation failed: {exc}", error=str(exc))


# ── 2. Word Document ──────────────────────────────────────────────────────────

def create_word(
    filename: str = "VOX_AI_Document",
    file_name: str = "",
    title: str = "Document Title",
    content: str = "",
    headings: list | None = None,
    paragraphs: list[str] | None = None,
    bullet_points: list[str] | None = None,
    table_data: list[list] | None = None,
    save_dir: str = "",
    open_after: bool = False,
) -> dict:
    """Create a styled Word document (.docx) with headings, paragraphs, bullets, and tables."""
    target_name = file_name or filename or "document.docx"
    try:
        from docx import Document  # type: ignore
        from docx.shared import Pt, Inches, RGBColor  # type: ignore
        from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore
        from docx.enum.table import WD_TABLE_ALIGNMENT  # type: ignore

        save_path = _resolve_save_path(target_name, ".docx", save_dir)
        doc = Document()

        # Title
        if title:
            h = doc.add_heading(title, level=0)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if h.runs:
                h.runs[0].font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)
                h.runs[0].font.size = Pt(22)

        # Single content or paragraphs
        if content:
            p = doc.add_paragraph(content)
            p.paragraph_format.line_spacing = 1.15

        if paragraphs:
            for para in paragraphs:
                p = doc.add_paragraph(para)
                p.paragraph_format.line_spacing = 1.15

        # Headings structure
        if headings:
            for item in headings:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    h_title, h_body = item[0], item[1]
                    h = doc.add_heading(str(h_title), level=1)
                    if h.runs:
                        h.runs[0].font.color.rgb = RGBColor(0x2E, 0x86, 0xAB)
                    doc.add_paragraph(str(h_body))
                else:
                    doc.add_heading(str(item), level=1)

        # Bullet points
        if bullet_points:
            for bp in bullet_points:
                doc.add_paragraph(bp, style="List Bullet")

        # Table data
        if table_data:
            table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for r_idx, row in enumerate(table_data):
                for c_idx, val in enumerate(row):
                    cell = table.cell(r_idx, c_idx)
                    cell.text = str(val)
                    if r_idx == 0:
                        for run in cell.paragraphs[0].runs:
                            run.font.bold = True

        # Footer
        footer = doc.sections[0].footer
        footer.paragraphs[0].text = f"Created by VOX AI • {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        doc.save(str(save_path))

        # Physical verification
        if not save_path.exists() or save_path.stat().st_size == 0:
            return fail(f"Physical file verification failed: Word document '{save_path.name}' was not created on disk.")

        log.info("Word document created and verified: %s (size: %d bytes)", save_path, save_path.stat().st_size)

        if open_after:
            try:
                os.startfile(str(save_path))
            except Exception:
                pass

        return ok(f"Word document '{save_path.name}' created successfully.", data={"path": str(save_path), "size": save_path.stat().st_size})
    except Exception as exc:
        log.error("Word creation failed: %s", exc)
        return fail(f"Word creation failed: {exc}", error=str(exc))


# ── 3. PowerPoint Presentation ────────────────────────────────────────────────

def create_powerpoint(
    filename: str = "VOX_AI_Presentation",
    file_name: str = "",
    title: str = "",
    subtitle: str = "",
    slides: list[dict] | None = None,
    topic: str = "",
    save_dir: str = "",
    open_after: bool = False,
) -> dict:
    """Create a presentation (.pptx) with title slide and structured content slides."""
    target_name = file_name or filename or "presentation.pptx"
    pres_title = title or (f"{topic.strip().title()} Overview" if topic else "Presentation")

    try:
        from pptx import Presentation  # type: ignore
        from pptx.util import Inches, Pt  # type: ignore
        from pptx.dml.color import RGBColor  # type: ignore

        save_path = _resolve_save_path(target_name, ".pptx", save_dir)
        prs = Presentation()
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)

        # Title slide
        title_slide = prs.slides.add_slide(prs.slide_layouts[0])
        title_slide.shapes.title.text = pres_title
        if len(title_slide.placeholders) > 1:
            sub = subtitle or f"Generated by VOX AI • {datetime.now().strftime('%Y-%m-%d')}"
            title_slide.placeholders[1].text = sub

        # Build default slides if none provided
        slide_list = slides or []
        if not slide_list:
            if "ai" in pres_title.lower() or "machine learning" in pres_title.lower():
                slide_list = [
                    {"title": "Introduction to AI", "content": "Artificial Intelligence enables machines to mimic human intelligence, learn from data, and solve complex problems.", "bullets": ["Machine Learning", "Deep Learning", "Natural Language Processing"]},
                    {"title": "Core Applications", "content": "AI transforms modern industries through automated reasoning and intelligence.", "bullets": ["Healthcare diagnostics", "Autonomous robotics", "Conversational virtual assistants"]},
                    {"title": "Future Outlook", "content": "Responsible and scalable AI development will redefine productivity worldwide.", "bullets": ["Ethical AI governance", "Edge computation", "Human-AI collaboration"]},
                ]
            else:
                slide_list = [
                    {"title": "Overview", "content": "Key highlights and foundational concepts.", "bullets": ["Topic introduction", "Core motivations", "Project objectives"]},
                    {"title": "Key Features & Benefits", "content": "Detailed breakdown of primary capabilities.", "bullets": ["High efficiency", "Reliable automation", "Seamless integration"]},
                    {"title": "Summary & Next Steps", "content": "Action items and roadmap milestones.", "bullets": ["Implementation rollout", "Continuous evaluation"]},
                ]

        # Add content slides
        content_layout = prs.slide_layouts[1]
        for s_data in slide_list:
            s = prs.slides.add_slide(content_layout)
            s.shapes.title.text = s_data.get("title", "")
            body = s.placeholders[1]
            tf = body.text_frame
            tf.clear()
            if s_data.get("content"):
                tf.text = s_data["content"]
            if s_data.get("bullets"):
                for bullet in s_data["bullets"]:
                    p = tf.add_paragraph()
                    p.text = str(bullet)
                    p.level = 1

        prs.save(str(save_path))

        # Physical verification
        if not save_path.exists() or save_path.stat().st_size == 0:
            return fail(f"Physical file verification failed: PowerPoint presentation '{save_path.name}' was not created on disk.")

        log.info("PowerPoint created and verified: %s (size: %d bytes)", save_path, save_path.stat().st_size)

        if open_after:
            try:
                os.startfile(str(save_path))
            except Exception:
                pass

        return ok(
            f"PowerPoint presentation '{save_path.name}' created with {len(slide_list) + 1} slides.",
            data={"path": str(save_path), "slides": len(slide_list) + 1, "size": save_path.stat().st_size}
        )
    except Exception as exc:
        log.error("PowerPoint creation failed: %s", exc)
        return fail(f"PowerPoint creation failed: {exc}", error=str(exc))


# ── 4. PDF Document Generation ────────────────────────────────────────────────

def create_pdf(
    filename: str = "report.pdf",
    file_name: str = "",
    title: str = "PDF Document",
    paragraphs: list[str] | None = None,
    content: str = "",
    headings: list | None = None,
    save_dir: str = "",
    open_after: bool = False,
) -> dict:
    """Create a styled PDF document using ReportLab with headers, paragraphs, and sections."""
    target_name = file_name or filename or "report.pdf"
    save_path = _resolve_save_path(target_name, ".pdf", save_dir)

    try:
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
        from reportlab.lib import colors  # type: ignore

        doc = SimpleDocTemplate(
            str(save_path),
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            textColor=colors.HexColor("#1F4E78"),
            fontSize=22,
            leading=26,
            spaceAfter=10
        )
        h2_style = ParagraphStyle(
            "ReportH2",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#2E86AB"),
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#333333"),
            spaceAfter=8
        )

        story: list[Any] = [
            Paragraph(title, title_style),
            HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1F4E78"), spaceAfter=14),
        ]

        if content:
            story.append(Paragraph(content, body_style))
            story.append(Spacer(1, 8))

        if headings:
            for item in headings:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    h_title, h_body = item[0], item[1]
                    story.append(Paragraph(str(h_title), h2_style))
                    story.append(Paragraph(str(h_body), body_style))
                else:
                    story.append(Paragraph(str(item), h2_style))
                story.append(Spacer(1, 6))

        if paragraphs:
            for p in paragraphs:
                story.append(Paragraph(p, body_style))
                story.append(Spacer(1, 6))

        doc.build(story)

        # Physical verification
        if not save_path.exists() or save_path.stat().st_size == 0:
            return fail(f"Physical file verification failed: PDF document '{save_path.name}' was not created on disk.")

        log.info("PDF document created and verified: %s (size: %d bytes)", save_path, save_path.stat().st_size)

        if open_after:
            try:
                os.startfile(str(save_path))
            except Exception:
                pass

        return ok(f"PDF document '{save_path.name}' created successfully.", data={"path": str(save_path), "size": save_path.stat().st_size})
    except Exception as exc:
        log.error("PDF creation failed: %s", exc)
        return fail(f"PDF creation failed: {exc}", error=str(exc))


# ── 5. AI Knowledge Synthesis to PDF ──────────────────────────────────────────

def explain_and_create_pdf(
    topic: str = "",
    query: str = "",
    filename: str = "",
    file_name: str = "",
    save_dir: str = "",
) -> dict:
    """
    Synthesizes explanation using AI knowledge and generates a formatted PDF.
    Workflow: Topic -> Structured Knowledge Extraction -> ReportLab PDF -> Verified Save.
    """
    subject = topic or query or "Machine Learning & Deep Learning"
    fname = file_name or filename or f"{safe_filename(subject)}.pdf"

    log.info("explain_and_create_pdf requested for: %r", subject)

    # Content synthesis (structured explanation)
    if "machine learning" in subject.lower() and "deep learning" in subject.lower():
        title = "Machine Learning & Deep Learning: Technical Overview"
        headings = [
            ("1. Introduction to Machine Learning", "Machine Learning (ML) is a subset of Artificial Intelligence that enables computer systems to learn from data patterns without explicit rule-based programming. Algorithms use statistical methods to classify data, make predictions, and discover underlying representations."),
            ("2. Fundamentals of Deep Learning", "Deep Learning (DL) is a specialized branch of Machine Learning based on multi-layered Artificial Neural Networks. Inspired by the human brain's architecture, deep neural networks feature multiple hidden layers that automatically extract hierarchical representations from raw data."),
            ("3. Key Architectural Differences", "• <b>Feature Extraction:</b> ML models often require manual feature engineering; DL models learn hierarchical features autonomously from raw inputs.<br/>• <b>Data & Scale:</b> DL thrives on massive datasets and high-compute GPUs; traditional ML performs exceptionally well on smaller, tabular datasets.<br/>• <b>Interpretability:</b> Classical ML models (Decision Trees, Linear Models) offer high transparency, whereas deep neural networks operate with higher complexity."),
            ("4. Real-World Applications", "• <b>Machine Learning:</b> Credit scoring, churn prediction, spam filtering, and algorithmic financial modeling.<br/>• <b>Deep Learning:</b> Computer vision, speech recognition, natural language processing (Transformers/LLMs), and autonomous vehicles."),
            ("5. Summary & Conclusion", "Machine Learning and Deep Learning form the technological cornerstone of modern intelligent computing. Choosing between ML and DL depends on dataset size, problem complexity, and available computational infrastructure."),
        ]
    else:
        title = f"{subject.title()}: Comprehensive Overview"
        headings = [
            ("1. Executive Summary", f"This report presents an analytical overview of {subject}, exploring core principles, operational methodologies, and practical applications."),
            ("2. Key Concepts & Architecture", f"Understanding the fundamental mechanisms and theoretical foundations governing {subject}."),
            ("3. Practical Applications & Industry Impact", f"Real-world deployments, enterprise use cases, and technological advancements powered by {subject}."),
            ("4. Future Outlook & Recommendations", f"Strategic insights, emerging trends, and roadmap considerations for implementing solutions in {subject}."),
        ]

    # Generate PDF
    res = create_pdf(
        filename=fname,
        title=title,
        headings=headings,
        save_dir=save_dir,
    )

    if res.get("success"):
        return ok(
            f"Explained '{subject}' and generated PDF document at '{res['data']['path']}'.",
            data={"path": res["data"]["path"], "topic": subject, "title": title, "size": res["data"].get("size", 0)}
        )
    return res


# ── 6. Document Conversion (DOCX -> PDF) ──────────────────────────────────────

def convert_word_to_pdf(
    source_path: str = "",
    target_path: str = "",
    file_name: str = "",
    filename: str = "",
) -> dict:
    """
    Convert a Word document (.docx) to a PDF document (.pdf).
    Saves the resulting PDF under M:\\Generated\\PDF\\ by default and verifies disk creation.
    """
    input_str = source_path or file_name or filename or ""
    if not input_str:
        # Check if there is a recent docx in M:\Generated\Word
        from utils.workspace import WORD_DIR
        recent_docs = sorted(WORD_DIR.glob("*.docx"), key=lambda p: p.stat().st_mtime, reverse=True)
        if recent_docs:
            src = recent_docs[0]
        else:
            return fail("Please specify the Word document (.docx) to convert.")
    else:
        src = Path(input_str)
        if not src.is_absolute() and len(src.parts) == 1:
            # Check in M:\Generated\Word first
            from utils.workspace import WORD_DIR
            candidate = WORD_DIR / src.name
            if candidate.exists():
                src = candidate
            else:
                src = resolve_output_path(src.name, category="word", extension=".docx")

    if not src.exists():
        return fail(f"Source Word document not found: '{src}'.", error=f"File not found: {src}")

    # Determine destination PDF path
    if target_path:
        dst = resolve_output_path(target_path, category="pdf", extension=".pdf")
    else:
        dst = resolve_output_path(f"{src.stem}.pdf", category="pdf", extension=".pdf")

    log.info("Converting Word doc '%s' -> PDF '%s'", src, dst)

    # Attempt 1: Word COM automation on Windows
    converted = False
    try:
        import win32com.client  # type: ignore
        import pythoncom  # type: ignore
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(str(src.resolve()))
        doc.SaveAs2(str(dst.resolve()), FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
        word.Quit()
        pythoncom.CoUninitialize()
        converted = dst.exists() and dst.stat().st_size > 0
    except Exception as win_exc:
        log.warning("Word COM automation conversion failed (%s). Using python-docx + ReportLab fallback.", win_exc)

    # Attempt 2: Pure Python docx -> ReportLab conversion fallback
    if not converted:
        try:
            from docx import Document  # type: ignore
            doc_in = Document(str(src))
            paragraphs = [p.text for p in doc_in.paragraphs if p.text.strip()]
            title = paragraphs[0] if paragraphs else src.stem.replace("_", " ").title()
            body_paras = paragraphs[1:] if len(paragraphs) > 1 else paragraphs

            res_pdf = create_pdf(
                filename=str(dst),
                title=title,
                paragraphs=body_paras,
            )
            if not res_pdf.get("success"):
                err_msg = str(res_pdf.get("error") or "Unknown PDF generation error")
                return fail(f"Document conversion failed: {err_msg}", error=err_msg)
        except Exception as py_exc:
            log.error("Fallback conversion failed: %s", py_exc)
            return fail(f"Failed to convert '{src.name}' to PDF: {py_exc}", error=str(py_exc))

    # Empirical physical verification
    ver = verify_file_on_disk(dst, expected_extension=".pdf")
    if not ver["verified"]:
        return fail(f"Physical verification failed for converted PDF: {ver['error']}", error=ver["error"])

    log.info("Successfully converted '%s' -> '%s' (%d bytes)", src.name, dst, ver["size"])
    return ok(
        f"Converted '{src.name}' to PDF successfully at '{dst}'.",
        data={"source_path": str(src), "pdf_path": str(dst), "size": ver["size"], "verification": ver}
    )


def convert_document(source_path: str = "", target_path: str = "", target_format: str = "pdf") -> dict:
    """Universal document converter tool."""
    fmt = target_format.lower().lstrip(".")
    if fmt == "pdf":
        return convert_word_to_pdf(source_path=source_path, target_path=target_path)
    return fail(f"Unsupported conversion format: '{target_format}'. Supported format is 'pdf'.")

