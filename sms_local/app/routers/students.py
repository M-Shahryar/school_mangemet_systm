from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, Base, engine
from ..security.roles import require_any
from ..models.student import Student
from ..models.guardian import Guardian
from ..models.enrollment import Enrollment
from ..schemas.students import StudentCreate, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])

# Ensure tables exist (dev convenience)
Base.metadata.create_all(bind=engine)

@router.get("")
def list_students(db: Session = Depends(get_db), role=Depends(require_any("ADMIN", "DIRECTOR"))):
    return db.query(Student).order_by(Student.gr_number).all()

@router.post("")
def create_student(body: StudentCreate, db: Session = Depends(get_db), role=Depends(require_any("ADMIN", "DIRECTOR"))):
    if db.query(Student).filter(Student.gr_number == body.gr_number).first():
        raise HTTPException(400, "GR number already exists")
    s = Student(
        gr_number=body.gr_number,
        first_name=body.first_name,
        last_name=body.last_name,
        dob=body.dob,
        gender=body.gender,
        status=body.status or "ACTIVE",
    )
    db.add(s); db.flush()

    if body.guardian:
        g = Guardian(**body.guardian.model_dump())
        db.add(g); db.flush()
        s.guardians.append(g)

    if body.enrollment:
        e = Enrollment(student_id=s.id, **body.enrollment.model_dump())
        db.add(e)

    db.commit(); db.refresh(s)
    return s

@router.get("/{student_id}")
def get_student(student_id: str, db: Session = Depends(get_db), role=Depends(require_any("ADMIN", "DIRECTOR"))):
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(404, "Not found")
    return s

@router.patch("/{student_id}")
def update_student(student_id: str, body: StudentUpdate, db: Session = Depends(get_db), role=Depends(require_any("ADMIN", "DIRECTOR"))):
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(404, "Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db), role=Depends(require_any("ADMIN", "DIRECTOR"))):
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(404, "Not found")
    db.delete(s); db.commit()
    return {"ok": True}
