"""
CommerceMind VoiceCare AI — Custom Exceptions and Error Constants
Centralised error definitions to avoid magic strings throughout the codebase.
"""

from typing import Optional


# ================================================================
# Custom Exception Hierarchy
# ================================================================

class VoiceCareError(Exception):
    """Base exception for all VoiceCare AI errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(VoiceCareError):
    """Input validation failed."""

    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")


class PipelineError(VoiceCareError):
    """An agent in the 9-stage pipeline encountered an unrecoverable error."""

    def __init__(self, stage: int, agent_name: str, message: str):
        self.stage = stage
        self.agent_name = agent_name
        super().__init__(
            f"Pipeline stage {stage} ({agent_name}) failed: {message}",
            code="PIPELINE_ERROR",
        )


class STTError(VoiceCareError):
    """Speech-to-Text transcription failed."""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(
            f"{provider} STT failed: {message}",
            code="STT_ERROR",
        )


class LLMError(VoiceCareError):
    """LLM call failed after all retries."""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(
            f"{provider} LLM call failed: {message}",
            code="LLM_ERROR",
        )


class DatabaseError(VoiceCareError):
    """Database operation failed."""

    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(
            f"Database {operation} failed: {message}",
            code="DATABASE_ERROR",
        )


class RateLimitError(VoiceCareError):
    """Rate limit exceeded for a specific resource."""

    def __init__(self, resource: str, retry_after_seconds: int = 60):
        self.resource = resource
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Rate limit exceeded for {resource}. Retry after {retry_after_seconds}s.",
            code="RATE_LIMIT_ERROR",
        )


class AuthError(VoiceCareError):
    """Authentication or authorisation failed."""

    def __init__(self, message: str):
        super().__init__(message, code="AUTH_ERROR")


# ================================================================
# Error Message Factory
# ================================================================

class ErrorMessages:
    """Centralised error message strings — prevents magic strings in handlers."""

    # Voice / STT
    NO_INPUT = "No audio or text input provided."
    STT_UNAVAILABLE = (
        "Voice recognition is temporarily unavailable. "
        "Please use the 'Switch to Text' option to type your query."
    )
    GROQ_KEY_MISSING = (
        "GROQ_API_KEY is not set. Please add it to your environment variables."
    )

    # Session
    INVALID_SESSION_ID = "Invalid session ID format — a new session will be created."
    SESSION_NOT_FOUND = "Session not found. A new session will be initialised."

    # Ticket
    TICKET_NOT_FOUND = "Ticket not found."
    INVALID_TICKET_ID = "Invalid ticket ID format."
    TICKET_CREATION_FAILED = "Ticket creation failed — please try again."

    # Order
    INVALID_ORDER_ID = "Invalid order ID format."
    ORDER_NOT_FOUND = "No matching order found for the provided details."

    # Rate Limiting
    RATE_LIMIT_VOICE = (
        "Too many requests. Voice queries are limited to 5 per minute per phone number. "
        "Please wait before trying again."
    )

    # Auth
    INVALID_CREDENTIALS = "Invalid admin credentials."
    DEFAULT_PASSWORD_IN_PROD = (
        "Admin password must be changed from the default value in production!"
    )

    # Generic
    INTERNAL_ERROR = (
        "An internal error occurred. Please try again or contact support."
    )

    @staticmethod
    def pipeline_stage_failed(stage: int, agent: str) -> str:
        return f"Pipeline stage {stage} ({agent}) encountered an error."

    @staticmethod
    def llm_call_failed(provider: str) -> str:
        return f"{provider} AI service failed. Using fallback response."

    @staticmethod
    def db_query_failed(table: str) -> str:
        return f"Failed to query {table}. Please try again."
