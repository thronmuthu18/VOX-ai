"""
MuthuAI — voice/language_detector.py
Production 4-tier language detection for English, Tamil, and natural Tanglish.

Priority Order:
1. Explicit user language instruction ("in English", "தமிழ்ல சொல்லு", "Tanglish-la", etc.)
2. Language / script / style of the current utterance
3. Recent conversational context language (for short/ambiguous queries like 'yes', 'ok')
4. Configured default fallback language
"""

from __future__ import annotations
import re
from utils.helpers import contains_tamil, contains_english
from utils.logger import get_logger

log = get_logger("muthuai.language_detector")

# Priority 1: Explicit language override patterns
_EXPLICIT_ENGLISH_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(in english|english-?la|englishil|ஆங்கிலத்தில்|speak in english|answer in english|reply in english|explain (?:this )?in english|tell me in english)\b", re.I),
    re.compile(r"(?:answer|reply|explain|tell|speak).*?\b(in english|english-?la)\b", re.I),
    re.compile(r"(?:தமிழ்ல|tamil-?la).*?(?:english-?la|in english)", re.I),
]

_EXPLICIT_TAMIL_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(in tamil|tamil-?la|தமிழில்|தமிழ்ல|தமிழ் மொழியில்|speak in tamil|answer in tamil|reply in tamil|explain (?:this )?in tamil|tell me in tamil)\b", re.I),
    re.compile(r"(?:answer|reply|explain|tell|speak|solli|sollu|explain\s+pannu).*?\b(in tamil|tamil-?la|தமிழ்ல)\b", re.I),
    re.compile(r"தமிழ்ல\s+(?:சொல்லு|சொல்|விளக்கு|விவரி|explain)", re.I),
    re.compile(r"இதை\s+தமிழ்ல", re.I),
]

_EXPLICIT_TANGLISH_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(in tanglish|tanglish-?la|டங்கிலிஷ்|டங்லீஷ்|speak in tanglish|answer in tanglish|explain (?:this )?in tanglish)\b", re.I),
    re.compile(r"(?:explain|solli|sollu|explain\s+pannu).*?\b(in tanglish|tanglish-?la)\b", re.I),
]

# Priority 2: Tanglish lexical & suffix markers
_TANGLISH_LATIN_WORDS = re.compile(
    r"\b(panni|pannunga|pannrom|pannu|pannidunga|solu|sollu|solren|vandhutom|"
    r"paa|paaru|paarunga|edhu|enna|eppo|ethanai|ippo|inga|ange|"
    r"adhu|idhu|unga|nalla|theriyuma|puriyuthu|ketku|podu|vaa|po|"
    r"va|la|nu|da|di|seri|illai|aamaa|illaam|konjam|romba|"
    r"summa|neenga|apdiye|ithu|kitu|maari|mathiri|kaanom|teriyum|"
    r"vendam|vendum|irukku|iruka|irukkanga|kaathu|kelunga|"
    r"enna-?na|adhu-?na|idhu-?na|epdi|eppadi|apdi|appadi|enna-?nu|"
    r"solunga|pannalam|panlaam|seiyanum|mudiyum|mudiyuma|kudukka|"
    r"pathu|paathutu|vaanga|ponga|kitta|kooda|mattum|thara|tharen)\b",
    re.IGNORECASE,
)

_LATIN_TANGLISH_SUFFIX = re.compile(
    r"\b[A-Za-z]+-(?:na|la|oda|kku|ukku|lerundhu|ilirundhu|a|ah|nu|da|di)\b",
    re.IGNORECASE,
)

_MIXED_SCRIPT_SUFFIX = re.compile(
    r"\b[A-Za-z]+-(?:ஐ|ஆ|ல|னா|க்கு|லிருந்து|ஓட|தான்)\b|\b[A-Za-z]+(?:-ஐ|-ஆ|-ல|-னா|-க்கு|-லிருந்து)\b"
)

_TAMIL_FORMAL_GRAMMAR = re.compile(
    r"(?:என்றால்\s+என்ன|பற்றி\s+கூறு|விளக்கு|விளக்குக|என்றால்\s+என்னவென்று|சொல்லு|சொல்|தெரியுமா|என்ன\s*\?|விவரி)"
)


def has_tamil_script(text: str) -> bool:
    """Return True if text contains Tamil Unicode script (U+0B80..U+0BFF)."""
    return bool(re.search(r"[\u0B80-\u0BFF]", text))


