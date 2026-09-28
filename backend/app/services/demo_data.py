from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application, Candidate, CandidateSkill, Certification, Education, Job, MatchResult, Project, Resume
from app.services.matching_service import ensure_skill, score_application

DEMO_JOBS = [
    {"title": "Python Platform Engineer", "company": "Northstar Labs", "location": "Remote · US", "employment_type": "Full-time", "experience_required": 3, "description": "Build dependable Python services and REST APIs with FastAPI, PostgreSQL, Docker, cloud infrastructure, automated tests, and collaborative Git workflows.", "required_skills": ["Python", "FastAPI", "SQL", "REST API", "Git"], "preferred_skills": ["Docker", "AWS", "Machine Learning"]},
    {"title": "Applied Machine Learning Engineer", "company": "Fieldnote AI", "location": "New York, NY · Hybrid", "employment_type": "Full-time", "experience_required": 2, "description": "Develop machine learning and NLP products using Python, scikit-learn, PyTorch, pandas, model evaluation, and production REST services.", "required_skills": ["Python", "Machine Learning", "scikit-learn", "NLP"], "preferred_skills": ["PyTorch", "FastAPI", "Docker"]},
    {"title": "Product Data Scientist", "company": "Open Harbor", "location": "Remote", "employment_type": "Contract", "experience_required": 2, "description": "Explore product behavior with SQL, Python, pandas, experimentation, statistics, clear communication, and practical machine learning.", "required_skills": ["Python", "SQL", "Pandas"], "preferred_skills": ["Machine Learning", "Power BI", "AWS"]},
]

DEMO_CANDIDATES = [
    {"name": "Avery Chen", "email": "avery.chen@example.test", "location": "Portland, OR", "years": 4, "skills": ["Python", "FastAPI", "SQL", "REST API", "Git", "Docker", "AWS", "PostgreSQL"], "degree": "B.S. Computer Science", "school": "Cascadia Technical University", "project": "Service observability platform", "project_description": "Built a Python FastAPI platform with PostgreSQL, Docker, and AWS deployment pipelines."},
    {"name": "Jordan Rivera", "email": "jordan.rivera@example.test", "location": "Chicago, IL", "years": 3, "skills": ["Python", "Machine Learning", "scikit-learn", "NLP", "Pandas", "PyTorch", "Git"], "degree": "M.S. Data Science", "school": "Lakeview Institute", "project": "Support ticket intent classifier", "project_description": "Trained and evaluated an NLP classification model with scikit-learn and PyTorch on customer support text."},
    {"name": "Samira Okafor", "email": "samira.okafor@example.test", "location": "Atlanta, GA", "years": 5, "skills": ["Python", "SQL", "Pandas", "Machine Learning", "Power BI", "AWS", "Git"], "degree": "B.S. Applied Mathematics", "school": "Piedmont State College", "project": "Product adoption analysis", "project_description": "Analyzed product funnels with SQL and pandas, tested adoption hypotheses, and delivered Power BI reporting."},
    {"name": "Taylor Brooks", "email": "taylor.brooks@example.test", "location": "Denver, CO", "years": 2, "skills": ["Python", "FastAPI", "SQL", "REST API", "Git", "Machine Learning", "scikit-learn"], "degree": "B.S. Software Engineering", "school": "Front Range University", "project": "Inventory demand forecasting", "project_description": "Created Python forecasting models and served them through a FastAPI REST API backed by SQL."},
    {"name": "Riley Morgan", "email": "riley.morgan@example.test", "location": "Boston, MA", "years": 1, "skills": ["Python", "Pandas", "SQL", "Machine Learning", "Git", "TensorFlow"], "degree": "B.S. Statistics", "school": "Commonwealth College", "project": "Transit delay prediction", "project_description": "Compared TensorFlow and baseline machine learning models using Python, pandas, and SQL data."},
]


def seed_demo(db: Session, owner_id: int) -> dict:
    if db.scalar(select(Job.id).where(Job.owner_id == owner_id).limit(1)):
        return {"created": False, "message": "This workspace already has data. Demo records were not duplicated."}
    jobs = []
    for values in DEMO_JOBS:
        job = Job(owner_id=owner_id, **values)
        db.add(job)
        db.flush()
        jobs.append(job)
    for index, profile in enumerate(DEMO_CANDIDATES):
        candidate = Candidate(owner_id=owner_id, full_name=profile["name"], email=profile["email"], location=profile["location"], total_experience=profile["years"])
        db.add(candidate)
        db.flush()
        for name in profile["skills"]:
            skill = ensure_skill(db, name)
            db.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, evidence="Extracted from synthetic sample resume"))
        db.add(Education(candidate_id=candidate.id, degree=profile["degree"], institution=profile["school"]))
        db.add(Project(candidate_id=candidate.id, name=profile["project"], description=profile["project_description"], technologies=profile["skills"][:4]))
        db.add(Resume(candidate_id=candidate.id, filename=f"sample_resume_{index + 1:02}.docx", stored_path=f"sample://resume-{index + 1}", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", extracted_text=f"{profile['name']}\n{profile['email']}\n{profile['location']}\n{profile['years']} years experience\nSkills\n{', '.join(profile['skills'])}\nEducation\n{profile['degree']}\n{profile['school']}\nProjects\n{profile['project']}\n{profile['project_description']}"))
        for job in jobs:
            application = Application(job_id=job.id, candidate_id=candidate.id, status="Shortlisted" if index == 0 and job.id == jobs[0].id else "New")
            db.add(application)
            db.flush()
            score_application(db, application, job)
    db.commit()
    return {"created": True, "jobs": len(jobs), "candidates": len(DEMO_CANDIDATES), "applications": len(jobs) * len(DEMO_CANDIDATES)}
