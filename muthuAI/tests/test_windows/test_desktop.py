"""MuthuAI Phase 7 — tests/test_windows/test_desktop.py"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.windows.application import resolve_app
from tools.windows.filesystem import resolve_folder_path


def test_app_alias_resolver():
    assert resolve_app("chrome") is not None
    assert resolve_app("calculator") == "calc.exe"


def test_folder_path_resolver():
    assert resolve_folder_path("desktop") is not None
    assert resolve_folder_path("downloads") is not None
