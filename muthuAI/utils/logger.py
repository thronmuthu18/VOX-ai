"""
MuthuAI Phase 2 — utils/logger.py
Centralised logger with rotating file handler.
Never logs API keys or credentials.
"""

from __future__ import annotations
import re
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Redact anything that looks like an API key in log output
_REDACT_RE = re.compile(r"AIza[A-Za-z0-9_\-]{35}", re.ASCII)


class _Redactor(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _REDACT_RE.sub("***API_KEY***", str(record.msg))
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    _REDACT_RE.sub("***API_KEY***", str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: (_REDACT_RE.sub("***API_KEY***", str(v)) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
        return True


_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE = "%Y-%m-%d %H:%M:%S"
_initialized: dict[str, logging.Logger] = {}


def get_logger(name: str = "muthuai") -> logging.Logger:
    """
    Return a named logger with rotating file + console handlers.
    """
    if name in _initialized:
        return _initialized[name]

    from config.settings import LOG_LEVEL, LOG_DIR

    log_file = Path(LOG_DIR) / "muthuai.log"
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    fmt = logging.Formatter(_FMT, datefmt=_DATE)
    redactor = _Redactor()

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.addFilter(redactor)
    logger.addHandler(ch)

    # Rotating file handler (5 MB × 3 files)
    fh = RotatingFileHandler(log_file, maxBytes=5_242_880, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.addFilter(redactor)
    logger.addHandler(fh)

    logger.propagate = False
    _initialized[name] = logger
    return logger
