"""
CHAMP — tests/test_voice/test_speech.py
Unit tests for language detection and wake word detector.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from voice.language_detector import detect_language
from voice.wake_word import WakeWordDetector


def test_language_detection():
    assert detect_language("Hello how are you") == "en"
    assert detect_language("வணக்கம் எப்படி இருக்கிறீர்கள்") == "ta"
    assert detect_language("Chrome open pannu") == "tanglish"


def test_wake_word_detector():
    detector = WakeWordDetector()
    
    assert detector.is_activated("Hey Bro") is True
    assert detector.is_activated("Bro open Chrome") is True
    assert detector.is_activated("Wake up Bro") is True
    assert detector.is_activated("Hello world") is False
    assert detector.is_activated("ஹே ப்ரோ") is True
    assert detector.is_activated("ப்ரோ ஓப்பன் குரோம்") is True
    assert detector.is_activated("புரோ") is True

    assert detector.strip_wake_word("Hey Bro open Chrome") == "open Chrome"
    assert detector.strip_wake_word("Bro") == ""
    assert detector.strip_wake_word("ப்ரோ ஓப்பன் குரோம்") == "ஓப்பன் குரோம்"
    assert detector.strip_wake_word("ஹே ப்ரோ ஓப்பன் குரோம்") == "ஓப்பன் குரோம்"
    assert detector.strip_wake_word("புரோ") == ""
