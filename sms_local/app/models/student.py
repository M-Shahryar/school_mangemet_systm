from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Enum, Table, Column, ForeignKey
from ..db import Base
import uuid

def uid(): return str(uuid.uuid4())

# Student↔Guardian link table
student_guardian = Table(
    "student_guardian",
    Base.metadata,
    Column("student_id", String, ForeignKey("student.id", ondelete="CASCADE"), primary_key=True),
    Column("guardian_id", String, ForeignKey("guardian.id", ondelete="CASCADE"), primary_key=True),
    Column("is_primary", String, default="1")
)

class Student(Base):
    __tablename__ = "student"
    id: Mapped[str]          = mapped_column(String, primary_key=True, default=uid)
    gr_number: Mapped[str]   = mapped_column(String(32), unique=True, index=True)
    first_name: Mapped[str]  = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    dob: Mapped[Date | None]
    gender: Mapped[str | None] = mapped_column(Enum("M","F","O", name="gender"))
    status: Mapped[str]      = mapped_column(String(16), default="ACTIVE")

    guardians = relationship("Guardian", secondary=student_guardian, back_populates="students")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
