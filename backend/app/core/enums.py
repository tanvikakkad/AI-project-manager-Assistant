from enum import StrEnum


class TaskStatus(StrEnum):
    """Lifecycle status of a task. Always app-assigned, never LLM-inferred."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskPriority(StrEnum):
    """Priority inferred by the LLM at extraction time, editable afterwards."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ProcessingStatus(StrEnum):
    """Lifecycle status of a meeting's task-extraction pipeline."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AIProviderName(StrEnum):
    """Supported AI provider identifiers — the only valid `AI_PROVIDER` values."""

    GEMINI = "gemini"
    GROQ = "groq"
