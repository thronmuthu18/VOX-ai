"""MuthuAI Phase 7 — tests/test_memory/test_mem.py"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from memory.personal_memory import PersonalMemoryStore


def test_personal_memory_store(tmp_path):
    mem_file = tmp_path / "mem.json"
    store = PersonalMemoryStore(memory_file=mem_file)

    rec = store.remember("I prefer Tamil explanations", category="preference")
    assert rec is not None

    all_mem = store.get_all()
    assert len(all_mem) == 1

    # Secret filtering test
    secret_rec = store.remember("My password is SecretPass123")
    assert secret_rec is None
