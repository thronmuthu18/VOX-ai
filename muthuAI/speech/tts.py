"""
CHAMP Production TTS Engine — speech/tts.py

High-Quality Text-to-Speech using Microsoft Edge TTS with:
- Persistent background asyncio worker loop (eliminates 'Event loop is closed' errors on Windows)
- Language-aware voice selection (Tamil: PallaviNeural, English: NeerjaExpressiveNeural, Tanglish)
- Speech-friendly text normalization: strips markdown headers, bullet points, code blocks, URLs, emojis
- Sentence-boundary chunking: natural flow without artificial mid-sentence pauses
- Pipelined parallel synthesis: synthesizes next sentences while previous sentence is playing (zero gap)
- Instant sub-10ms barge-in and cancellation support
- Thread-safe is_speaking() state polling for microphone VAD echo gating
- Configurable speech rate (+12% default) for natural conversational pacing
"""

from __future__ import annotations
import sys
import asyncio
import re
import tempfile
import threading
import time
import queue
from pathlib import Path
from typing import TypedDict

import edge_tts
import pygame

from config.settings import (
    TTS_VOICE_TAMIL,
    TTS_VOICE_ENGLISH,
    TTS_RATE,
    TTS_VOLUME,
    TTS_PITCH,
)
from voice.language_detector import detect_language, has_tamil_script
from utils.logger import get_logger

log = get_logger("muthuai.tts")

# ── Initialise pygame mixer once ──────────────────────────────────
_mixer_ok = False
try:
    # 24000 Hz matches Edge TTS native output rate — avoids resampling artefacts
    pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
    _mixer_ok = True
    log.info("pygame mixer initialised at 24kHz.")
except Exception as _exc:
    log.warning("pygame mixer init failed (%s). Audio playback disabled.", _exc)


class TTSDiagnostics(TypedDict):
    text: str
    normalized_text: str
    voice: str
    rate: str
    detected_lang: str
    sentence_count: int
    first_chunk_latency_ms: float
    total_synthesis_ms: float
    total_playback_ms: float
    interrupted: bool


# ── Persistent Background Worker for Async Edge TTS ────────────────
class _BackgroundTTSWorker:
    """
    Dedicated worker thread with a persistent asyncio event loop.
    Avoids repeatedly creating and closing event loops on Windows,
    which triggers Proactor pipe transport closed errors.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._start_worker()

    def _start_worker(self) -> None:
        def _runner() -> None:
            # Use Selector event loop on Windows for TTS thread's non-blocking network I/O
            # without mutating the global process policy which breaks Playwright subprocesses
            selector_cls = getattr(asyncio, "SelectorEventLoop", None)
            if sys.platform == "win32" and selector_cls is not None:
                try:
                    import selectors
                    self._loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
                except Exception:
                    self._loop = asyncio.new_event_loop()
            else:
                self._loop = asyncio.new_event_loop()

            asyncio.set_event_loop(self._loop)
            self._ready.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=_runner, name="TTS-AsyncWorker", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5.0)
        log.info("BackgroundTTSWorker thread started successfully.")

    def synthesize(
        self,
        text: str,
        voice: str,
        rate: str,
        volume: str,
        pitch: str,
        output_path: Path,
        timeout: float = 15.0,
    ) -> None:
        """Execute Edge TTS communicate.save() inside the persistent worker loop."""
        if self._loop is None or not self._loop.is_running():
            raise RuntimeError("TTS worker event loop is not running.")

        async def _async_synthesize() -> None:
            comm = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=pitch,
            )
            await comm.save(str(output_path))

        future = asyncio.run_coroutine_threadsafe(_async_synthesize(), self._loop)
        future.result(timeout=timeout)


_worker = _BackgroundTTSWorker()


def _run_async_synthesis(text: str, voice: str, output_path: Path) -> None:
    """Helper to synthesize text directly to file via background TTS worker."""
    _worker.synthesize(text, voice, TTS_RATE, TTS_VOLUME, TTS_PITCH, output_path)


# ── Voice Selection Logic ──────────────────────────────────────────
def _pick_voice(text: str) -> str:
    """
    Select the most natural TTS voice based on text content and script.

    - Tamil Unicode script or Tamil language -> TTS_VOICE_TAMIL (ta-IN-PallaviNeural)
    - Pure English or Latin script -> TTS_VOICE_ENGLISH (en-IN-NeerjaExpressiveNeural)
    - Tanglish:
        - If Tamil script is used: Tamil voice
        - If Latin script is used: Indian English Expressive voice (pronounces Tanglish naturally)
    """
    lang = detect_language(text)
    has_ta = has_tamil_script(text)

    if lang == "ta" or has_ta:
        voice = TTS_VOICE_TAMIL
        log.debug("TTS voice selected: Tamil (%s) for text snippet: %r", voice, text[:50])
    else:
        voice = TTS_VOICE_ENGLISH
        log.debug("TTS voice selected: English (%s) for text snippet: %r", voice, text[:50])
    return voice


# ── Text Normalization for Natural Speech ──────────────────────────
_MARKDOWN_HEADER_RE = re.compile(r"^#+\s+", re.MULTILINE)
_MARKDOWN_BULLET_RE = re.compile(r"^\s*[-*•]\s+", re.MULTILINE)
_MARKDOWN_FORMAT_RE = re.compile(r"(\*\*|\*|__|_|`|~~)")
_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RE = re.compile(r"`[^`]+`")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_EMOJI_RE = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
_PAUSE_DASH_RE = re.compile(r"\s*[—–]\s*")
_ELLIPSIS_RE = re.compile(r"\.{2,}")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{2,}")


def _normalize_for_tts(text: str) -> str:
    """
    Transform raw LLM output into clean, spoken-friendly text:
    - Strips code blocks, URLs, markdown syntax, bullet points, headers
    - Collapses dashes, ellipses, and excessive punctuation
    - Removes emojis that trigger abnormal TTS pronunciation
    """
    if not text:
        return ""

    t = _CODE_BLOCK_RE.sub(" ", text)
    t = _INLINE_CODE_RE.sub(" ", t)
    t = _URL_RE.sub(" ", t)
    t = _MARKDOWN_HEADER_RE.sub("", t)
    t = _MARKDOWN_BULLET_RE.sub("", t)
    t = _MARKDOWN_FORMAT_RE.sub("", t)
    t = _EMOJI_RE.sub("", t)
    t = _PAUSE_DASH_RE.sub(", ", t)
    t = _ELLIPSIS_RE.sub(".", t)
    t = _MULTI_SPACE_RE.sub(" ", t)
    t = _MULTI_NEWLINE_RE.sub(". ", t)

    # Clean leading numbering like "1. ", "2) "
    t = re.sub(r"^\s*\d+[\.\)]\s*", "", t, flags=re.MULTILINE)

    return t.strip()


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text on natural sentence boundaries (. ! ? । \n).
    Keeps sentences intact; does NOT chop mid-thought on commas.
    """
    cleaned = text.strip()
    if not cleaned:
        return []

    # Split on sentence ending punctuation followed by whitespace or end of string
    raw_sentences = re.split(r"(?<=[.!?।])\s+|\n+", cleaned)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    # If splitting produced nothing (e.g. no punctuation), return full text
    if not sentences:
        return [cleaned]

    return sentences


