"""Bill extraction agent parameterized by model config."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from config.settings import ModelConfig, get_settings
from data_models.schemas import BillDocument, CandidateValue, MissingField
from services.json_utils import safe_json_parse
from services.llm_factory import resolve_llm
from services.ocr import extract_text_auto
from services.prompt_loader import load_prompt


class BillExtractor:
    def __init__(self, model_config: ModelConfig | None = None):
        self.settings = get_settings()
        self.prompt = load_prompt("bill_extractor")
        model = model_config or self.settings.extractor_model_a
        self.llm = resolve_llm(model, self.settings)

    def _make_bill(self, path: str | Path) -> BillDocument:
        text = extract_text_auto(path)
        return BillDocument(id=Path(path).stem, source_path=str(path), text=text)

    def process_directory(self, bills_dir: str | Path, missing_fields: Iterable[MissingField]) -> list[CandidateValue]:
        bills_dir = Path(bills_dir)
        missing_fields_json = json.dumps([mf.model_dump() for mf in missing_fields])
        all_candidates: list[CandidateValue] = []
        for bill_path in bills_dir.iterdir():
            if bill_path.is_file():
                bill = self._make_bill(bill_path)
                all_candidates.extend(self.process_bill(bill, missing_fields_json))
        return all_candidates

    def process_bill(self, bill: BillDocument, missing_fields_json: str) -> list[CandidateValue]:
        messages = [
            {"role": "system", "content": self.prompt["system"]},
            {
                "role": "user",
                "content": self.prompt["user"]
                .replace("{{bill_text}}", bill.text or "")
                .replace("{{target_fields}}", missing_fields_json),
            },
        ]
        resp = self.llm.invoke(messages)
        parsed = safe_json_parse(resp.content if hasattr(resp, "content") else str(resp))
        candidates: list[CandidateValue] = []
        for item in parsed:
            candidates.append(
                CandidateValue(
                    field_id=item.get("field_id") or item.get("field"),
                    value=item.get("value"),
                    units=item.get("units"),
                    confidence=item.get("confidence"),
                    source_bill=bill.id,
                    justification=item.get("justification"),
                    calc_steps=item.get("calc_steps") or [],
                )
            )
        return candidates
