from pydantic import BaseModel, Field
from datetime import date

class GuardianIn(BaseModel):
    name: str
    phone: str
    email: str | None = None
    relation: str | None = None

class EnrollmentIn(BaseModel):
    academic_year: str = Field(..., example="2025-26")
    klass: str
    section: str

class StudentCreate(BaseModel):
    gr_number: str
    first_name: str
    last_name: str | None = None
    dob: date | None = None
    gender: str | None = None  # M/F/O
    status: str | None = "ACTIVE"
    guardian: GuardianIn | None = None
    enrollment: EnrollmentIn | None = None

class StudentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    gender: str | None = None
    status: str | None = None