# ── Cancellable TTS Player with Pipelined Playback ─────────────────
class CancellableTTSPlayer:
    """
    Thread-safe, interruptible TTS Player for CHAMP Real-Time Voice Engine.

    Architecture:
    - Producer thread: Pre-fetches / synthesizes sentence chunks in background
    - Consumer thread: Plays audio chunks sequentially as soon as they become available
    - Seamless flow: 0ms dead gap between sentences
    - Immediate barge-in / cancellation
    """

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._speaking = False
        self._last_diag: TTSDiagnostics | None = None

    def is_speaking(self) -> bool:
        """Return True if TTS audio is actively playing."""
        with self._lock:
            if not self._speaking:
                return False
        if not _mixer_ok:
            return False
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False

    def stop(self) -> None:
        """Stop current speech playback immediately."""
        self.cancel()

    def cancel(self) -> None:
        """Cancel current speech, stop audio playback, and clear queues."""
        self._stop_event.set()
        if _mixer_ok:
            try:
                pygame.mixer.music.stop()
                try:
                    pygame.mixer.music.unload()
                except AttributeError:
                    pass
            except Exception as exc:
                log.debug("Error stopping pygame mixer: %s", exc)
        with self._lock:
            self._speaking = False
        log.info("CancellableTTSPlayer: Speech cancelled immediately (barge-in triggered).")

    def _play_single_file(self, audio_path: Path) -> bool:
        """
        Play a single MP3 file.
        Polls for completion or barge-in interruption.
        Returns True if played to end, False if interrupted.
        """
        if self._stop_event.is_set():
            return False
        try:
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                time.sleep(0.01)  # 10ms polling interval for sub-10ms barge-in response
            if self._stop_event.is_set():
                pygame.mixer.music.stop()
                log.info("TTS playback interrupted by barge-in.")
                return False
            try:
                pygame.mixer.music.unload()
            except AttributeError:
                pass
            return True
        except Exception as exc:
            log.error("TTS audio playback error for %s: %s", audio_path, exc)
            return False

    def speak(self, text: str) -> None:
        """
        Synthesise and speak text with seamless sentence-pipelined playback.
        """
        if not text or not text.strip():
            return

        if not _mixer_ok:
            log.warning("TTS playback skipped — pygame mixer not available.")
            return

        start_time = time.perf_counter()
        self._stop_event.clear()
        with self._lock:
            self._speaking = True

        norm_text = _normalize_for_tts(text)
        if not norm_text:
            with self._lock:
                self._speaking = False
            return

        voice = _pick_voice(norm_text)
        detected_lang = detect_language(norm_text)
        sentences = _split_into_sentences(norm_text)

        log.info(
            "TTS Starting speak (voice=%s, rate=%s, lang=%s, sentences=%d): %r",
            voice, TTS_RATE, detected_lang, len(sentences), norm_text[:80]
        )

        audio_queue: queue.Queue[tuple[int, Path | None, Exception | None]] = queue.Queue()
        temp_files: list[Path] = []
        first_audio_time: float | None = None
        interrupted = False

        # ── Producer: Background Synthesis Worker ─────────────────
        def _synthesis_producer() -> None:
            for idx, sent in enumerate(sentences):
                if self._stop_event.is_set():
                    break
                try:
                    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                    tmp.close()
                    p = Path(tmp.name)
                    temp_files.append(p)

                    _worker.synthesize(
                        text=sent,
                        voice=voice,
                        rate=TTS_RATE,
                        volume=TTS_VOLUME,
                        pitch=TTS_PITCH,
                        output_path=p,
                    )
                    audio_queue.put((idx, p, None))
                except Exception as exc:
                    log.warning("Synthesis error for sentence %d (%r): %s", idx, sent[:40], exc)
                    audio_queue.put((idx, None, exc))

            # Sentinel to mark completion
            audio_queue.put((-1, None, None))

        producer_thread = threading.Thread(target=_synthesis_producer, name="TTS-Producer", daemon=True)
        producer_thread.start()

        # ── Consumer: Playback Loop ───────────────────────────────
        try:
            played_count = 0
            while played_count < len(sentences) and not self._stop_event.is_set():
                try:
                    idx, chunk_path, exc = audio_queue.get(timeout=10.0)
                except queue.Empty:
                    log.warning("TTS audio queue timed out waiting for synthesis.")
                    break

                if idx == -1:  # End of queue
                    break

                if chunk_path is not None and chunk_path.exists():
                    if first_audio_time is None:
                        first_audio_time = (time.perf_counter() - start_time) * 1000.0
                        log.debug("TTS First-Audio Latency: %.1fms", first_audio_time)

                    completed = self._play_single_file(chunk_path)
                    if not completed:
                        interrupted = True
                        break

                played_count += 1

            if self._stop_event.is_set():
                interrupted = True

        except Exception as exc:
            log.error("TTS speak() playback error: %s", exc)
        finally:
            with self._lock:
                self._speaking = False

            total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self._last_diag = {
                "text": text,
                "normalized_text": norm_text,
                "voice": voice,
                "rate": TTS_RATE,
                "detected_lang": detected_lang,
                "sentence_count": len(sentences),
                "first_chunk_latency_ms": first_audio_time or 0.0,
                "total_synthesis_ms": 0.0,
                "total_playback_ms": total_elapsed_ms,
                "interrupted": interrupted,
            }

            log.info(
                "TTS speak finished in %.1fms (first_audio=%.1fms, interrupted=%s)",
                total_elapsed_ms, first_audio_time or 0.0, interrupted
            )

            # Cleanup all temporary MP3 files safely
            for f in temp_files:
                try:
                    f.unlink(missing_ok=True)
                except Exception as _e:
                    log.debug("Temp file cleanup deferred: %s", _e)

    def get_last_diagnostics(self) -> TTSDiagnostics | None:
        """Return metrics of the last speak() invocation."""
        return self._last_diag


