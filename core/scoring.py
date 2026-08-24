"""
core/scoring.py

Deterministic candidate-vs-job scoring.
The LLM never invents this number -- it is computed purely from
structured data extracted from the resume and the job description.

final_score = (skill_match     * 0.50 +
               experience_fit  * 0.25 +
               education_fit   * 0.15 +
               title_relevance * 0.10) * 10
"""

from __future__ import annotations
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re

EDUCATION_WEIGHTS = {
    "phd": 1.0,
    "doctorate": 1.0,
    "masters": 0.85,
    "master": 0.85,
    "bachelors": 0.7,
    "bachelor": 0.7,
    "associate": 0.5,
    "diploma": 0.45,
}
DEFAULT_EDUCATION_WEIGHT = 0.4


@dataclass
class ScoreBreakdown:
    final_score: float
    skill_match: float
    experience_fit: float
    education_fit: float
    title_relevance: float
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "final_score": round(self.final_score, 2),
            "skill_match": round(self.skill_match, 2),
            "experience_fit": round(self.experience_fit, 2),
            "education_fit": round(self.education_fit, 2),
            "title_relevance": round(self.title_relevance, 2),
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
        }


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def _skill_match(candidate_skills: list[str], required_skills: list[str]) -> tuple[float, list[str], list[str]]:
    if not required_skills:
        return 1.0, [], []

    cand_norm = {_normalize(s) for s in candidate_skills}
    matched, missing = [], []

    for req in required_skills:
        req_norm = _normalize(req)
        # exact match or close fuzzy match (handles minor wording differences)
        hit = req_norm in cand_norm or any(
            SequenceMatcher(None, req_norm, c).ratio() > 0.85 for c in cand_norm
        )
        if hit:
            matched.append(req)
        else:
            missing.append(req)

    score = len(matched) / len(required_skills)
    return score, matched, missing


def _experience_fit(candidate_years: float, required_years: float) -> float:
    if required_years <= 0:
        return 1.0
    return min(candidate_years / required_years, 1.0)


def _education_fit(education_level: str) -> float:
    key = _normalize(education_level).replace(" degree", "").strip()
    for known, weight in EDUCATION_WEIGHTS.items():
        if known in key:
            return weight
    return DEFAULT_EDUCATION_WEIGHT


def _title_relevance(past_titles: list[str], jd_title: str) -> float:
    if not past_titles or not jd_title:
        return 0.0
    jd_norm = _normalize(jd_title)
    jd_tokens = set(jd_norm.split())
    best = 0.0
    for title in past_titles:
        t_norm = _normalize(title)
        t_tokens = set(t_norm.split())
        if jd_tokens:
            overlap = len(jd_tokens & t_tokens) / len(jd_tokens)
        else:
            overlap = 0.0
        seq_ratio = SequenceMatcher(None, jd_norm, t_norm).ratio()
        combined = max(overlap, seq_ratio)
        best = max(best, combined)
    return min(best, 1.0)


def compute_score(
    candidate: dict,
    required_skills: list[str],
    required_years: float,
    jd_title: str,
) -> ScoreBreakdown:
    """
    candidate: structured dict produced by core/extraction.py, expected keys:
        skills (list[str]), years_of_experience (number),
        education_level (str), past_job_titles (list[str])
    """
    skill_score, matched, missing = _skill_match(
        candidate.get("skills", []), required_skills
    )
    exp_score = _experience_fit(
        float(candidate.get("years_of_experience", 0) or 0), required_years
    )
    edu_score = _education_fit(candidate.get("education_level", ""))
    title_score = _title_relevance(
        candidate.get("past_job_titles", []), jd_title
    )

    final = (
        skill_score * 0.50
        + exp_score * 0.25
        + edu_score * 0.15
        + title_score * 0.10
    ) * 10

    return ScoreBreakdown(
        final_score=final,
        skill_match=skill_score,
        experience_fit=exp_score,
        education_fit=edu_score,
        title_relevance=title_score,
        matched_skills=matched,
        missing_skills=missing,
    )
