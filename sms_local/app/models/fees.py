from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, ForeignKey, Numeric, Enum
from ..db import Base
from datetime import date
import uuid

def uid() -> str: return str(uuid.uuid4())

class Challan(Base):
    __tablename__ = "challan"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    student_id: Mapped[str] = mapped_column(ForeignKey("student.id", ondelete="CASCADE"), index=True)
    month: Mapped[date] = mapped_column(Date, index=True)             # store as first day of month
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gross: Mapped[float] = mapped_column(Numeric(10,2))
    discount: Mapped[float] = mapped_column(Numeric(10,2), default=0)
    status: Mapped[str] = mapped_column(Enum("PENDING","PAID","PARTIAL","CANCELLED", name="challan_status"), default="PENDING")
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    payments = relationship("Payment", back_populates="challan", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payment"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    challan_id: Mapped[str] = mapped_column(ForeignKey("challan.id", ondelete="CASCADE"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(10,2))
    method: Mapped[str] = mapped_column(Enum("CASH","BANK","ONLINE", name="payment_method"), default="CASH")
    paid_at: Mapped[date] = mapped_column(Date)

    challan = relationship("Challan", back_populates="payments")
