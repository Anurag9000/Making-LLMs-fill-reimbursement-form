"""Utility helpers for JSON parsing of LLM outputs."""
from __future__ import annotations

import json
from typing import Any


def safe_json_parse(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find first/last bracket pair
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            return json.loads(snippet)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            return json.loads(snippet)
        raise
