from datetime import date

_EXTRACTION_TEMPLATE = """\
You are an assistant that extracts actionable tasks from meeting notes or \
task descriptions.

Today's date is {reference_date}. Use it to resolve any relative dates \
mentioned in the notes (e.g. "by Friday", "next week", "tomorrow") into \
absolute ISO 8601 dates (YYYY-MM-DD).

Return ONLY a JSON array (no prose, no markdown fences). Each element must \
be an object with exactly these fields:
- "description": string, required - a concise, actionable description of the task
- "owner": string or null - the person responsible, if mentioned
- "due_date": string in "YYYY-MM-DD" format, or null - the deadline, if mentioned or inferable
- "priority": one of "LOW", "MEDIUM", "HIGH", "URGENT" - infer from urgency language, default to "MEDIUM" if unclear
- "source_text": string - the exact sentence or phrase from the notes this task was derived from

If no tasks are found, return an empty JSON array: [].

Meeting notes:
\"\"\"
{notes}
\"\"\"
"""


def build_extraction_prompt(notes: str, reference_date: date) -> str:
    """The single template used for task extraction — the only place prompt text is built."""
    return _EXTRACTION_TEMPLATE.format(reference_date=reference_date.isoformat(), notes=notes)