def has_latin_script(text: str) -> bool:
    """Return True if text contains Latin alphabetic characters."""
    return bool(re.search(r"[A-Za-z]", text))


def detect_language(text: str, context_lang: str | None = None) -> str:
    """
    Detect the intended response language and style of the user utterance.

    Returns:
        "en"       — English
        "ta"       — Tamil (formal/standard)
        "tanglish" — Tanglish (Tamil-English conversational code-mixed style)
    """
    if not text or not text.strip():
        return context_lang or "en"

    cleaned = text.strip()

    # ── Priority 1: Explicit Override ────────────────────────
    for pattern in _EXPLICIT_ENGLISH_PATTERNS:
        if pattern.search(cleaned):
            log.debug("Language explicitly overridden to English for: %r", text)
            return "en"

    for pattern in _EXPLICIT_TAMIL_PATTERNS:
        if pattern.search(cleaned):
            log.debug("Language explicitly overridden to Tamil for: %r", text)
            return "ta"

    for pattern in _EXPLICIT_TANGLISH_PATTERNS:
        if pattern.search(cleaned):
            log.debug("Language explicitly overridden to Tanglish for: %r", text)
            return "tanglish"

    # ── Priority 2: Script and Linguistic Markers ────────────
    has_ta = has_tamil_script(cleaned)
    has_en = has_latin_script(cleaned)

    # 2A: Mixed Script (Tamil Unicode + English Latin)
    if has_ta and has_en:
        if _LATIN_TANGLISH_SUFFIX.search(cleaned) or _MIXED_SCRIPT_SUFFIX.search(cleaned):
            log.debug("Language detected: Tanglish (mixed suffixes) for: %r", text)
            return "tanglish"
        if re.search(r"(?:பண்ணு|பண்ணுங்க|சொல்லு|சொல்லுங்க|என்னன்னு|பாரு|பார்த்து)", cleaned):
            log.debug("Language detected: Tanglish (colloquial Tamil in mixed script) for: %r", text)
            return "tanglish"
        if _TAMIL_FORMAL_GRAMMAR.search(cleaned):
            log.debug("Language detected: Tamil (Tamil grammar with English noun) for: %r", text)
            return "ta"
        tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", cleaned))
        if tamil_chars >= 6 and not _LATIN_TANGLISH_SUFFIX.search(cleaned):
            return "ta"
        return "tanglish"

    # 2B: Pure Tamil Unicode Script
    if has_ta and not has_en:
        log.debug("Language detected: Tamil (Unicode script) for: %r", text)
        return "ta"

    # 2C: Pure Latin Script
    if has_en and not has_ta:
        if _LATIN_TANGLISH_SUFFIX.search(cleaned) or _TANGLISH_LATIN_WORDS.search(cleaned):
            log.debug("Language detected: Tanglish (Romanised Tamil) for: %r", text)
            return "tanglish"

        # Short generic tokens use conversational context if available
        lower_token = cleaned.lower().strip(" ,.-!?")
        if lower_token in {"yes", "no", "ok", "okay", "next", "continue", "stop", "sure", "fine"} and context_lang:
            log.debug("Ambiguous short token %r inheriting context language %s", text, context_lang)
            return context_lang

        log.debug("Language detected: English for: %r", text)
        return "en"

    # ── Priority 3 & 4: Context / Default Fallback ───────────
    return context_lang or "en"


def get_language_prompt_instruction(detected_lang: str) -> str:
    """
    Generate the prompt instruction string for Gemini response generation.
    """
    if detected_lang == "en":
        return "Respond in clear, natural English."
    elif detected_lang == "ta":
        return (
            "Respond in natural, modern Tamil (தமிழ்). Keep the explanation clear and conversational. "
            "You may preserve standard technical English terms (like 'machine learning', 'function', 'database') "
            "in English if it improves clarity."
        )
    elif detected_lang == "tanglish":
        return (
            "Respond in natural, conversational Tanglish (Tamil-English code-mixed spoken style, e.g. "
            "'Recursion-na ஒரு function தன்னையே மீண்டும் call பண்ணிக்கிற concept'). "
            "Do NOT translate into awkward, ancient, or overly formal textbook Tamil. "
            "Preserve technical English keywords and speak like a friendly bilingual engineer."
        )
    return "Respond in clear, natural English."


def response_language_code(detected_lang: str) -> str:
    """
    Map detected language to BCP-47 code for voice/TTS compatibility.
    """
    if detected_lang in ("ta", "tanglish"):
        return "ta-IN"
    return "en-IN"

