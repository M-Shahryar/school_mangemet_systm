from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date as dt_date
from ..db import get_db, Base, engine
from ..security.roles import require_any
from ..models.attendance import Attendance
from ..models.student import Student

router = APIRouter(prefix="/attendance", tags=["attendance"])
Base.metadata.create_all(bind=engine)  # dev convenience

@router.post("/mark")
def mark_attendance(
    student_id: str,
    date: str,
    code: str,
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    if code not in {"P", "A", "L", "E"}:
        raise HTTPException(400, "Invalid code, use P/A/L/E")
    if not db.get(Student, student_id):
        raise HTTPException(404, "Student not found")

    d = dt_date.fromisoformat(date)
    att = db.query(Attendance).filter(Attendance.student_id == student_id, Attendance.date == d).first()
    if att:
        att.code = code
    else:
        att = Attendance(student_id=student_id, date=d, code=code, marked_by=role)
        db.add(att)
    db.commit()
    return {"ok": True}

@router.get("/daily")
def daily_attendance(
    date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    d = dt_date.fromisoformat(date)
    rows = (
        db.query(Attendance.student_id, Attendance.code)
        .filter(Attendance.date == d)
        .all()
    )
    return [{"student_id": r[0], "code": r[1]} for r in rows]
