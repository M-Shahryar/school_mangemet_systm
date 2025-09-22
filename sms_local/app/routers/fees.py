from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date as dt_date
from decimal import Decimal

from ..db import get_db, Base, engine
from ..security.roles import require_any
from ..models.fees import Challan, Payment
from ..models.student import Student
from ..services.pdf import generate_challan_pdf, challan_pdf_path

router = APIRouter(prefix="/fees", tags=["fees"])
Base.metadata.create_all(bind=engine)  # dev convenience

# ---- Challans ----
@router.post("/challan")
def create_challan(
    student_id: str,
    month: str,
    gross: float,
    discount: float = 0.0,
    due_date: str | None = None,
    note: str | None = None,
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN","DIRECTOR")),
):
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(404, "Student not found")

    try:
        m = dt_date.fromisoformat(month)        # e.g., 2025-09-01
    except ValueError:
        raise HTTPException(400, "Month must be YYYY-MM-01")

    d = None
    if due_date:
        try:
            d = dt_date.fromisoformat(due_date)
        except ValueError:
            raise HTTPException(400, "Due date must be YYYY-MM-DD")

    exists = db.query(Challan).filter(Challan.student_id==student_id, Challan.month==m).first()
    if exists:
        raise HTTPException(400, "Challan already exists for this month")

    c = Challan(student_id=student_id, month=m, due_date=d, gross=gross, discount=discount, note=note)
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id}

@router.get("/unpaid")
def list_unpaid(month: str, db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    m = dt_date.fromisoformat(month)
    rows = db.query(Challan).filter(Challan.month==m, Challan.status!="PAID").all()
    return rows

@router.post("/payment")
def add_payment(challan_id: str, amount: float, method: str = "CASH", paid_at: str = Query(..., description="YYYY-MM-DD"),
                db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    c = db.get(Challan, challan_id)
    if not c:
        raise HTTPException(404, "Challan not found")
    pay_date = dt_date.fromisoformat(paid_at)
    p = Payment(challan_id=challan_id, amount=amount, method=method, paid_at=pay_date)
    db.add(p)
    db.flush()

    # update status
    total_paid = db.query(func.coalesce(func.sum(Payment.amount),0)).filter(Payment.challan_id==challan_id).scalar() or 0
    # ensure numeric
    if isinstance(total_paid, Decimal):
        total_paid = float(total_paid)
    net = float(c.gross) - float(c.discount)
    c.status = "PAID" if total_paid >= net - 1e-6 else ("PARTIAL" if total_paid > 0 else "PENDING")
    db.commit()
    return {"ok": True, "status": c.status}

@router.get("/challan/{challan_id}/pdf")
def challan_pdf(challan_id: str, db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    c = db.get(Challan, challan_id)
    if not c:
        raise HTTPException(404, "Challan not found")

    s = db.get(Student, c.student_id)
    if not s:
        raise HTTPException(404, "Student not found")

    # guardians via relationship (no tricky joins)
    guardians = getattr(s, "guardians", []) or []
    payments = c.payments or []

    path = challan_pdf_path(c.id)
    # Always (re)generate to avoid stale files during dev
    generate_challan_pdf(c, s, guardians, payments)
    return FileResponse(path, media_type="application/pdf", filename=f"challan_{s.gr_number}_{c.month.strftime('%Y_%m')}.pdf")
