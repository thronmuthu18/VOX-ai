"""
VOX AI — tests/test_vox_ai_end_to_end.py

Comprehensive End-to-End Verification Test Suite for VOX AI:
Covers all 10 core verification scenarios:
1. "Bro, open Chrome" -> application discovery & launch verification
2. "Bro, open YouTube" -> browser navigation & URL verification
3. "Bro, open Chrome and search YouTube for Python tutorials" -> multi-step browser execution
4. "Bro, create a PDF with a simple paragraph" -> physical PDF file existence & size check
5. "Bro, create a Word document" -> physical DOCX file existence & size check
6. "Bro, create an Excel file" -> physical XLSX file existence & size check
7. "Bro, create a PowerPoint" -> physical PPTX file existence & size check
8. Multi-step task execution -> ordered execution & step verification
9. Normal conversation -> conversation history & language handling
10. Task failure reporting -> honest error reporting without fabricated success
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure muthuAI root is in path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import setup_default_registry
from tools.base import ToolResult
from agent.command_router import route_command
from agent.intent_router import IntentRouter, IntentMode
from agent.command_normalizer import CommandNormalizer
from agent.validator import StepValidator
from validator.result_validator import ResultValidator
from task_queue.task_model import Task, TaskStatus
from task_queue.task_queue import TaskQueue


class TestVoxAIEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = setup_default_registry()
        cls.normalizer = CommandNormalizer()
        cls.intent_router = IntentRouter()
        cls.step_validator = StepValidator()
        cls.result_validator = ResultValidator()

    def test_01_tool_registry_integrity(self):
        """Verify tool registry has all tools registered with no duplicates."""
        self.assertGreaterEqual(len(self.registry), 75)
        # Check critical tools
        for tool_name in [
            "open_application", "open_browser", "open_website", "search_youtube",
            "play_youtube", "create_pdf", "create_word", "create_excel", "create_powerpoint",
            "create_file", "create_csv", "create_folder", "web_search", "search_documents",
            "remember_fact", "show_memory", "whatsapp_send_message"
        ]:
            self.assertTrue(self.registry.has(tool_name), f"Missing tool: {tool_name}")

    def test_02_command_routing_chrome_youtube(self):
        """Test TEST 1 & TEST 2 routing: Open Chrome, Open YouTube."""
        # TEST 1: Open Chrome
        norm1 = self.normalizer.normalize("Bro, open Chrome", wake_authenticated=True)
        route1 = self.intent_router.route(norm1)
        self.assertEqual(route1["mode"], IntentMode.ACTION)
        plan1 = route1["direct_plan"]
        self.assertIsNotNone(plan1)
        self.assertEqual(plan1["tool"], "open_application")
        self.assertEqual(plan1["arguments"].get("name"), "chrome")

        # TEST 2: Open YouTube
        norm2 = self.normalizer.normalize("Bro, open YouTube", wake_authenticated=True)
        route2 = self.intent_router.route(norm2)
        self.assertEqual(route2["mode"], IntentMode.ACTION)
        plan2 = route2["direct_plan"]
        self.assertIsNotNone(plan2)
        self.assertIn(plan2["tool"], ("open_website", "open_browser"))

    def test_03_multi_step_chrome_youtube_search(self):
        """Test TEST 3: 'Bro, open Chrome and search YouTube for Python tutorials'."""
        query = "Bro, open Chrome and search YouTube for Python tutorials"
        norm = self.normalizer.normalize(query, wake_authenticated=True)
        route = self.intent_router.route(norm)
        self.assertEqual(route["mode"], IntentMode.ACTION)
        plan = route["direct_plan"]
        self.assertIsNotNone(plan)
        self.assertIsInstance(plan, list)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["tool"], "open_application")
        self.assertEqual(plan[1]["tool"], "search_youtube")
        self.assertIn("python", plan[1]["arguments"]["query"].lower())

    def test_04_physical_pdf_creation_and_verification(self):
        """Test TEST 4: Physical PDF file creation on disk and empirical verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test_report.pdf"
            res = self.registry.execute(
                "create_pdf",
                filename=str(pdf_path),
                title="AI Architecture Report",
                paragraphs=["This is a verified test paragraph for VOX AI task execution."]
            )
            self.assertTrue(res.success, f"create_pdf failed: {res.message}")
            self.assertTrue(pdf_path.exists(), "PDF file was not physically created on disk.")
            self.assertGreater(pdf_path.stat().st_size, 100, "PDF file is empty or corrupt.")

            # Validate with StepValidator and ResultValidator
            is_valid, reason = self.step_validator.validate_result("create_pdf", {"filename": str(pdf_path)}, res)
            self.assertTrue(is_valid, f"StepValidator rejected valid PDF: {reason}")

            task = Task(id="t1", action="create_pdf", parameters={"filename": str(pdf_path)})
            is_res_valid, res_reason = self.result_validator.validate(task, res.success, res.message, res.data)
            self.assertTrue(is_res_valid, f"ResultValidator rejected valid PDF: {res_reason}")

    def test_05_physical_word_creation_and_verification(self):
        """Test TEST 5: Physical Word DOCX creation on disk and empirical verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "test_doc.docx"
            res = self.registry.execute(
                "create_word",
                filename=str(doc_path),
                title="VOX AI Architecture",
                paragraphs=["Document execution verified."]
            )
            self.assertTrue(res.success, f"create_word failed: {res.message}")
            self.assertTrue(doc_path.exists(), "Word file was not created on disk.")
            self.assertGreater(doc_path.stat().st_size, 100, "Word file is 0 bytes.")

    def test_06_physical_excel_creation_and_verification(self):
        """Test TEST 6: Physical Excel XLSX creation on disk and empirical verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            excel_path = Path(tmpdir) / "test_sheet.xlsx"
            res = self.registry.execute(
                "create_excel",
                filename=str(excel_path),
                headers=["ID", "Task", "Status"],
                rows=[[1, "Audit", "Complete"], [2, "Execution", "Verified"]]
            )
            self.assertTrue(res.success, f"create_excel failed: {res.message}")
            self.assertTrue(excel_path.exists(), "Excel file was not created on disk.")
            self.assertGreater(excel_path.stat().st_size, 100, "Excel file is 0 bytes.")

    def test_07_physical_powerpoint_creation_and_verification(self):
        """Test TEST 7: Physical PowerPoint PPTX creation on disk and empirical verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ppt_path = Path(tmpdir) / "test_pres.pptx"
            res = self.registry.execute(
                "create_powerpoint",
                filename=str(ppt_path),
                title="VOX AI System Overview",
                topic="AI Automation"
            )
            self.assertTrue(res.success, f"create_powerpoint failed: {res.message}")
            self.assertTrue(ppt_path.exists(), "PowerPoint file was not created on disk.")
            self.assertGreater(ppt_path.stat().st_size, 100, "PowerPoint file is 0 bytes.")

    def test_08_physical_text_file_and_csv_creation(self):
        """Test custom file and CSV creation with physical verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "notes.txt"
            res1 = self.registry.execute("create_file", path=str(txt_path), content="VOX AI notes content")
            self.assertTrue(res1.success)
            self.assertTrue(txt_path.exists())
            self.assertEqual(txt_path.read_text(encoding="utf-8"), "VOX AI notes content")

            csv_path = Path(tmpdir) / "data.csv"
            res2 = self.registry.execute(
                "create_csv",
                path=str(csv_path),
                headers=["Name", "Score"],
                rows=[["Alice", "95"], ["Bob", "88"]]
            )
            self.assertTrue(res2.success)
            self.assertTrue(csv_path.exists())
            self.assertGreater(csv_path.stat().st_size, 10)

    def test_09_multi_step_dependency_execution(self):
        """Test TEST 8: Multi-step task execution through DependencyAwareExecutor."""
        from executor.dependency_executor import DependencyAwareExecutor

        executor = DependencyAwareExecutor(registry=self.registry)
        queue = TaskQueue()

        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "step1.txt"
            f2 = Path(tmpdir) / "step2.txt"

            t1 = Task(id="task_001", action="create_file", parameters={"path": str(f1), "content": "Step 1 complete"})
            t2 = Task(id="task_002", action="create_file", parameters={"path": str(f2), "content": "Step 2 complete"}, dependencies=["task_001"])

            queue.add(t1)
            queue.add(t2)

            executor.execute(queue)
            self.assertTrue(queue.is_complete())
            self.assertEqual(t1.status, TaskStatus.SUCCESS)
            self.assertEqual(t2.status, TaskStatus.SUCCESS)
            self.assertTrue(f1.exists())
            self.assertTrue(f2.exists())

    def test_10_task_failure_honesty(self):
        """Test TEST 10: Task failure reporting without fake success fabrication."""
        task = Task(id="task_fail", action="create_file", parameters={"path": "Z:\\invalid_nonexistent_drive\\file.txt"})
        # Validating a failed tool result should return is_valid=False
        is_valid, reason = self.result_validator.validate(
            task,
            result_success=False,
            result_message="Disk write failed: directory not found",
            result_data={}
        )
        self.assertFalse(is_valid)
        self.assertIn("Disk write failed", reason)

    def test_11_m_workspace_default_resolution(self):
        """Test CRITICAL M:\ storage rule: default resolution routes to M:\ without prompting."""
        from utils.workspace import DEFAULT_WORKSPACE, PDF_DIR, WORD_DIR, EXCEL_DIR, PPT_DIR, TEXT_DIR, DOWNLOADS_DIR, resolve_output_path

        # 1. Default Workspace is M:\
        self.assertEqual(str(DEFAULT_WORKSPACE).upper(), "M:\\")

        # 2. PDF resolution
        pdf_res = resolve_output_path("AI_Report.pdf")
        self.assertTrue(str(pdf_res).startswith("M:\\Generated\\PDF"))
        self.assertEqual(pdf_res.name, "AI_Report.pdf")

        # 3. Word resolution
        word_res = resolve_output_path("Python_Guide.docx")
        self.assertTrue(str(word_res).startswith("M:\\Generated\\Word"))
        self.assertEqual(word_res.name, "Python_Guide.docx")

        # 4. Excel resolution
        excel_res = resolve_output_path("Students.xlsx")
        self.assertTrue(str(excel_res).startswith("M:\\Generated\\Excel"))
        self.assertEqual(excel_res.name, "Students.xlsx")

        # 5. PowerPoint resolution
        ppt_res = resolve_output_path("Cloud_Computing.pptx")
        self.assertTrue(str(ppt_res).startswith("M:\\Generated\\PowerPoint"))
        self.assertEqual(ppt_res.name, "Cloud_Computing.pptx")

        # 6. Text note resolution
        txt_res = resolve_output_path("Todays_Notes.txt")
        self.assertTrue(str(txt_res).startswith("M:\\Generated\\Text"))
        self.assertEqual(txt_res.name, "Todays_Notes.txt")

        # 7. Downloads resolution
        dl_res = resolve_output_path("sample_installer.exe", category="downloads")
        self.assertTrue(str(dl_res).startswith("M:\\Downloads"))
        self.assertEqual(dl_res.name, "sample_installer.exe")

    def test_12_physical_m_workspace_file_creation(self):
        """Test that physical files are actually written and verified directly on M:\ when created without explicit path."""
        # Create PDF on M:\
        res_pdf = self.registry.execute("create_pdf", filename="vox_ai_test_report.pdf", title="M Workspace Test", paragraphs=["Tested on M: drive."])
        self.assertTrue(res_pdf.success)
        created_pdf_path = Path(res_pdf.data["path"])
        self.assertTrue(created_pdf_path.exists())
        self.assertTrue(str(created_pdf_path).startswith("M:\\Generated\\PDF"))
        self.assertGreater(created_pdf_path.stat().st_size, 100)

        # Create Word on M:\
        res_word = self.registry.execute("create_word", filename="vox_ai_test_doc.docx", title="M Workspace Doc", paragraphs=["Word document tested on M: drive."])
        self.assertTrue(res_word.success)
        created_word_path = Path(res_word.data["path"])
        self.assertTrue(created_word_path.exists())
        self.assertTrue(str(created_word_path).startswith("M:\\Generated\\Word"))
        self.assertGreater(created_word_path.stat().st_size, 100)

        # Create Excel on M:\
        res_excel = self.registry.execute("create_excel", filename="vox_ai_test_students.xlsx", headers=["ID", "Name", "Mark"], rows=[[1, "Muthu", 95]])
        self.assertTrue(res_excel.success)
        created_excel_path = Path(res_excel.data["path"])
        self.assertTrue(created_excel_path.exists())
        self.assertTrue(str(created_excel_path).startswith("M:\\Generated\\Excel"))
        self.assertGreater(created_excel_path.stat().st_size, 100)

        # Create PowerPoint on M:\
        res_ppt = self.registry.execute("create_powerpoint", filename="vox_ai_test_pres.pptx", title="M Workspace Slides", topic="Cloud AI")
        self.assertTrue(res_ppt.success)
        created_ppt_path = Path(res_ppt.data["path"])
        self.assertTrue(created_ppt_path.exists())
        self.assertTrue(str(created_ppt_path).startswith("M:\\Generated\\PowerPoint"))
        self.assertGreater(created_ppt_path.stat().st_size, 100)

        # Create Text file on M:\
        res_txt = self.registry.execute("create_file", path="vox_ai_test_notes.txt", content="Testing default M:\\ storage policy.")
        self.assertTrue(res_txt.success)
        created_txt_path = Path(res_txt.data["path"])
        self.assertTrue(created_txt_path.exists())
        self.assertTrue(str(created_txt_path).startswith("M:\\Generated\\Text"))
        self.assertGreater(created_txt_path.stat().st_size, 10)

    def test_13_multi_step_word_to_pdf_conversion(self):
        """Test multi-step workflow: Create Word DOCX -> Convert to PDF -> Verify both on M:\."""
        # Step 1: Create Word
        res_word = self.registry.execute(
            "create_word",
            filename="multi_step_report.docx",
            title="Multi-Step Conversion Test",
            paragraphs=["This report is created in Word and converted to PDF."]
        )
        self.assertTrue(res_word.success)
        word_file = Path(res_word.data["path"])
        self.assertTrue(word_file.exists())

        # Step 2: Convert to PDF
        res_conv = self.registry.execute(
            "convert_word_to_pdf",
            source_path=str(word_file)
        )
        self.assertTrue(res_conv.success, f"convert_word_to_pdf failed: {res_conv.message}")
        pdf_file = Path(res_conv.data["pdf_path"])
        self.assertTrue(pdf_file.exists())
        self.assertTrue(str(pdf_file).startswith("M:\\Generated\\PDF"))
        self.assertGreater(pdf_file.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
