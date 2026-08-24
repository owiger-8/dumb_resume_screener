"""
core/pdf_parser.py

Extracts raw text from resume files (PDF or plain .txt).
"""

from __future__ import annotations
from pathlib import Path

import pdfplumber


def extract_text(file_path: str | Path) -> str:
    """Return the raw text content of a resume file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")

    if path.suffix.lower() == ".pdf":
        return _extract_pdf_text(path)
    elif path.suffix.lower() in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def _extract_pdf_text(path: Path) -> str:
    chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            chunks.append(text)
    full_text = "\n".join(chunks).strip()
    if not full_text:
        raise ValueError(
            f"No extractable text found in {path.name}. "
            "It may be a scanned/image-only PDF."
        )
    return full_text
