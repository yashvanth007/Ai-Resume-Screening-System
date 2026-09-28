import re
import logging
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings

WEIGHTS = {"skills": 0.35, "semantic": 0.25, "experience": 0.15, "education": 0.10, "projects": 0.10, "certifications": 0.05}
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _sentence_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


@lru_cache(maxsize=1024)
def _sentence_embedding(text: str) -> tuple[float, ...]:
    vector = _sentence_model().encode(text, normalize_embeddings=True)
    return tuple(float(value) for value in vector)


def sentence_embedding(text: str, excluded: tuple[str, ...] = ()) -> list[float] | None:
    if not settings.use_sentence_transformers or not text.strip():
        return None
    sanitized = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|https?://\S+|\+?\d[\d\s().-]{7,}\d", " ", text, flags=re.IGNORECASE)
    for value in excluded:
        if value and len(value.strip()) > 2:
            sanitized = re.sub(re.escape(value.strip()), " ", sanitized, flags=re.IGNORECASE)
    try:
        return list(_sentence_embedding(sanitized))
    except Exception:
        logger.warning("Sentence-transformer embedding unavailable.", exc_info=True)
        return None


def semantic_similarity(job_text: str, resume_text: str, excluded: tuple[str, ...] = ()) -> float:
    if not job_text.strip() or not resume_text.strip():
        return 0.0
    resume_text = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|https?://\S+|\+?\d[\d\s().-]{7,}\d", " ", resume_text, flags=re.IGNORECASE)
    for value in excluded:
        if value and len(value.strip()) > 2:
            resume_text = re.sub(re.escape(value.strip()), " ", resume_text, flags=re.IGNORECASE)
    if settings.use_sentence_transformers:
        try:
            job_embedding = sentence_embedding(job_text)
            resume_embedding = sentence_embedding(resume_text)
            if job_embedding is None or resume_embedding is None:
                raise RuntimeError("Embedding unavailable")
            return max(0.0, min(1.0, sum(left * right for left, right in zip(job_embedding, resume_embedding))))
        except Exception:
            logger.warning("Sentence-transformer inference unavailable; using TF-IDF fallback.", exc_info=True)
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        matrix = vectorizer.fit_transform([job_text, resume_text])
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        return 0.0


def _skill_score(required: list[str], preferred: list[str], candidate_skills: set[str]) -> tuple[float, list[str], list[str]]:
    required_by_folded = {skill.casefold(): skill for skill in required}
    preferred_by_folded = {skill.casefold(): skill for skill in preferred if skill.casefold() not in required_by_folded}
    required_folded = set(required_by_folded)
    preferred_folded = set(preferred_by_folded)
    matched_required = required_folded & candidate_skills
    matched_preferred = preferred_folded & candidate_skills
    missing = sorted((required_by_folded[skill] for skill in required_folded - candidate_skills), key=str.casefold)
    required_score = len(matched_required) / len(required_folded) if required_folded else (1.0 if matched_preferred else 0.0)
    preferred_score = len(matched_preferred) / len(preferred_folded) if preferred_folded else required_score
    if required_folded and preferred_folded:
        score = required_score * 0.8 + preferred_score * 0.2
    else:
        score = required_score if required_folded else preferred_score
    matched = sorted((required_by_folded.get(skill) or preferred_by_folded[skill] for skill in matched_required | matched_preferred), key=str.casefold)
    return score, matched, missing


def calculate_match(job: dict, candidate: dict, resume_text: str) -> dict:
    required = job.get("required_skills", [])
    preferred = job.get("preferred_skills", [])
    candidate_skills = {skill.casefold() for skill in candidate.get("skills", [])}
    skill_score, matched, missing = _skill_score(required, preferred, candidate_skills)
    semantic = semantic_similarity(job.get("description", ""), resume_text, tuple(candidate.get(key, "") for key in ("name", "email", "phone")))
    requested_years = float(job.get("experience_required") or 0)
    actual_years = float(candidate.get("experience_years") or 0)
    experience = 1.0 if requested_years == 0 else min(actual_years / requested_years, 1.0)
    education_items = candidate.get("education", [])
    education = 1.0 if not job.get("education_requirement") else float(any(job["education_requirement"].casefold() in str(item).casefold() for item in education_items))
    projects_text = " ".join(f"{item.get('name', '')} {item.get('description', '')} {' '.join(item.get('technologies', []))}" for item in candidate.get("projects", []))
    project_score = semantic_similarity(job.get("description", ""), projects_text) if projects_text.strip() else 0.0
    certification_text = " ".join(item.get("name", "") for item in candidate.get("certifications", []))
    certification_score = semantic_similarity(job.get("description", ""), certification_text) if certification_text else 0.0
    components = {"skills": skill_score, "semantic": semantic, "experience": experience, "education": education, "projects": project_score, "certifications": certification_score}
    overall = sum(components[key] * WEIGHTS[key] for key in WEIGHTS)
    explanations = [f"Matched {len(matched)} of {len(required) + len(preferred)} listed skills: {', '.join(matched)}." if matched else "No listed job skills were detected in the resume."]
    if missing:
        explanations.append(f"Required skills not detected: {', '.join(missing)}.")
    if actual_years:
        explanations.append(f"Resume states {actual_years:g} years of experience; role requests {requested_years:g}.")
    if semantic:
        explanations.append(f"Resume and job description have {semantic:.0%} text similarity.")
    return {"overall_score": round(overall * 100, 1), "skill_score": round(skill_score * 100, 1), "semantic_score": round(semantic * 100, 1), "experience_score": round(experience * 100, 1), "education_score": round(education * 100, 1), "project_score": round(project_score * 100, 1), "certification_score": round(certification_score * 100, 1), "matched_skills": matched, "missing_skills": missing, "explanation": explanations, "weights": WEIGHTS.copy()}


def extract_job_skills(description: str, catalog: list[str]) -> list[str]:
    detected = []
    for skill in catalog:
        if re.search(rf"(?<![\w]){re.escape(skill)}(?![\w])", description, re.IGNORECASE):
            detected.append(skill)
    return detected
