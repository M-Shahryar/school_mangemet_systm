from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric
from ..db import Base
import uuid

def uid(): return str(uuid.uuid4())

class StationeryItem(Base):
    __tablename__ = "stationery_item"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    sku: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    unit: Mapped[str] = mapped_column(String(16), default="pcs")
    opening_qty: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    sale_price: Mapped[float | None] = mapped_column(Numeric(12,2), nullable=True)

    # optional relationships
    moves = relationship("StockMove", back_populates="item", cascade="all,delete")
