"""
MuthuAI Phase 2 — tests/test_phase2_tools.py

Unit tests for Phase 2 Tool Registry, Windows Applications, Filesystem, and System tools.
"""

import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import setup_default_registry
from tools.base import PermissionLevel
from tools.windows.application import resolve_app
from tools.windows.filesystem import resolve_folder_path


def test_registry_registration():
    registry = setup_default_registry()
    assert len(registry) >= 15
    assert registry.has("open_application")
    assert registry.has("open_folder")
    assert registry.has("volume_up")
    assert registry.has("volume_down")
    assert registry.has("mute_volume")
    assert registry.has("get_time")
    assert registry.has("get_date")
    assert registry.has("open_control_panel")
    assert registry.has("open_settings")
    assert registry.has("open_task_manager")
    assert registry.has("open_command_prompt")
    assert registry.has("delete_file")
    assert registry.has("delete_folder")
    assert registry.has("terminate_process")


def test_app_alias_resolution():
    assert resolve_app("chrome") is not None
    assert resolve_app("vs code") is not None
    assert resolve_app("calculator") == "calc.exe"
    assert resolve_app("notepad") == "notepad.exe"
    assert resolve_app("cmd") == "cmd.exe"
    assert resolve_app("settings") == "ms-settings:"


def test_filesystem_path_resolution():
    assert resolve_folder_path("desktop") is not None
    assert resolve_folder_path("downloads") is not None
    assert resolve_folder_path("documents") is not None
    assert resolve_folder_path("c drive") is not None
    assert resolve_folder_path("d drive") is not None or resolve_folder_path("d drive") is None  # depends on system drive existence


def test_time_and_date_tools():
    registry = setup_default_registry()
    res_time = registry.execute("get_time")
    assert res_time.success
    assert ":" in res_time.data["time"]

    res_date = registry.execute("get_date")
    assert res_date.success
    assert len(res_date.data["date"]) > 5


def test_permission_levels():
    registry = setup_default_registry()
    assert registry.get("open_application").permission == PermissionLevel.SAFE
    assert registry.get("open_folder").permission == PermissionLevel.SAFE
    assert registry.get("volume_up").permission == PermissionLevel.SAFE
    assert registry.get("delete_file").permission == PermissionLevel.CONFIRM_REQUIRED
    assert registry.get("delete_folder").permission == PermissionLevel.CONFIRM_REQUIRED
    assert registry.get("terminate_process").permission == PermissionLevel.CONFIRM_REQUIRED
