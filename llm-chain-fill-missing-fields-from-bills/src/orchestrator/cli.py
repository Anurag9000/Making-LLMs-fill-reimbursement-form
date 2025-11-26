"""CLI entry point for running the workflow with shared input/output folders."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestrator.workflow import run_workflow

ALLOWED_FORM_EXTS = {".pdf", ".txt", ".json", ".png", ".jpg", ".jpeg"}
ROOT = Path(__file__).resolve().parents[2]  # repo root
SHARED_BASE = ROOT.parent / "common_data"
SHARED_INPUT = SHARED_BASE / "input"
SHARED_OUTPUT = SHARED_BASE / "output"


def ensure_shared_dirs() -> None:
    SHARED_INPUT.mkdir(parents=True, exist_ok=True)
    SHARED_OUTPUT.mkdir(parents=True, exist_ok=True)


def discover_cases():
    """Discover available cases in the shared input folder."""
    cases = []
    seen = set()

    # Directories containing a form file (and optional bills/)
    for entry in SHARED_INPUT.iterdir():
        if not entry.is_dir():
            continue
        form = None
        for cand in entry.iterdir():
            if cand.is_file() and cand.suffix.lower() in ALLOWED_FORM_EXTS:
                form = cand
                break
        bills_dir = entry / "bills"
        if form and form.exists():
            cases.append(
                {
                    "name": entry.name,
                    "form": form,
                    "bills": bills_dir if bills_dir.exists() else None,
                }
            )
            seen.add(entry.name.lower())

    # Top-level form files (optionally paired with <stem>_bills or bills/)
    for file in SHARED_INPUT.iterdir():
        if file.is_file() and file.suffix.lower() in ALLOWED_FORM_EXTS:
            stem = file.stem
            if stem.lower() in seen:
                continue
            candidate_bills = SHARED_INPUT / f"{stem}_bills"
            default_bills = SHARED_INPUT / "bills"
            bills_dir = candidate_bills if candidate_bills.exists() else default_bills if default_bills.exists() else None
            cases.append({"name": stem, "form": file, "bills": bills_dir})
    return cases


def select_cases(cases):
    print("Available forms in common_data/input:")
    for idx, case in enumerate(cases, start=1):
        bills_note = f", bills={case['bills'].name}" if case.get("bills") else ", bills=<missing>"
        print(f"{idx}. {case['name']} (form={case['form'].name}{bills_note})")
    raw = input("Select one or more (e.g., 1,3,4 or 'all'): ").strip()
    if raw.lower() == "all" or raw == "":
        return cases
    indices = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            indices.append(int(part))
    selected = []
    for idx in indices:
        if 1 <= idx <= len(cases):
            selected.append(cases[idx - 1])
    return selected


def run_for_case(case):
    form_path = case["form"]
    bills_dir = case.get("bills")
    if not bills_dir or not bills_dir.exists():
        print(f"Skipping {case['name']}: bills directory not found.")
        return
    result = run_workflow(form_path, bills_dir)
    output_path = SHARED_OUTPUT / f"{case['name']}_output.json"
    output_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"Wrote output -> {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LLM form-filling workflow (shared input/output)")
    parser.add_argument("--form", help="Path to partially filled form (pdf/image/json)")
    parser.add_argument("--bills", help="Directory containing bill files")
    parser.add_argument("--use-shared", action="store_true", help="Use common_data input/output selection UI (default)")
    args = parser.parse_args()

    # Direct path mode (backward compatible)
    if args.form and args.bills:
        result = run_workflow(Path(args.form), Path(args.bills))
        print(json.dumps(result, indent=2, default=str))
        return

    # Shared selection mode
    ensure_shared_dirs()
    cases = discover_cases()
    if not cases:
        print(f"No forms found in {SHARED_INPUT}. Place form files (and optional bills folders) there and retry.")
        return
    selected = select_cases(cases)
    if not selected:
        print("No selection made; exiting.")
        return
    for case in selected:
        run_for_case(case)


if __name__ == "__main__":
    main()
