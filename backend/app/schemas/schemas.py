from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    company: str = Field(min_length=1, max_length=180)
    location: str = "Remote"
    employment_type: str = "Full-time"
    experience_required: float = Field(default=0, ge=0, le=60)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    description: str = Field(min_length=30)
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    education_requirement: str | None = None


class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    experience_required: float | None = Field(default=None, ge=0, le=60)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, min_length=30)
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    education_requirement: str | None = None


class CandidateUpdate(BaseModel):
    status: str | None = None
    application_id: int | None = None


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
