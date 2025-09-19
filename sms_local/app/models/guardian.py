from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from ..db import Base
import uuid
def uid(): return str(uuid.uuid4())

class Guardian(Base):
    __tablename__ = "guardian"
    id: Mapped[str]      = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str]    = mapped_column(String(128))
    phone: Mapped[str]   = mapped_column(String(32))
    email: Mapped[str | None]
    relation: Mapped[str | None]

    students = relationship("Student", secondary="student_guardian", back_populates="guardians")
