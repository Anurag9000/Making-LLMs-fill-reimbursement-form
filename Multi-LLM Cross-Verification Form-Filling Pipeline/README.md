# Multi-LLM Cross-Verification Form-Filling Pipeline

Implements the agentic workflow from the diagrams: two independent extraction LLMs, a consensus checker (LLM3), and a final writer (LLM4) that only emits a filled form when values match. Uses shared `../common_data/input` and `../common_data/output` alongside a local `fixtures/` example.

## Layout
- `src/agents/`: Missing-field agent, two bill extractors (model variants), consensus checker, form writer.
- `src/orchestrator/`: Workflow + CLI selector.
- `src/services/`: LLM factory, OCR, prompt loader, JSON parsing, calculations, proposal builder.
- `src/prompts/`: Prompt templates for each agent.
- `src/data_models/`: Pydantic contracts.
- `fixtures/`: Sample form/bills.
- `../common_data/input` & `../common_data/output`: Shared I/O for both implementations.

## Install
```bash
pip install -r requirements.txt
```

## Run (shared input/output UI)
```bash
set PYTHONPATH=src
python -m orchestrator.cli
```
- Place cases in `../common_data/input` as folders with a form file and optional `bills/`, or as loose form files plus `<stem>_bills`.
- Select numbers (e.g., `1,3`) or press Enter for all. Outputs saved to `../common_data/output/<case>_output.json`.

## Run (direct paths)
```bash
set PYTHONPATH=src
python -m orchestrator.cli --form fixtures/sample_form.txt --bills fixtures/bills
```

## What happens
1) MissingFieldAgent identifies missing/invalid fields.
2) BillExtractor runs twice with two model configs to create candidate sets.
3) ConsensusChecker (LLM3) compares candidate sets and marks match/mismatch.
4) FormWriter (LLM4) fills form from matched values and emits audit trail and consistency report.

## Configure
- Edit `src/config/settings.py` to change model names/temperatures/tolerance.
- Prompts live in `src/prompts/` and can be tuned without code changes.

Note: Requires working LLM backends (OpenAI or Ollama) and Tesseract/PDF tooling for OCR.
