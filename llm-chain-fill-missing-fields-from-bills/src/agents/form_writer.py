"""Applies fill proposals to form fields and generates audit trail."""
from __future__ import annotations

from typing import List

from data_models.schemas import FinalFormPayload, FillProposal, FormField


class FormWriter:
    def apply(self, fields: List[FormField], proposals: List[FillProposal]) -> FinalFormPayload:
        field_map = {f.id: f for f in fields}
        audit: list[str] = []
        for prop in proposals:
            if prop.field_id in field_map:
                field = field_map[prop.field_id]
                field.value = prop.proposed_value
                field.is_missing = False
                audit.append(
                    f"Filled {prop.field_id} with {prop.proposed_value} (src={','.join(prop.source_entity_ids)})"
                )
        return FinalFormPayload(fields=list(field_map.values()), audit_trail=audit, consistency=[])
