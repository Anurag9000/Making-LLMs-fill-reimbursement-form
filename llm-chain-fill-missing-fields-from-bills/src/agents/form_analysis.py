"""Form analysis agent that finds missing fields."""
from __future__ import annotations

from typing import Iterable, List

from config.settings import get_settings
from data_models.schemas import FormField, MissingField
from services.json_utils import safe_json_parse
from services.llm_factory import resolve_llm
from services.prompt_loader import load_prompt


class FormAnalysisAgent:
    def __init__(self):
        self.settings = get_settings()
        self.prompt = load_prompt("form_analysis")
        self.llm = resolve_llm(self.settings.form_analysis_model, self.settings)

    def analyze(self, form_structure: str) -> List[FormField]:
        messages = [
            {"role": "system", "content": self.prompt["system"]},
            {
                "role": "user",
                "content": self.prompt["user"].replace("{{form_structure}}", form_structure),
            },
        ]
        resp = self.llm.invoke(messages)
        parsed = safe_json_parse(resp.content if hasattr(resp, "content") else str(resp))
        fields: list[FormField] = []
        for item in parsed:
            fields.append(
                FormField(
                    id=item.get("id") or item.get("field", ""),
                    label=item.get("label") or item.get("name", ""),
                    value=item.get("value"),
                    is_missing=item.get("is_missing", True),
                    hint=item.get("hint"),
                )
            )
        return fields

    @staticmethod
    def missing(fields: Iterable[FormField]) -> List[MissingField]:
        return [
            MissingField(
                id=f.id,
                label=f.label,
                expected_type=None,
                hint=f.hint,
            )
            for f in fields
            if f.is_missing or f.value in (None, "")
        ]
