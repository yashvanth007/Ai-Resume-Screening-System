from app.ml.matching import calculate_match, semantic_similarity


def test_required_skills_carry_more_weight_than_preferred():
    result = calculate_match(
        {"description": "Build Python FastAPI SQL REST services", "required_skills": ["Python", "SQL", "FastAPI", "Machine Learning"], "preferred_skills": ["Docker"], "experience_required": 0},
        {"skills": ["Python", "SQL", "FastAPI", "Docker"], "experience_years": 2, "education": [], "projects": [], "certifications": []},
        "Python SQL FastAPI Docker REST services",
    )
    assert result["skill_score"] == 80
    assert result["missing_skills"] == ["Machine Learning"]
    assert "Docker" in result["matched_skills"]
    assert 0 <= result["overall_score"] <= 100


def test_semantic_fallback_is_bounded_and_handles_empty_text():
    assert semantic_similarity("", "python services") == 0
    score = semantic_similarity("Python REST API service", "Python API service development")
    assert 0 < score <= 1


def test_match_score_does_not_use_candidate_name():
    job = {"description": "Python backend APIs", "required_skills": ["Python"], "preferred_skills": [], "experience_required": 0}
    first = calculate_match(job, {"name": "Person One", "skills": ["Python"]}, "Python backend APIs")
    second = calculate_match(job, {"name": "Person Two", "skills": ["Python"]}, "Python backend APIs")
    assert first["overall_score"] == second["overall_score"]
