"""Utilities for selecting best candidates and building proposals."""
from __future__ import annotations

from typing import List

from data_models.schemas import CandidateValue, ConsistencyReport, FillProposal


def build_proposals(reports: List[ConsistencyReport], candidates_a: List[CandidateValue], candidates_b: List[CandidateValue]) -> List[FillProposal]:
    proposals: list[FillProposal] = []
    by_field: dict[str, list[CandidateValue]] = {}
    for cand in candidates_a + candidates_b:
        key = (cand.field_id or "").lower()
        by_field.setdefault(key, []).append(cand)

    for report in reports:
        if report.status != "match":
            continue
        key = (report.field_id or "").lower()
        cands = by_field.get(key, [])
        if not cands:
            continue
        best = sorted(cands, key=lambda c: (c.confidence or 0, -len(c.justification or "")), reverse=True)[0]
        proposals.append(
            FillProposal(
                field_id=report.field_id,
                proposed_value=report.agreed_value if report.agreed_value is not None else best.value,
                justification=best.justification,
                confidence=best.confidence,
                sources=[best.source_bill] if best.source_bill else [],
            )
        )
    return proposals
