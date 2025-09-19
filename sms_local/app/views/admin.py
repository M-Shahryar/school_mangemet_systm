from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date

from ..security.roles import require_any
from ..db import get_db
from ..models.student import Student
from ..models.guardian import Guardian
from ..models.enrollment import Enrollment
from .base import templates

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, role=Depends(require_any("ADMIN", "DIRECTOR"))):
    kpis = {"unpaid_students": 0, "low_stock": 0, "attendance_marked": "0%"}
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "kpis": kpis})

# ---------------- Students HTML ----------------
@router.get("/students", response_class=HTMLResponse)
def students_list(request: Request, db: Session = Depends(get_db), role=Depends(require_any("ADMIN", "DIRECTOR"))):
    students = db.query(Student).order_by(Student.gr_number).all()
    return templates.TemplateResponse("admin/students_list.html", {"request": request, "students": students})

@router.get("/students/new", response_class=HTMLResponse)
def student_new(request: Request, role=Depends(require_any("ADMIN", "DIRECTOR"))):
    return templates.TemplateResponse("admin/student_form.html", {"request": request, "mode": "Create", "s": None})

@router.post("/students/new")
def student_create(
    request: Request,
    gr_number: str = Form(...),
    first_name: str = Form(...),
    last_name: str | None = Form(None),
    dob: str | None = Form(None),
    gender: str | None = Form(None),
    status: str = Form("ACTIVE"),
    g_name: str | None = Form(None),
    g_phone: str | None = Form(None),
    g_email: str | None = Form(None),
    g_relation: str | None = Form(None),
    en_year: str | None = Form(None),
    en_class: str | None = Form(None),
    en_section: str | None = Form(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    if db.query(Student).filter(Student.gr_number == gr_number).first():
        return RedirectResponse(url="/admin/students?error=GR+exists", status_code=302)

    s = Student(
        gr_number=gr_number,
        first_name=first_name,
        last_name=last_name or None,
        dob=date.fromisoformat(dob) if dob else None,
        gender=gender or None,
        status=status or "ACTIVE",
    )
    db.add(s); db.flush()

    if g_name and g_phone:
        g = Guardian(name=g_name, phone=g_phone, email=g_email or None, relation=g_relation or None)
        db.add(g); db.flush()
        s.guardians.append(g)

    if en_year and en_class and en_section:
        e = Enrollment(student_id=s.id, academic_year=en_year, klass=en_class, section=en_section)
        db.add(e)

    db.commit()
    return RedirectResponse(url="/admin/students", status_code=302)

@router.get("/students/{student_id}/edit", response_class=HTMLResponse)
def student_edit(student_id: str, request: Request, db: Session = Depends(get_db), role=Depends(require_any("ADMIN", "DIRECTOR"))):
    s = db.get(Student, student_id)
    if not s:
        return RedirectResponse(url="/admin/students", status_code=302)
    return templates.TemplateResponse("admin/student_form.html", {"request": request, "mode": "Update", "s": s})

@router.post("/students/{student_id}/edit")
def student_update(
    student_id: str,
    first_name: str = Form(...),
    last_name: str | None = Form(None),
    dob: str | None = Form(None),
    gender: str | None = Form(None),
    status: str = Form("ACTIVE"),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    s = db.get(Student, student_id)
    if not s:
        return RedirectResponse(url="/admin/students", status_code=302)
    s.first_name = first_name
    s.last_name = last_name or None
    s.dob = date.fromisoformat(dob) if dob else None
    s.gender = gender or None
    s.status = status or "ACTIVE"
    db.commit()
    return RedirectResponse(url="/admin/students", status_code=302)

@router.post("/students/{student_id}/delete")
def student_delete(student_id: str, db: Session = Depends(get_db), role=Depends(require_any("ADMIN", "DIRECTOR"))):
    s = db.get(Student, student_id)
    if s:
        db.delete(s); db.commit()
    return RedirectResponse(url="/admin/students", status_code=302)
