# LLM Chain: Fill Missing Fields from Bills

This repository implements the agentic workflow described in `Pipeline Diagram/Agentic_Workflow.md` and `Pipeline Diagram/Implementation_Blueprint.md`. It ingests a partially filled form plus supporting bills, detects missing fields, extracts values with two LLM passes, reconciles differences, and emits a filled form with provenance.

## Layout
- `src/agents/`: Form analysis, bill parsing, reconciler, form writer.
- `src/orchestrator/`: Workflow runner and CLI.
- `src/services/`: LLM factory, OCR helpers, prompt loader, calculations.
- `src/prompts/`: Prompt templates for each agent.
- `src/data_models/`: Pydantic schemas for shared contracts.
- `fixtures/`: Sample form and bills for local testing.
- `Pipeline Diagram/`: Original diagrams and narrative docs.
- `../common_data/input`: Shared input for forms/bills (used by both implementations).
- `../common_data/output`: Shared outputs; each run writes `<case>_output.json`.

## Quickstart
1. Python 3.10+ recommended.
2. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment (choose OpenAI or local Ollama):
   ```bash
   # Option A: OpenAI
   set OPENAI_API_KEY=sk-...
   # Option B: Ollama (ensure model exists, e.g., qwen2:7b or llama3:instruct)
   set OLLAMA_ENDPOINT=http://localhost:11434
   ```
4. Run the pipeline on fixtures (set PYTHONPATH so `src` is importable):
   ```bash
   set PYTHONPATH=src
   # Interactive shared-mode (pulls forms from ../common_data/input)
   python -m orchestrator.cli
   # or direct paths (legacy)
   python -m orchestrator.cli --form fixtures/sample_form.txt --bills fixtures/bills
   ```

## What happens
- FormAnalysisAgent finds missing fields from the form text.
- BillParsingAgent runs twice (two model configs) to produce independent candidate values.
- Reconciler checks consensus; matches become fill proposals.
- FormWriter applies proposals to produce the final filled form and audit trail.

## Configuration
Adjust `src/config/settings.py` for model names, temperatures, numeric tolerance, and retry limits. Prompts live in `src/prompts/` and can be edited without touching code.

## Notes
- OCR is provided via `pdfplumber`/`pytesseract`. For images/PDFs, ensure Tesseract is installed and on PATH.
- The code is LLM-provider agnostic; it will use OpenAI if `OPENAI_API_KEY` is set, otherwise Ollama.
