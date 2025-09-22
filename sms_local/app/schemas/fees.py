from pydantic import BaseModel
from datetime import date

class ChallanCreate(BaseModel):
    student_id: str
    month: date         # use first day of month, e.g. 2025-09-01
    due_date: date | None = None
    gross: float
    discount: float = 0
    note: str | None = None

class PaymentCreate(BaseModel):
    challan_id: str
    amount: float
    method: str = "CASH"
    paid_at: date
