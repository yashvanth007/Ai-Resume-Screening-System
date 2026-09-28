import io

from docx import Document

from app.api.routes.resumes import validate_file
from app.services.resume_parser import extract_text, parse_resume


def document_bytes(text: str) -> bytes:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_docx_extraction_and_resume_fields():
    content = document_bytes("Casey Sample\ncasey@example.test\n3 years experience\nSkills\nPython, FastAPI, PostgreSQL\nEducation\nB.S. Computer Science\nProjects\nResume matching API")
    text = extract_text("sample.docx", content)
    parsed = parse_resume(text)
    assert parsed["name"] == "Casey Sample"
    assert parsed["email"] == "casey@example.test"
    assert parsed["experience_years"] == 3
    assert {skill["name"] for skill in parsed["skills"]} >= {"Python", "FastAPI", "PostgreSQL"}
    assert parsed["education"]
    assert parsed["projects"]


def test_empty_or_unsupported_documents_are_rejected():
    try:
        extract_text("blank.pdf", b"%PDF-1.7")
    except Exception:
        pass
    else:
        raise AssertionError("A corrupt PDF should not parse as a resume")
    try:
        validate_file("resume.txt", b"resume")
    except ValueError as error:
        assert "PDF or DOCX" in str(error)
    else:
        raise AssertionError("Unsupported file extensions must be rejected")


def test_upload_validation_checks_signature_and_size():
    try:
        validate_file("fake.pdf", b"not a pdf")
    except ValueError as error:
        assert "signature" in str(error)
    else:
        raise AssertionError("Mismatched file content must be rejected")
