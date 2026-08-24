"""
core/extraction.py

Uses the local LLM to turn raw resume text into structured JSON.
Validates the output and retries once on failure.
"""

from __future__ import annotations
import json
import re
from pathlib import Path

from core.llm_engine import LLMEngine

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extraction_prompt.txt"

REQUIRED_FIELDS = {
    "name": str,
    "skills": list,
    "years_of_experience": (int, float),
    "education_level": str,
    "past_job_titles": list,
}

SYSTEM_PROMPT = "You are a precise, deterministic JSON-only extraction engine."


def _load_prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _extract_json_block(text: str) -> str:
    """Grab the first {...} block in case the model adds stray text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output.")
    return match.group(0)


def _validate(data: dict) -> dict:
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(data[field], expected_type):
            raise ValueError(f"Field '{field}' has wrong type: {type(data[field])}")
    return data


def extract_resume_data(resume_text: str, engine: LLMEngine | None = None) -> dict:
    """
    Returns a structured dict:
    { name, skills[], years_of_experience, education_level, past_job_titles[] }
    Raises ValueError if extraction fails twice.
    """
    engine = engine or LLMEngine.get_instance()
    template = _load_prompt_template()
    user_prompt = template.format(resume_text=resume_text[:6000])  # guard context length

    last_error = None
    for attempt in range(2):
        raw_output = engine.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt if attempt == 0 else user_prompt + "\n\nReturn ONLY valid JSON, nothing else.",
            max_tokens=512,
            temperature=0.1,
        )
        try:
            json_str = _extract_json_block(raw_output)
            data = json.loads(json_str)
            return _validate(data)
        except (ValueError, json.JSONDecodeError) as e:
            last_error = e
            continue

    raise ValueError(f"Failed to extract structured data after retries: {last_error}")
