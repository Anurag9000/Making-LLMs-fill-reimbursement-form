# Implementation Blueprint for the Agentic Form-Filling Workflow

This file translates the conceptual diagram and agent description into concrete coding steps. Each step can be fed to an LLM-powered coding copilot to scaffold the full solution.

## 0. Repository & tooling setup
1. Initialize a Python project (`uv`/`pipenv`/`poetry`). Pin dependencies such as `pydantic`, `fastapi` (for an API), `langchain` or `llama-index`, `tiktoken`, `httpx`, and `pytesseract`/`paddleocr` for OCR.
2. Create folders:
   - `agents/form_analysis`, `agents/bill_parser`, `agents/reconciler`.
   - `orchestrator/` for workflow control logic.
   - `data_models/` for schemas shared across agents.
   - `tests/` mirroring each module.
3. Configure logging (structlog/loguru) and `.env` loading for API keys.

## 1. Data contracts (code-first)
Prompt the LLM to write Pydantic models:
- `FormField` with fields: `id`, `label`, `value`, `is_missing`, `hint`.
- `BillDocument` (`id`, `source_path`, `text`, `metadata`).
- `ExtractedEntity` with provenance info (`bill_id`, `field`, `value`, `confidence`, `coordinates`).
- `FillProposal` with `field_id`, `proposed_value`, `justification`, `confidence`, `source_entity_ids`.
Validate serialization to/from JSON.

## 2. Form Analysis Agent implementation
1. Create `agents/form_analysis/prompts.py` containing a system prompt describing the form JSON structure and the expected output schema (list of `FormField`).
2. Implement `FormAnalysisAgent`:
   - Accepts `form_pdf_path` or structured JSON.
   - Uses OCR (if PDF) + parsing heuristics to convert to a field array before LLM call.
   - Calls the LLM with function calling or JSON schema forcing to return missing-field report.
3. Write unit tests using a stub LLM that returns deterministic JSON.

## 3. Bill Parsing Agent implementation
1. Build OCR pipeline (`ocr/extract_text.py`), returning text blocks per bill.
2. Prompt template instructs the LLM to emit normalized entities. Example message:
   ```json
   {
     "instruction": "Extract vendor, date, amount, tax, description from the following bill text.",
     "output_schema": ExtractedEntityList
   }
   ```
3. Implement batching + rate limiting; persist outputs in `storage/extracted_data.jsonl`.
4. Tests: feed synthetic bill text, assert entity normalization and provenance capture.

## 4. Reconciliation & Filling Agent
1. Construct prompt that receives two payloads: `missing_fields` and `extracted_entities`. Demand JSON output containing `FillProposal` entries.
2. Implement `Reconciler` class with methods:
   - `match_candidates(field: FormField, entities: list[ExtractedEntity]) -> list[ExtractedEntity]` (rule-based pre-filter).
   - `propose_fill(field, candidates)` that calls the LLM when deterministic rules fail.
3. Add validators for currency/date formatting and conflict detection (two proposals for same field). Persist justification text for audit.

## 5. Orchestrator / workflow engine
1. Define a high-level state machine (python `Enum` + `dataclass WorkflowState`). States: `COLLECT_INPUTS`, `ANALYZE_FORM`, `PARSE_BILLS`, `RECONCILE`, `HUMAN_REVIEW`, `COMPLETE`.
2. Implement `run_workflow(form_path, bills_dir)`:
   ```python
   def run_workflow(form_path, bills_dir):
       state = WorkflowState(inputs_loaded=False, completed_fields={})
       form_fields = FormAnalysisAgent().analyze(form_path)
       entities = BillParsingAgent().process_directory(bills_dir)
       proposals = Reconciler().fill(form_fields, entities)
       final_form = FormRenderer().apply(form_fields, proposals)
       return final_form, proposals
   ```
3. Add streaming logs + event hooks for UI/human review. Provide CLI entry point `python -m orchestrator.cli --form form.pdf --bills bills/`.

## 6. Form rendering / export layer
1. Build `FormRenderer` utility that maps `FillProposal` data into the final artifact:
   - Option A: produce JSON/CSV for downstream integration.
   - Option B: write into a PDF template using `pdfrw`/`reportlab`.
2. Include a `source_map.json` capturing `field_id -> [bill_id, page, line]` for traceability.

## 7. Prompt & config registry
- Store prompts and few-shot examples in YAML (e.g., `prompts/form_analysis.yaml`, `prompts/reconciler.yaml`).
- Parameterize temperature, model, and token limits in `config/settings.py` so different environments can tune behavior.

## 8. Testing & evaluation harness
1. Create synthetic fixture data under `fixtures/` (fake forms + bills).
2. Implement regression tests ensuring agents respect schemas (jsonschema validation).
3. Provide evaluation script `python scripts/evaluate.py --fixtures fixtures/basic` that compares generated form vs gold standard and reports recall/precision of filled fields.

## 9. Deployment considerations
- Wrap the orchestrator inside a FastAPI service exposing `/run` endpoint for batch requests.
- Add background jobs for asynchronous processing if bills are heavy (Celery/RQ).
- Instrument usage metrics (tokens, duration) for cost monitoring.

## 10. Feeding instructions to an LLM coding partner
When using the above blueprint with a coding LLM, iterate section by section:
1. Paste the relevant step (e.g., "Implement FormAnalysisAgent") and ask the LLM to generate scaffolding code + tests.
2. Review output, run tests, then move to the next numbered step.
3. Maintain context by reminding the LLM of the data models and prompts defined earlier.

Following these steps sequentially will recreate the workflow described in `Agentic_Workflow.md` with production-ready code scaffolding.
