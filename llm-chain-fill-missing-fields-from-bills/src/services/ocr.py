"""OCR utilities for bills/forms."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pdfplumber
import pytesseract
from PIL import Image


def extract_text_from_pdf(path: str | Path) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_text_from_image(path: str | Path) -> str:
    img = Image.open(path)
    return pytesseract.image_to_string(img)


def extract_text_auto(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() in {".pdf"}:
        return extract_text_from_pdf(path)
    if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        return extract_text_from_image(path)
    return path.read_text(encoding="utf-8")