# ── Global Singleton Instance & Public API ─────────────────────────
_player = CancellableTTSPlayer()


def speak(text: str) -> None:
    """Synthesise and speak text. Blocks until finished or cancelled."""
    _player.speak(text)


def stop() -> None:
    """Stop active TTS playback immediately."""
    _player.stop()


def stop_speaking() -> None:
    """Alias for stop() for voice_manager compatibility."""
    _player.stop()


def cancel() -> None:
    """Cancel active TTS playback immediately."""
    _player.cancel()


def is_speaking() -> bool:
    """Return True if TTS audio is currently playing."""
    return _player.is_speaking()


def get_voice_for_text(text: str) -> str:
    """Return the voice that would be selected for the given text."""
    norm = _normalize_for_tts(text)
    return _pick_voice(norm)


def get_tts_config() -> dict:
    """Return current TTS configuration as a dictionary."""
    return {
        "voice_tamil": TTS_VOICE_TAMIL,
        "voice_english": TTS_VOICE_ENGLISH,
        "rate": TTS_RATE,
        "volume": TTS_VOLUME,
        "pitch": TTS_PITCH,
        "mixer_ok": _mixer_ok,
    }


def get_last_diagnostics() -> TTSDiagnostics | None:
    """Return diagnostic telemetry from the last synthesis/playback."""
    return _player.get_last_diagnostics()

