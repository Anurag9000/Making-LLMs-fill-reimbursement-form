"""Shared input/output selector for the Multi-LLM Cross-Verification pipeline."""
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
    cases = []
    seen = set()
    for entry in SHARED_INPUT.iterdir():
        if entry.is_dir():
            form = None
            for cand in entry.iterdir():
                if cand.is_file() and cand.suffix.lower() in ALLOWED_FORM_EXTS:
                    form = cand
                    break
            bills_dir = entry / "bills"
            if form:
                cases.append({"name": entry.name, "form": form, "bills": bills_dir if bills_dir.exists() else None})
                seen.add(entry.name.lower())
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
        if part.strip().isdigit():
            indices.append(int(part.strip()))
    return [cases[i - 1] for i in indices if 1 <= i <= len(cases)]


def run_pipeline(case):
    form_path = case["form"]
    bills_dir = case.get("bills")
    if not bills_dir or not bills_dir.exists():
        print(f"Skipping {case['name']}: bills directory not found.")
        return None
    return run_workflow(form_path, bills_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Select shared inputs for the multi-LLM cross-verification pipeline")
    parser.add_argument("--form", help="Path to form (bypasses selector)")
    parser.add_argument("--bills", help="Path to bills directory (bypasses selector)")
    args = parser.parse_args()

    ensure_shared_dirs()

    if args.form and args.bills:
        case = {"name": Path(args.form).stem, "form": Path(args.form), "bills": Path(args.bills)}
        result = run_pipeline(case)
        if result:
            output_path = SHARED_OUTPUT / f"{case['name']}_output.json"
            output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(f"Wrote output -> {output_path}")
        return

    cases = discover_cases()
    if not cases:
        print(f"No forms found in {SHARED_INPUT}. Place form files (and optional bills folders) there and retry.")
        return

    selected = select_cases(cases)
    if not selected:
        print("No selection made; exiting.")
        return

    for case in selected:
        result = run_pipeline(case)
        if result:
            output_path = SHARED_OUTPUT / f"{case['name']}_output.json"
            output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(f"Wrote output -> {output_path}")


if __name__ == "__main__":
    main()
