"""Pipeline orchestration for multi-LLM cross-verification."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agents.bill_extractor import BillExtractor
from agents.consensus_checker import ConsensusChecker
from agents.form_writer import FormWriter
from agents.missing_fields import MissingFieldAgent
from config.settings import get_settings
from data_models.schemas import WorkflowState
from services.ocr import extract_text_auto
from services.proposals import build_proposals


def run_workflow(form_path: str | Path, bills_dir: str | Path) -> Dict[str, Any]:
    settings = get_settings()
    missing_agent = MissingFieldAgent()
    extractor_a = BillExtractor(model_config=settings.extractor_model_a)
    extractor_b = BillExtractor(model_config=settings.extractor_model_b)
    checker = ConsensusChecker()
    writer = FormWriter()

    form_text = extract_text_auto(form_path)
    form_fields = missing_agent.analyze(form_text)
    missing = missing_agent.missing(form_fields)

    candidates_a = extractor_a.process_directory(bills_dir, missing)
    candidates_b = extractor_b.process_directory(bills_dir, missing)

    reports = checker.check(candidates_a, candidates_b)
    proposals = build_proposals(reports, candidates_a, candidates_b)
    final_form = writer.write(form_fields, proposals)
    final_form.consistency = reports

    state = WorkflowState(
        missing_fields=missing,
        candidates_a=candidates_a,
        candidates_b=candidates_b,
        consistency=reports,
        proposals=proposals,
        final_form=final_form,
    )

    return {
        "final_form": final_form.model_dump(),
        "consistency_reports": [r.model_dump() for r in reports],
        "workflow_state": state.model_dump(),
    }
