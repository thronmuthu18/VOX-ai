"""
CHAMP Voice, Language Detection, Conversation, and TTS Quality Test Suite.
Tests all requirements specified in the hardening prompt.
"""

import time
import pytest
from voice.language_detector import (
    detect_language,
    get_language_prompt_instruction,
    response_language_code,
    has_tamil_script,
    has_latin_script,
)
from voice.wake_word import WakeWordDetector
from speech.tts import (
    _normalize_for_tts,
    _split_into_sentences,
    _pick_voice,
    speak,
    cancel,
    is_speaking,
    get_tts_config,
    get_last_diagnostics,
)
from ai.prompt_manager import (
    conversational_prompt,
    rag_response_prompt,
    web_search_response_prompt,
    final_response_prompt,
)
from ai.conversation import ConversationManager


# ── 1. Language Detection & Style Policy Tests ───────────────────────────────

def test_language_detection_english():
    """A. Pure English query."""
    q = "What is artificial intelligence?"
    assert detect_language(q) == "en"
    assert "English" in get_language_prompt_instruction(detect_language(q))


def test_language_detection_tamil():
    """B. Pure Tamil query (Tamil grammar with subject)."""
    q = "Artificial intelligence என்றால் என்ன?"
    assert detect_language(q) == "ta"
    assert "Tamil" in get_language_prompt_instruction(detect_language(q))


def test_language_detection_tanglish():
    """C. Tanglish query (code-mixed Latin/Tamil)."""
    q = "Artificial intelligence-na enna bro?"
    assert detect_language(q) == "tanglish"
    assert "Tanglish" in get_language_prompt_instruction(detect_language(q))


def test_language_explicit_english_override():
    """D. Explicit English instruction overrides Tamil input."""
    q = "தமிழ்ல கேட்டாலும் answer in English."
    assert detect_language(q) == "en"


def test_language_explicit_tamil_override():
    """E. Explicit Tamil instruction."""
    q = "Explain this in Tamil."
    assert detect_language(q) == "ta"


def test_language_detection_mixed():
    """F. Mixed script with Tanglish particle."""
    q = "Bro machine learning-ஐ simple-ah explain பண்ணு."
    assert detect_language(q) == "tanglish"


def test_language_context_inheritance():
    """Language context inherited for ambiguous short tokens."""
    assert detect_language("yes", context_lang="ta") == "ta"
    assert detect_language("ok", context_lang="tanglish") == "tanglish"
    assert detect_language("sure", context_lang="en") == "en"


# ── 2. Conversation Memory & Follow-up Context ───────────────────────────────

def test_conversation_follow_up_context():
    """G. Follow-up query context tracking."""
    cm = ConversationManager(max_turns=5)
    cm.add_user_turn("What is deep learning?")
    cm.add_assistant_turn("Deep learning is a subset of machine learning using neural networks.")
    
    history = cm.get_history()
    assert len(history) == 2
    assert history[0]["text"] == "What is deep learning?"
    assert "neural networks" in history[1]["text"]

    # Format conversational prompt for follow-up
    prompt = conversational_prompt("Give me an example.", cm.summary(), "en")
    assert "Give me an example." in prompt


# ── 3. Wake Word Detection Tests ─────────────────────────────────────────────

def test_wake_word_detection():
    """H. Wake word detection for 'Bro' and variants."""
    detector = WakeWordDetector()
    assert detector.is_activated("Bro") is True
    assert detector.is_activated("Hey bro") is True
    assert detector.is_activated("Hi bro, what is machine learning?") is True
    assert detector.is_activated("புரோ") is True
    assert detector.is_activated("Come on bro, help me out") is True


def test_no_wake_word():
    """I. Non-wake word commands."""
    detector = WakeWordDetector()
    assert detector.is_activated("Open YouTube.") is False
    assert detector.is_activated("What is the time?") is False


# ── 4. Speech Normalization & Sentence Chunking Tests ────────────────────────

def test_text_normalization_markdown_and_code():
    """J. Strip markdown headers, bullets, code blocks, raw URLs."""
    raw = """### Machine Learning

- Supervised Learning: uses labelled data.
- Unsupervised Learning: uses unlabelled data.

```python
def train():
    pass
```
Check https://example.com/ml for more details! 😊"""

    cleaned = _normalize_for_tts(raw)
    assert "###" not in cleaned
    assert "def train" not in cleaned
    assert "https://" not in cleaned
    assert "Supervised Learning: uses labelled data." in cleaned
    assert "Unsupervised Learning: uses unlabelled data." in cleaned


def test_sentence_chunking_boundaries():
    """Sentence chunking splits on natural sentence terminators (. ! ? ।)."""
    text = "Machine learning is a branch of artificial intelligence. It allows systems to learn patterns from data! A simple example is spam detection."
    sentences = _split_into_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Machine learning is a branch of artificial intelligence."
    assert sentences[1] == "It allows systems to learn patterns from data!"
    assert sentences[2] == "A simple example is spam detection."


def test_sentence_chunking_tamil():
    """Sentence chunking for Tamil sentences."""
    tamil_text = "மெஷின் லேர்னிங் என்பது செயற்கை நுண்ணறிவின் ஒரு பகுதி. இது தரவுகளிலிருந்து கற்றுக்கொள்கிறது."
    sentences = _split_into_sentences(tamil_text)
    assert len(sentences) == 2


# ── 5. TTS Voice Selection & Configuration ───────────────────────────────────

def test_tts_voice_selection():
    """TTS voice correctly maps English vs Tamil."""
    voice_en = _pick_voice("What is artificial intelligence?")
    assert "Neerja" in voice_en or "en-IN" in voice_en

    voice_ta = _pick_voice("செயற்கை நுண்ணறிவு என்றால் என்ன?")
    assert "Pallavi" in voice_ta or "ta-IN" in voice_ta


def test_tts_config():
    """TTS configuration returns valid rate and parameters."""
    cfg = get_tts_config()
    assert "rate" in cfg
    assert "voice_tamil" in cfg
    assert "voice_english" in cfg
    assert "+12%" in cfg["rate"] or "%" in cfg["rate"]


# ── 6. Live TTS Synthesis & Barge-in Test ────────────────────────────────────

def test_live_tts_speak_and_barge_in():
    """M, N, O: Live speak and instantaneous barge-in test."""
    # Test short speak
    speak("Hello Champ.")
    diag = get_last_diagnostics()
    assert diag is not None
    assert diag["normalized_text"] == "Hello Champ."

    # Test immediate cancel
    cancel()
    assert is_speaking() is False
