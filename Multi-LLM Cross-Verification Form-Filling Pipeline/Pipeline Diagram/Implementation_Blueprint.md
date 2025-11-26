# Implementation Blueprint: Multi-LLM Cross-Verification Form-Filling Pipeline

This plan turns the diagram into concrete engineering work so you can feed LLM coding assistants with precise tasks. Follow sections sequentially.

## 0. Project scaffolding
1. Initialize a mono-repo with packages: `orchestrator`, `agents`, `storage`, `prompts`, `tests`.
2. Add dependencies: `langchain`/`openai`, `pydantic`, `fastapi`, `uvicorn`, `structlog`, OCR libs, `pandas`, `tenacity` (retry), `jsonschema`.
3. Configure `.env` for API keys and a `config/settings.py` that stores model names, temperatures, consensus thresholds, and retry limits.

## 1. Shared schemas
- `MissingField` (id, label, expected_type, hint).
- `CandidateValue` (field_id, value, units, confidence, source_bill, calc_steps).
- `ConsistencyReport` (field_id, status in {match, mismatch, unresolved}, notes).
- `FilledForm` (fields dict, audit_trail list).
Expose them via Pydantic models in `data_models/` so every agent serializes identically.

## 2. Missing-field extraction module
1. Write `agents/missing_fields/parser.py` that reads PDF/JSON forms and emits normalized field objects (maybe using `pdfplumber` + heuristics).
2. Create prompt templates (`prompts/missing_fields.yaml`) instructing an LLM to flag empty/invalid entries and supply hints.
3. Unit tests: feed fixture forms and assert the list of missing fields matches the ground truth.

## 3. LLM1 & LLM2 extractor services
1. Implement a base class `BaseExtractorAgent` with `extract(form_context, bills, missing_fields) -> list[CandidateValue]`.
2. Specialize into `LLM1Extractor` and `LLM2Extractor` that vary prompts/models/temperature to get independent outputs.
3. Add bill pre-processing: OCR to text, chunking, vendor detection.
4. Persist each candidate set in `storage/candidates/llm1.jsonl` and `llm2.jsonl` for traceability.
5. Tests: use stubbed LLMs returning deterministic JSON to ensure parsing and serialization work.

## 4. Calculation utilities
- Build `services/calculations.py` containing helpers (sum_line_items, compute_tax_from_rate, currency_normalization) so LLM responses can cite deterministic formulas.
- Allow LLMs to call these functions via tool/function-calling for better accuracy.

## 5. LLM3 consensus checker
1. Implement `ConsensusAgent` that ingests two candidate sets and outputs `ConsistencyReport` objects.
2. Include deterministic checks before prompting: direct equality for strings, tolerance comparisons for numbers, date diff rules.
3. Prompt the LLM only for ambiguous cases (e.g., two close values) to keep costs low.
4. Store mismatch diagnostics for UI display.

## 6. Retry & escalation logic
- In `orchestrator/workflow.py`, codify rules: if mismatch occurs, request re-run from the extractor that diverged; after `max_retries`, flag for human review.
- Maintain per-field retry counters and track which bill snippets were already provided so prompts can be refined automatically.

## 7. LLM4 form writer
1. Build `FormWriter` that takes the approved values and updates the output form template (JSON, PDF, XLSX). Use libs like `pdfrw` or `openpyxl` as needed.
2. Generate an audit log summarizing consensus evidence and attach to the final payload.

## 8. Orchestrator & pipeline execution
1. Create a state machine: `INGEST -> FIND_MISSING -> EXTRACT_LLM1 -> EXTRACT_LLM2 -> CONSENSUS -> (RETRY|WRITE_FORM)`.
2. Provide CLI/API entry points: `python -m orchestrator.run --form input/form.pdf --bills data/bills/`.
3. Include structured logging for each transition plus metrics (tokens, latency).

## 9. Testing & evaluation harness
- Fixture set with synthetic bills and known answers to validate consensus logic.
- Integration test running the entire pipeline with mock LLMs to ensure loops behave correctly.
- Evaluation script that reports how many fields reached consensus vs required human intervention.

## 10. Feeding instructions to a coding LLM
When developing, copy the relevant numbered section into your AI pair programmer prompt (e.g., "Implement `BaseExtractorAgent` as described in Section 3"). Ask it to output code + tests, run them locally, then proceed to the next section to keep context focused and ensure the final product mirrors the diagram exactly.
