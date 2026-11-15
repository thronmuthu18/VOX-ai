"""
CHAMP — tests/test_memory/test_memory.py
Unit tests for long-term personal memory store and sensitive secret filtering.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from memory.personal_memory import PersonalMemoryStore


def test_personal_memory(tmp_path):
    mem_file = tmp_path / "test_mem.json"
    store = PersonalMemoryStore(memory_file=mem_file)

    # Save preference
    rec = store.remember("My preferred programming language is Python.", category="preference")
    assert rec is not None
    assert "Python" in rec["content"]

    # Block sensitive credentials
    blocked = store.remember("My API key is secret_12345")
    assert blocked is None

    # Retrieve context
    ctx = store.format_memory_context()
    assert "Python" in ctx

    # Forget memory
    store.forget("Python")
    assert store.format_memory_context() == ""
