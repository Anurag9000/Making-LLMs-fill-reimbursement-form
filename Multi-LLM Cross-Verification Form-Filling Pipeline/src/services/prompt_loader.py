"""Prompt loader from YAML files."""
from __future__ import annotations

from pathlib import Path
import yaml


PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> dict:
    path = PROMPT_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))
