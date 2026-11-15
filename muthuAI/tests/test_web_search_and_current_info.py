"""
CHAMP — tests/test_web_search_and_current_info.py

Comprehensive test suite for:
- Internet connectivity diagnostics
- Multilingual freshness detection (English, Tamil, Tanglish)
- Search query optimization & date awareness
- Web search multi-provider retrieval & source extraction
- Gemini answer grounding (no 'I don't have internet' false claims)
- Follow-up conversation context
"""

import pytest
from retrieval.web_search import (
    check_internet_connectivity,
    is_freshness_query,
    build_optimized_search_queries,
    WebSearcher,
)
from retrieval.source_processor import SourceProcessor
from ai.prompt_manager import web_search_response_prompt


# ── 1. Internet Connectivity & Diagnostics Tests ────────────────────────────

def test_check_internet_connectivity():
    status = check_internet_connectivity()
    assert "internet_available" in status
    assert "status_code" in status
    assert "message" in status
    assert status["internet_available"] is True
    assert status["status_code"] == "INTERNET_AVAILABLE"


# ── 2. Freshness Query Intent Classification Tests ──────────────────────────

@pytest.mark.parametrize("query,expected", [
    # English current-information queries
    ("What is the latest AI news?", True),
    ("What happened in the world today?", True),
    ("What is happening in India today?", True),
    ("What is happening in Tamil Nadu today?", True),
    ("What happened in Tirunelveli today?", True),
    ("What is happening in Nepal right now?", True),
    ("What is the latest news about floods in Nepal?", True),
    ("Give me today's important technology news.", True),
    ("What's the latest update about AI?", True),
    ("Search the latest AI news and explain it in English.", True),

    # Tamil current-information queries (Tamil Unicode)
    ("தமிழ்நாட்டு லேட்டஸ்ட் நியூஸ் என்ன", True),
    ("இன்னைக்கு என்ன news", True),
    ("தமிழ்நாட்டுல இப்போ என்ன நடந்துட்டு இருக்கு", True),
    ("திருநெல்வேலி இன்றைய செய்திகள்", True),
    ("நேபாளம் வெள்ள நிலவரம் என்ன", True),

    # Tanglish current-information queries
    ("Tamil-la latest news sollu.", True),
    ("Nepal-la ippo enna nadakuthu?", True),
    ("Bro, Tirunelveli-la inniku enna nadanthirukku?", True),
    ("World-la latest news enna?", True),
    ("Nepal flood situation ippo epdi irukku?", True),

    # Negative tests (Standard / Static conversational questions)
    ("What is machine learning?", False),
    ("What is recursion?", False),
    ("How does a binary search tree work?", False),
    ("What is Python?", False),
])
def test_freshness_intent_classification(query, expected):
    assert is_freshness_query(query) is expected


# ── 3. Query Optimization & Date Awareness Tests ────────────────────────────

def test_query_optimization_tamil_nadu():
    candidates = build_optimized_search_queries("தமிழ்நாட்டு லேட்டஸ்ட் நியூஸ் என்ன")
    assert len(candidates) > 0
    # Should produce English keyword query like 'Tamil Nadu today August 2026' or 'Tamil Nadu latest news'
    assert any("tamil nadu" in c.lower() for c in candidates)


def test_query_optimization_nepal_floods():
    candidates = build_optimized_search_queries("Nepal flood situation ippo epdi irukku?")
    assert len(candidates) > 0
    assert any("nepal" in c.lower() and "flood" in c.lower() for c in candidates)


def test_query_optimization_tirunelveli():
    candidates = build_optimized_search_queries("Bro, Tirunelveli-la inniku enna nadanthirukku?")
    assert len(candidates) > 0
    assert any("tirunelveli" in c.lower() for c in candidates)


# ── 4. Live Search Retrieval & Source Extraction Tests ──────────────────────

def test_live_web_search_ai_news():
    searcher = WebSearcher()
    results = searcher.search("latest AI news updates", max_results=3)
    assert len(results) > 0
    for r in results:
        assert "title" in r and len(r["title"]) > 0
        assert "url" in r
        assert "source" in r


def test_live_web_search_tamil_nadu():
    searcher = WebSearcher()
    results = searcher.search("தமிழ்நாட்டு லேட்டஸ்ட் நியூஸ்", max_results=3)
    assert len(results) > 0
    for r in results:
        assert "title" in r and len(r["title"]) > 0


def test_source_processor_formatting():
    sp = SourceProcessor()
    dummy_results = [
        {
            "title": "AI Breakthrough Announced",
            "url": "https://news.example.com/ai",
            "source": "The Hindu",
            "published": "Mon, 31 Aug 2026",
            "snippet": "New AI models improve reasoning capabilities.",
        }
    ]
    formatted = sp.format_sources(dummy_results)
    assert "The Hindu" in formatted
    assert "AI Breakthrough Announced" in formatted
    assert "https://news.example.com/ai" in formatted
    assert "31 Aug 2026" in formatted


# ── 5. Grounded Prompt Generation ───────────────────────────────────────────

def test_web_search_prompt_anti_hallucination_instruction():
    prompt = web_search_response_prompt(
        user_text="What is the latest AI news?",
        search_results="SOURCE 1: Title: Gemini 2.0 Released. Source: Reuters",
        lang="en",
        current_date="Monday, August 31, 2026",
    )
    assert "Monday, August 31, 2026" in prompt
    assert "Gemini 2.0 Released" in prompt
    assert "Under NO circumstances say" in prompt
