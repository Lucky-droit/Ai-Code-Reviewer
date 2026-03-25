import json
import re
from typing import Any


class ParseError(ValueError):
    """Raised when model output cannot be converted into valid JSON."""


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ParseError("No JSON object found in model output.")

    depth = 0
    in_string = False
    escape = False

    for i, char in enumerate(text[start:], start=start):
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
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    raise ParseError("JSON object appears incomplete.")


def parse_review_json(raw_text: str) -> dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise ParseError("Model output was empty.")

    candidate = _strip_code_fences(raw_text)
    candidate = re.sub(r"^json\s*", "", candidate, flags=re.IGNORECASE).strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    extracted = _extract_first_json_object(candidate)
    try:
        return json.loads(extracted)
    except json.JSONDecodeError as exc:
        raise ParseError(f"Failed to decode JSON: {exc.msg}") from exc