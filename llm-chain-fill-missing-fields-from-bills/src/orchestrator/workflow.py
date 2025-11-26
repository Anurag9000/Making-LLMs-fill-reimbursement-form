"""Pipeline orchestration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agents.bill_parser import BillParsingAgent
from agents.form_analysis import FormAnalysisAgent
from agents.form_writer import FormWriter
from agents.reconciler import Reconciler
from config.settings import get_settings
from data_models.schemas import WorkflowState
from services.ocr import extract_text_auto


def run_workflow(form_path: str | Path, bills_dir: str | Path) -> Dict[str, Any]:
    settings = get_settings()
    form_agent = FormAnalysisAgent()
    bill_agent_a = BillParsingAgent(model_config=settings.bill_parser_model_a)
    bill_agent_b = BillParsingAgent(model_config=settings.bill_parser_model_b)
    reconciler = Reconciler()
    writer = FormWriter()

    form_text = extract_text_auto(form_path)
    form_fields = form_agent.analyze(form_text)
    missing = form_agent.missing(form_fields)

    candidate_a = bill_agent_a.process_directory(bills_dir, missing)
    candidate_b = bill_agent_b.process_directory(bills_dir, missing)

    reports = reconciler.reconcile(candidate_a, candidate_b)
    proposals = reconciler.propose(reports, candidate_a, candidate_b)
    final_form = writer.apply(form_fields, proposals)
    state = WorkflowState(
        missing_fields=missing,
        candidate_set_a=candidate_a,
        candidate_set_b=candidate_b,
        proposals=proposals,
        final_form=final_form,
    )

    return {
        "final_form": final_form.model_dump(),
        "consistency_reports": [r.model_dump() for r in reports],
        "workflow_state": state.model_dump(),
    }
