"""Reconciliation agent for matching candidate values and proposing fills."""
from __future__ import annotations

from typing import Dict, List

from config.settings import get_settings
from data_models.schemas import CandidateValue, ConsistencyReport, FillProposal, MissingField
from services.json_utils import safe_json_parse
from services.llm_factory import resolve_llm
from services.prompt_loader import load_prompt


def _to_key(field_id: str | None) -> str:
    return (field_id or "").lower()


class Reconciler:
    def __init__(self):
        self.settings = get_settings()
        self.prompt = load_prompt("reconciler")
        self.llm = resolve_llm(self.settings.reconciler_model, self.settings)

    def reconcile(self, candidates_a: List[CandidateValue], candidates_b: List[CandidateValue]) -> List[ConsistencyReport]:
        candidates_a_json = [c.model_dump() for c in candidates_a]
        candidates_b_json = [c.model_dump() for c in candidates_b]
        messages = [
            {"role": "system", "content": self.prompt["system"]},
            {
                "role": "user",
                "content": self.prompt["user"]
                .replace("{{candidates_a}}", str(candidates_a_json))
                .replace("{{candidates_b}}", str(candidates_b_json))
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
                    candidates=[],
                )
            )
        return reports

    def propose(self, reports: List[ConsistencyReport], candidates_a: List[CandidateValue], candidates_b: List[CandidateValue]) -> List[FillProposal]:
        by_field: Dict[str, list[CandidateValue]] = {}
        for cand in candidates_a + candidates_b:
            by_field.setdefault(_to_key(cand.field_id), []).append(cand)

        proposals: list[FillProposal] = []
        for report in reports:
            key = _to_key(report.field_id)
            cands = by_field.get(key, [])
            if report.status == "match" and cands:
                # Pick highest confidence
                best = sorted(
                    cands,
                    key=lambda c: (c.confidence or 0, -len(c.justification or "")),
                    reverse=True,
                )[0]
                proposals.append(
                    FillProposal(
                        field_id=report.field_id,
                        proposed_value=best.value,
                        justification=best.justification,
                        confidence=best.confidence,
                        source_entity_ids=[best.source_bill] if best.source_bill else [],
                    )
                )
        return proposals
