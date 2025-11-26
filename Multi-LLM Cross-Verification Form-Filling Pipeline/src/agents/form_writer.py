"""Form writer using LLM4 to produce filled form JSON."""
from __future__ import annotations

from config.settings import get_settings
from data_models.schemas import FinalFormPayload, FillProposal, FormField
from services.json_utils import safe_json_parse
from services.llm_factory import resolve_llm
from services.prompt_loader import load_prompt


class FormWriter:
    def __init__(self):
        self.settings = get_settings()
        self.prompt = load_prompt("form_writer")
        self.llm = resolve_llm(self.settings.writer_model, self.settings)

    def write(self, fields: list[FormField], proposals: list[FillProposal]) -> FinalFormPayload:
        fields_json = [f.model_dump() for f in fields]
        props_json = [p.model_dump() for p in proposals]
        messages = [
            {"role": "system", "content": self.prompt["system"]},
            {
                "role": "user",
                "content": self.prompt["user"]
                .replace("{{form_fields}}", str(fields_json))
                .replace("{{approved_values}}", str(props_json)),
            },
        ]
        resp = self.llm.invoke(messages)
        parsed = safe_json_parse(resp.content if hasattr(resp, "content") else str(resp))
        # Expecting {"fields": [...], "audit": [..]} but tolerate array
        if isinstance(parsed, dict) and "fields" in parsed:
            updated_fields = [FormField(**f) for f in parsed.get("fields", [])]
            audit = parsed.get("audit", []) or []
        elif isinstance(parsed, list):
            updated_fields = [FormField(**f) for f in parsed]
            audit = []
        else:
            updated_fields = fields
            audit = []
        return FinalFormPayload(fields=updated_fields, audit_trail=[str(a) for a in audit])
