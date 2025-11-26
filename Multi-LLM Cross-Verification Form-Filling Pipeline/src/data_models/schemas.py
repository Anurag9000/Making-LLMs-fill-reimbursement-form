"""Shared data models for the cross-verification pipeline."""
from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, Field


class MissingField(BaseModel):
    id: str
    label: str
    expected_type: str | None = None
    hint: str | None = None


class FormField(BaseModel):
    id: str
    label: str
    value: Any | None = None
    is_missing: bool = False
    hint: str | None = None


class BillDocument(BaseModel):
    id: str
    source_path: str
    text: str | None = None
    metadata: dict = Field(default_factory=dict)


class CandidateValue(BaseModel):
    field_id: str
    value: Any
    units: str | None = None
    confidence: float | None = None
    source_bill: str | None = None
    justification: str | None = None
    calc_steps: list[str] = Field(default_factory=list)


class ConsistencyReport(BaseModel):
    field_id: str
    status: str  # match | mismatch | unresolved
    notes: str | None = None
    agreed_value: Any | None = None


class FillProposal(BaseModel):
    field_id: str
    proposed_value: Any | None = None
    justification: str | None = None
    confidence: float | None = None
    sources: list[str] = Field(default_factory=list)


class FinalFormPayload(BaseModel):
    fields: list[FormField]
    audit_trail: list[str] = Field(default_factory=list)
    consistency: list[ConsistencyReport] = Field(default_factory=list)


class WorkflowState(BaseModel):
    missing_fields: list[MissingField] = Field(default_factory=list)
    candidates_a: list[CandidateValue] = Field(default_factory=list)
    candidates_b: list[CandidateValue] = Field(default_factory=list)
    consistency: list[ConsistencyReport] = Field(default_factory=list)
    proposals: list[FillProposal] = Field(default_factory=list)
    final_form: FinalFormPayload | None = None
