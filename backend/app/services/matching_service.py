from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.ml.matching import calculate_match, sentence_embedding
from app.models import Application, Candidate, CandidateSkill, Job, MatchResult, Skill
from app.services.resume_parser import extract_skills


def candidate_payload(candidate: Candidate) -> dict:
    return {
        "id": candidate.id, "name": candidate.full_name, "email": candidate.email, "phone": candidate.phone,
        "location": candidate.location, "linkedin": candidate.linkedin, "github": candidate.github,
        "portfolio": candidate.portfolio, "experience_years": candidate.total_experience,
        "skills": [{"name": item.skill.name, "category": item.skill.category, "evidence": item.evidence} for item in candidate.skills],
        "education": [{"degree": item.degree, "institution": item.institution, "graduation_year": item.graduation_year, "gpa": item.gpa} for item in candidate.education],
        "experiences": [{"company": item.company, "title": item.title, "start_date": item.start_date, "end_date": item.end_date, "description": item.description} for item in candidate.experiences],
        "projects": [{"name": item.name, "description": item.description, "technologies": item.technologies} for item in candidate.projects],
        "certifications": [{"name": item.name, "issuer": item.issuer} for item in candidate.certifications],
    }


def score_application(db: Session, application: Application, job: Job | None = None) -> MatchResult:
    job = job or application.job
    candidate = db.scalar(
        select(Candidate).where(Candidate.id == application.candidate_id).options(
            selectinload(Candidate.skills).selectinload(CandidateSkill.skill),
            selectinload(Candidate.education), selectinload(Candidate.projects), selectinload(Candidate.certifications),
            selectinload(Candidate.resumes),
        )
    )
    latest_resume = max(candidate.resumes, key=lambda resume: resume.uploaded_at) if candidate.resumes else None
    candidate_data = candidate_payload(candidate)
    candidate_data["skills"] = [item["name"] for item in candidate_data["skills"]]
    if latest_resume:
        parsed = extract_skills(latest_resume.extracted_text)
        candidate_data["skills"] = list(dict.fromkeys(candidate_data["skills"] + [item["name"] for item in parsed]))
    result = calculate_match({"description": job.description, "required_skills": job.required_skills, "preferred_skills": job.preferred_skills, "experience_required": job.experience_required, "education_requirement": job.education_requirement}, candidate_data, latest_resume.extracted_text if latest_resume else "")
    existing = db.scalar(select(MatchResult).where(MatchResult.application_id == application.id))
    match = existing or MatchResult(application_id=application.id)
    for key in ("overall_score", "skill_score", "semantic_score", "experience_score", "education_score", "project_score", "certification_score", "matched_skills", "missing_skills", "explanation"):
        setattr(match, key, result[key])
    match.embedding = sentence_embedding(latest_resume.extracted_text, (candidate.full_name, candidate.email or "", candidate.phone or "")) if latest_resume and settings.use_sentence_transformers else None
    db.add(match)
    db.flush()
    return match


def ensure_skill(db: Session, name: str, category: str = "Other") -> Skill:
    skill = db.scalar(select(Skill).where(Skill.name.ilike(name)))
    if not skill:
        skill = Skill(name=name, category=category)
        db.add(skill)
        db.flush()
    return skill
