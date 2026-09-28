SKILL_CATALOG = {
    "Programming": ["Python", "Java", "JavaScript", "TypeScript", "C++", "C", "Go", "Rust", "Ruby", "R"],
    "Web": ["HTML", "CSS", "React", "Angular", "Vue", "Node.js", "FastAPI", "Django", "Flask", "REST API", "REST APIs", "Express.js"],
    "Database": ["SQL", "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch"],
    "AI/ML": ["Machine Learning", "Deep Learning", "NLP", "Natural Language Processing", "Computer Vision", "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Pandas", "NumPy", "spaCy", "Transformers"],
    "Cloud": ["AWS", "Azure", "GCP", "Google Cloud", "Amazon Web Services"],
    "DevOps": ["Docker", "Kubernetes", "GitHub Actions", "Jenkins", "CI/CD", "Terraform", "Linux", "Git"],
    "Analytics": ["Power BI", "Tableau", "Apache Spark", "Airflow", "Excel"],
}

ALIASES = {
    "REST APIs": "REST API", "Natural Language Processing": "NLP",
    "Amazon Web Services": "AWS", "Google Cloud": "GCP", "sklearn": "scikit-learn",
}
SKILL_CATEGORY = {skill.casefold(): category for category, skills in SKILL_CATALOG.items() for skill in skills}
SKILL_DISPLAY = {skill.casefold(): skill for skills in SKILL_CATALOG.values() for skill in skills}
ALL_SKILLS = sorted(SKILL_CATEGORY, key=len, reverse=True)
