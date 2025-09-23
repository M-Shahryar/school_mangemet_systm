from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Numeric, Enum, ForeignKey
from ..db import Base
from enum import Enum as PyEnum
import uuid
from datetime import date

def uid(): return str(uuid.uuid4())

class MoveKind(PyEnum):
    IN = "IN"
    OUT = "OUT"

class StockMove(Base):
    __tablename__ = "stock_move"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    item_id: Mapped[str] = mapped_column(String, ForeignKey("stationery_item.id"), index=True)
    move_date: Mapped[date] = mapped_column(Date, index=True)
    qty: Mapped[float] = mapped_column(Numeric(12,2))
    kind: Mapped[str] = mapped_column(Enum(MoveKind))
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    # Link to sale (optional)
    sale_id: Mapped[str | None] = mapped_column(String, ForeignKey("stationery_sale.id"), nullable=True)

    item = relationship("StationeryItem", back_populates="moves")
