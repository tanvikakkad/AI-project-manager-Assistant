"""User-facing message strings, centralized so copy changes touch one file."""

INTERNAL_ERROR_MESSAGE = "An unexpected error occurred."

# AI provider layer
GEMINI_API_KEY_MISSING_MESSAGE = "GEMINI_API_KEY is not configured"
GROQ_API_KEY_MISSING_MESSAGE = "GROQ_API_KEY is not configured"
EMPTY_AI_RESPONSE_MESSAGE = "AI provider returned an empty response"
AI_PROVIDER_EXHAUSTED_MESSAGE_TEMPLATE = "AI provider failed after {attempts} attempts"
UNSUPPORTED_AI_PROVIDER_MESSAGE_TEMPLATE = "Unsupported AI provider: {provider!r}"

# Extraction parsing/validation
AI_RESPONSE_NOT_JSON_MESSAGE = "AI response was not valid JSON"
AI_RESPONSE_NOT_ARRAY_MESSAGE = "AI response JSON must be an array of tasks"
AI_RESPONSE_INVALID_TASK_MESSAGE = "AI response contained an invalid task"

# Entity lookups
TASK_NOT_FOUND_MESSAGE_TEMPLATE = "Task {task_id} not found"
MEETING_NOT_FOUND_MESSAGE_TEMPLATE = "Meeting {meeting_id} not found"

# Meeting/notes business-rule validation
MEETING_NOTES_REQUIRED_MESSAGE = "Meeting notes are required."
MEETING_DATE_IN_FUTURE_MESSAGE = "Meeting date cannot be in the future."
MEETING_TIME_IN_FUTURE_MESSAGE = "Meeting time cannot be in the future for today's date."

# Request-level validation envelope
REQUEST_VALIDATION_ERROR_MESSAGE = "Request validation failed."
