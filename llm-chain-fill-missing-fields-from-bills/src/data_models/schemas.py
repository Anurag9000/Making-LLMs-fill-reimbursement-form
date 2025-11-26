"""Shared data models for the pipeline."""
from __future__ import annotations

from typing import Any, List, Optional

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
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedEntity(BaseModel):
    bill_id: str
    field: str
    value: Any
    units: str | None = None
    confidence: float | None = None
    coordinates: dict[str, Any] | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


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
    status: str  # "match", "mismatch", or "unresolved"
    notes: str | None = None
    candidates: List[CandidateValue] = Field(default_factory=list)


class FillProposal(BaseModel):
    field_id: str
    proposed_value: Any
    justification: str | None = None
    confidence: float | None = None
    source_entity_ids: list[str] = Field(default_factory=list)


class FinalFormPayload(BaseModel):
    fields: list[FormField]
    audit_trail: list[str] = Field(default_factory=list)
    consistency: list[ConsistencyReport] = Field(default_factory=list)


class WorkflowState(BaseModel):
    missing_fields: list[MissingField] = Field(default_factory=list)
    candidate_set_a: list[CandidateValue] = Field(default_factory=list)
    candidate_set_b: list[CandidateValue] = Field(default_factory=list)
    proposals: list[FillProposal] = Field(default_factory=list)
    final_form: FinalFormPayload | None = None
