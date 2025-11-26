# Multi-LLM Cross-Verification Workflow Description

The handwritten diagram (`Dia.jpg`) and the polished version (`DigiDia.png`) depict the same pipeline: a partially filled form plus bill stack flow through a chain of four LLM agents that repeatedly extract the missing values, cross-check each other, and only emit the filled form once every model agrees. Everything below verbalizes that shared design.

## Actors and Responsibilities
- **Missing-Field Extractor:** Parses the intake form to list identifiers/labels that still need values. Provides guidance (currency, numerical relationships) for downstream agents.
- **LLM 1 – Primary Extractor:** Reads the bill documents, maps each missing field to a candidate value, and performs any necessary per-field calculations (totals, taxes, mileage).
- **LLM 2 – Independent Extractor:** Repeats the same extraction+calculation task with a different prompt/model/temperature to generate an independent candidate set.
- **LLM 3 – Consensus Checker:** Compares results from LLM1 and LLM2 field-by-field, flags disagreements, and may request clarifications or re-runs.
- **LLM 4 – Arbiter/Final Writer:** When all candidate values match or fall within tolerance, LLM4 writes them into the final form template and explains provenance. If LLM3 reports inconsistencies, LLM4 asks for another extraction round before emitting results.
- **Orchestrator:** Maintains state, routes documents, enforces retry thresholds, and decides when to stop for human review.

## Step-by-Step Flow
1. **Input ingest**
   - Receive the partially filled form and associated bills (PDF/JPEG/etc.).
   - Normalize file names, capture metadata such as claimant info, and push OCR text into a document store.

2. **Identify missing targets**
   - The missing-field extractor (rule-based + LLM) scans the form structure to list every field that lacks a value or fails validation.
   - The resulting `MissingFieldList` contains field ids, textual labels, expected datatype/units, and hints pointing to relevant sections of the bills.

3. **Parallel extraction attempts (LLM1 & LLM2)**
   - Each extractor receives the same `MissingFieldList` plus bill text snippets.
   - LLM1 outputs `CandidateSetA`, while LLM2 outputs `CandidateSetB`, both with value, confidence, and justification (bill id, line item, calculation steps).
   - If either extractor cannot find a value, it marks the field as `unresolved` with an explanation.

4. **Intermediate calculation auditing**
   - LLM1/LLM2 also return any derived figures (e.g., grand totals) so disagreements can be traced to the exact arithmetic step.

5. **Consensus check (LLM3)**
   - LLM3 receives both candidate sets and performs:
     - Equality/threshold comparison (numeric tolerance, date proximity).
     - Reasonableness rules (totals equal sum of line items, taxes <= amounts).
   - Output: `consistency_report` describing which fields match, which diverge, and recommended next actions.

6. **Branching on match vs mismatch**
   - *If all match:* The orchestrator forwards the approved values to LLM4.
   - *If mismatch:* The orchestrator loops back to LLM1/LLM2 with feedback (e.g., "re-check bill 3 for Meals Total"). Optionally escalate to a third extraction prompt or a human reviewer after N failed attempts.

7. **Final form generation (LLM4)**
   - LLM4 loads the latest agreed-upon values, injects them into the digital form (JSON/PDF), and writes an audit log showing each field, the consensus value, and the confirming models.
   - The filled form plus the audit report is returned as the pipeline output.

8. **Logging & provenance**
   - Every transition preserves prompts, responses, consensus decisions, and bill references to support future audits and prompt tuning.

## Data Hand-Offs Mirroring the Diagram
- `Form -> Missing-Field Extractor -> LLM1/LLM2`
- `Bills -> LLM1/LLM2 -> Candidate Sets`
- `Candidate Sets -> LLM3 (consistency)` -> either `retry` or `LLM4`
- `LLM4 -> Filled Form + Explanation`

This textual outline is the reference narrative for the cross-verification pipeline shown in both diagrams.
