import json
import urllib.error
import urllib.request

from app.core.config import settings


def generate_candidate_summary(candidate: dict, job: dict, match: dict) -> dict:
    skills = [item["name"] for item in candidate.get("skills", [])]
    projects = [item.get("name") for item in candidate.get("projects", []) if item.get("name")]
    summary = f"{candidate.get('name', 'Candidate')} has {candidate.get('experience_years', 0):g} stated years of experience and {len(match.get('matched_skills', []))} detected skills aligned to {job.get('title', 'the role')}."
    fallback = {"summary": summary, "strengths": match.get("matched_skills", [])[:6], "missing_requirements": match.get("missing_skills", []), "relevant_experience": projects[:4], "interview_focus": match.get("missing_skills", [])[:4], "source": "rule-based"}
    if not settings.llm_api_key or not settings.llm_base_url:
        return fallback
    facts = {"skills": skills, "experience_years": candidate.get("experience_years"), "projects": candidate.get("projects", [])[:8], "job_title": job.get("title"), "job_description": job.get("description", "")[:5000], "match": match}
    body = json.dumps({"model": settings.llm_model, "temperature": 0, "messages": [{"role": "system", "content": "Summarize only facts present in the provided candidate and job data. Never infer protected characteristics or invent experience. Return JSON with summary, strengths, missing_requirements, relevant_experience, interview_focus."}, {"role": "user", "content": json.dumps(facts)}]}).encode()
    request = urllib.request.Request(settings.llm_base_url.rstrip("/") + "/chat/completions", body, {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            data = json.loads(response.read())
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content[content.find("{"):content.rfind("}") + 1])
        result["source"] = "llm"
        return result
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
        return fallback


def generate_interview_questions(candidate: dict, job: dict, match: dict) -> dict:
    skills = [item["name"] for item in candidate.get("skills", [])]
    projects = [item.get("name", "a project") for item in candidate.get("projects", [])]
    missing = match.get("missing_skills", [])
    required = job.get("required_skills", [])
    technical = [f"How have you used {skill} in a production or project setting?" for skill in (missing[:2] + [skill for skill in skills if skill in required][:3])[:5]]
    technical_fallbacks = [
        f"How would you validate a {job.get('title', 'role-specific')} solution before release?",
        f"What trade-offs would you consider when maintaining a {job.get('title', 'role-specific')} service?",
        "How would you diagnose a production issue when logs and metrics are incomplete?",
        "How would you evaluate reliability and quality after deployment?",
        "How would you communicate a technical risk and propose a mitigation?",
    ]
    for question in technical_fallbacks:
        if len(technical) >= 5:
            break
        if question not in technical:
            technical.append(question)
    project_questions = [f"What was your contribution to {project}, and how did you measure its outcome?" for project in projects[:3]]
    project_fallbacks = [
        "Describe a project decision you would revisit and what you learned from it.",
        "How did you divide the work and validate the outcome of a project?",
        "What changed after you received feedback on a project?",
    ]
    for question in project_fallbacks:
        if len(project_questions) >= 3:
            break
        project_questions.append(question)
    behavioral = ["Tell me about a time you received difficult feedback and how you responded.", "Describe how you work through ambiguity with teammates."]
    return {"technical": technical[:5], "project": project_questions[:3], "behavioral": behavioral, "source": "generated from extracted resume and job data; questions are prompts, not factual claims"}
