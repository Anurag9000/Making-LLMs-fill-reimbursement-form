# Agentic Workflow for Filling Reimbursement Forms

This document verbalizes the handwritten diagram (Dia.png) as a detailed agentic workflow that a multi-agent LLM system can implement to move from an incomplete reimbursement form and supporting bills to a fully populated form.

## Actors and responsibilities
- **Form Analysis Agent (LLM-A):** Inspects the partially filled reimbursement form, infers the schema, and enumerates every missing field along with contextual hints (e.g., "travel start date missing, see bill 2").
- **Document Parsing Agent (LLM-B):** Reads raw bill scans or PDFs and extracts structured candidate data (date, vendor, amount, tax, description, etc.).
- **Reconciliation & Filling Agent (LLM-C):** Aligns missing form fields with extracted bill data, applies validation rules, and writes the final filled form.
- **Orchestrator / Controller:** Keeps state, routes intermediate payloads between agents, and enforces stop conditions (e.g., when all mandatory fields are filled or human review needed).

## Step-by-step flow
1. **Input acquisition**  
   - The workflow receives (a) a partially filled reimbursement form and (b) a packet of supporting bills.
   - Metadata such as the claimant ID, policy constraints, or allowed expense types is logged for downstream validation.

2. **Form schema & gap discovery (LLM-A)**  
   - The orchestrator sends the raw form to LLM-A with instructions to output: field name, current value (if any), missing/invalid flag, and clues describing what information is still required.  
   - Output example: `{"field":"Total Meals Amount","status":"missing","hint":"Look for meal receipts dated 12-14 Jan"}`.

3. **Bill ingestion & entity extraction (LLM-B)**  
   - Each bill document is streamed to LLM-B. The agent produces normalized JSON rows with entity/value pairs plus provenance (bill id, page, OCR confidence).  
   - Data is stored in a temporary "extracted data" table for reconciliation.

4. **Candidate matching (LLM-C + orchestrator)**  
   - For every missing field reported by LLM-A, the orchestrator queries the extracted table and crafts a prompt to LLM-C such as: "Populate `Travel Start Date` using data from Bills 1-3".  
   - LLM-C selects the best matching bill entry, performs sanity checks (date formats, currency rules), and proposes a value along with justification.

5. **Form reconstruction**  
   - Once values are validated, LLM-C writes them into the digital form template or a structured payload (JSON/CSV) mirroring the form.  
   - Conflicts (e.g., two bills mapping to the same field) trigger another pass where the orchestrator asks for clarification or marks the field for manual review.

6. **Output generation**  
   - The completed form plus a log of field->source mappings is produced.  
   - Optional: generate a summary explaining which bills were used for each field to aid auditing.

7. **Human-in-the-loop checkpoints (optional)**  
   - If confidence scores drop below a threshold, the system pauses and requests a human reviewer to approve or correct the field before final submission.

## Data hand-offs (mirroring diagram arrows)
- `Form -> LLM-A -> Missing Field Report`
- `Bills -> LLM-B -> Extracted Data`
- `Missing Field Report + Extracted Data -> LLM-C -> Filled Form`

## Implementation notes
- Preserve provenance at every hop so auditors can trace each field back to a specific bill image + line item.
- Normalize units/currency early to reduce reconciliation errors.
- Store intermediate artifacts (prompts, responses, extracted JSON) to simplify debugging and improving prompts later.
- Modularize agents so that improvements to bill parsing or reconciliation can be deployed independently without retraining the entire chain.
