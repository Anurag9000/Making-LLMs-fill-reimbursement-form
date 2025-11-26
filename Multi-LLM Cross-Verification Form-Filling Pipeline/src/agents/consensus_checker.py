"""Consistency checker using LLM3."""
from __future__ import annotations

from config.settings import get_settings
from data_models.schemas import CandidateValue, ConsistencyReport
from services.json_utils import safe_json_parse
from services.llm_factory import resolve_llm
from services.prompt_loader import load_prompt


class ConsensusChecker:
    def __init__(self):
        self.settings = get_settings()
        self.prompt = load_prompt("consensus_checker")
        self.llm = resolve_llm(self.settings.checker_model, self.settings)

    def check(self, candidates_a: list[CandidateValue], candidates_b: list[CandidateValue]) -> list[ConsistencyReport]:
        cand_a_json = [c.model_dump() for c in candidates_a]
        cand_b_json = [c.model_dump() for c in candidates_b]
        messages = [
            {"role": "system", "content": self.prompt["system"]},
            {
                "role": "user",
                "content": self.prompt["user"]
                .replace("{{candidates_a}}", str(cand_a_json))
                .replace("{{candidates_b}}", str(cand_b_json))
                .replace("{{numeric_tolerance}}", str(self.settings.consensus.numeric_tolerance)),
            },
        ]
        resp = self.llm.invoke(messages)
        parsed = safe_json_parse(resp.content if hasattr(resp, "content") else str(resp))
        reports: list[ConsistencyReport] = []
        for item in parsed:
            reports.append(
                ConsistencyReport(
                    field_id=item.get("field_id"),
                    status=item.get("status"),
                    notes=item.get("notes"),
                    agreed_value=item.get("agreed_value"),
                )
            )
        return reports
