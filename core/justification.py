"""
core/justification.py

Uses the local LLM to explain an already-computed score breakdown
in plain English. The LLM never sets or changes the score itself.
"""

from __future__ import annotations
from pathlib import Path

from core.llm_engine import LLMEngine
from core.scoring import ScoreBreakdown

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "justification_prompt.txt"

SYSTEM_PROMPT = (
    "You explain pre-computed candidate scores clearly and briefly. "
    "You never invent or change numbers."
)


def _load_prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def generate_justification(
    candidate_name: str,
    job_title: str,
    breakdown: ScoreBreakdown,
    engine: LLMEngine | None = None,
) -> str:
    engine = engine or LLMEngine.get_instance()
    template = _load_prompt_template()

    prompt = template.format(
        candidate_name=candidate_name or "The candidate",
        job_title=job_title,
        final_score=round(breakdown.final_score, 1),
        skill_match=round(breakdown.skill_match, 2),
        matched_skills=len(breakdown.matched_skills),
        missing_skills=len(breakdown.missing_skills),
        experience_fit=round(breakdown.experience_fit, 2),
        education_fit=round(breakdown.education_fit, 2),
        title_relevance=round(breakdown.title_relevance, 2),
    )

    return engine.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        max_tokens=150,
        temperature=0.4,
    )
