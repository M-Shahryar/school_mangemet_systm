from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, Numeric
from ..db import Base
from datetime import date
import uuid

def uid(): return str(uuid.uuid4())

class StationerySale(Base):
    __tablename__ = "stationery_sale"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    sale_date: Mapped[date] = mapped_column(Date, index=True)
    item: Mapped[str] = mapped_column(String(128))
    qty: Mapped[float] = mapped_column(Numeric(10,2))
    amount: Mapped[float] = mapped_column(Numeric(12,2))
    note: Mapped[str | None] = mapped_column(String, nullable=True)
