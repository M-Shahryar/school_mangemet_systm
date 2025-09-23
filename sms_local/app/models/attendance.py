from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, ForeignKey, UniqueConstraint
from ..db import Base
from datetime import date
import uuid

def uid(): return str(uuid.uuid4())

class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    student_id: Mapped[str] = mapped_column(ForeignKey("student.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    code: Mapped[str] = mapped_column(String(1))  # P/A/L/E
    marked_by: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_att_student_date"),)
