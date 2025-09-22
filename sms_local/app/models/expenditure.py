from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, Numeric
from ..db import Base
from datetime import date
import uuid

def uid(): return str(uuid.uuid4())

class Expenditure(Base):
    __tablename__ = "expenditure"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    head: Mapped[str] = mapped_column(String(64))  # e.g., Utilities, Rent, Salaries
    spent_on: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12,2))
    note: Mapped[str | None] = mapped_column(String, nullable=True)
