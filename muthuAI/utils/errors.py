"""
MuthuAI — utils/errors.py
Custom exception hierarchy for clean error handling across all modules.
"""


class MuthuAIError(Exception):
    """Base exception for all MuthuAI errors."""

    def __init__(self, message: str, recoverable: bool = True):
        super().__init__(message)
        self.recoverable = recoverable  # True → agent speaks error and continues


class VoiceError(MuthuAIError):
    """Raised for microphone / speech recognition failures."""


class RecognitionError(VoiceError):
    """Speech could not be recognised (noise, silence, ambiguous)."""


class TTSError(MuthuAIError):
    """Raised when text-to-speech synthesis or playback fails."""


class GeminiError(MuthuAIError):
    """Raised for Gemini API failures."""


class GeminiRateLimitError(GeminiError):
    """API rate limit exceeded — retryable."""


class GeminiAuthError(GeminiError):
    """Invalid API key or authentication failure — not recoverable."""

    def __init__(self, message: str):
        super().__init__(message, recoverable=False)


class PlannerError(MuthuAIError):
    """Raised when the planner cannot parse a tool plan from Gemini."""


class ToolError(MuthuAIError):
    """Raised by any tool during execution."""


class ToolNotFoundError(ToolError):
    """Requested tool is not registered."""


class ToolValidationError(ToolError):
    """Tool parameters failed validation."""


class ToolPermissionError(ToolError):
    """Tool action was denied by the permission/safety layer."""


class ApplicationNotFoundError(ToolError):
    """Target application executable was not found on this system."""


class FileOperationError(ToolError):
    """File or folder operation failed."""


class BrowserError(ToolError):
    """Browser automation failure."""


class RAGError(MuthuAIError):
    """Raised for RAG pipeline failures (ingestion, embedding, retrieval)."""


class RetrievalError(MuthuAIError):
    """Web retrieval or source processing failure."""


class MemoryError(MuthuAIError):
    """Memory read/write failure."""


class ConfirmationTimeout(MuthuAIError):
    """User did not confirm a dangerous action within the timeout."""
