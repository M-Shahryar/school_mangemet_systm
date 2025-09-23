from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from ..db import Base
import uuid
def uid(): return str(uuid.uuid4())

class Enrollment(Base):
    __tablename__ = "enrollment"
    id: Mapped[str]         = mapped_column(String, primary_key=True, default=uid)
    student_id: Mapped[str] = mapped_column(ForeignKey("student.id", ondelete="CASCADE"))
    academic_year: Mapped[str] = mapped_column(String(9))  # e.g. 2025-26
    klass: Mapped[str]      = mapped_column(String(32))    # e.g. Grade 6
    section: Mapped[str]    = mapped_column(String(8))     # e.g. A

    student = relationship("Student", back_populates="enrollments")
