"""Shared JSON extraction utilities for parsing LLM responses.

LLM responses often wrap JSON in prose or Markdown fences. These helpers
locate and parse the first balanced ``{...}`` object from arbitrary text.
"""

import json
from typing import Any, Dict, Optional

from insighthub.errors import LLMProcessingError


def extract_first_json_object(text: str) -> Optional[str]:
    """Return the first balanced top-level ``{...}`` object found in *text*.

    A depth counter scans for ``{`` / ``}`` while respecting string literals
    (including escaped quotes). This is more robust than a greedy regex when the
    LLM wraps the JSON in prose, includes multiple objects, or emits comments.
    Returns ``None`` if no balanced object is found.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def parse_json_object(text: str, *, source_label: str = "LLM") -> Dict[str, Any]:
    """Parse a JSON object from text, extracting it if necessary.

    Args:
        text: Raw text that should contain a JSON object.
        source_label: Human-readable label for error messages (e.g. "scoring",
            "editorial step").

    Returns:
        Parsed dictionary.

    Raises:
        LLMProcessingError: If no valid JSON object can be extracted.
    """
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    extracted = extract_first_json_object(text)
    if extracted is None:
        raise LLMProcessingError(f"Expected JSON object from {source_label}, got: {text[:500]}")
    try:
        data = json.loads(extracted)
    except json.JSONDecodeError as e:
        raise LLMProcessingError(f"Invalid JSON from {source_label}: {text[:500]}") from e
    if not isinstance(data, dict):
        raise LLMProcessingError(f"Expected JSON object from {source_label}.")
    return data
