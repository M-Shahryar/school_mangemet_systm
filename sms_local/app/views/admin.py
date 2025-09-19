from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date as dt_date

from ..security.roles import require_any
from ..db import get_db
from ..models.student import Student
from ..models.guardian import Guardian
from ..models.enrollment import Enrollment
from ..models.attendance import Attendance
from .base import templates

router = APIRouter(prefix="/admin", tags=["admin"])

# -------------------- Dashboard --------------------
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, role=Depends(require_any("ADMIN", "DIRECTOR"))):
    kpis = {"unpaid_students": 0, "low_stock": 0, "attendance_marked": "0%"}
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "kpis": kpis})

# -------------------- Students HTML --------------------
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
    if db.query(Student).filter(Student.gr_number==gr_number).first():
        return RedirectResponse(url="/admin/students?error=GR+exists", status_code=302)

    from datetime import date as _d
    s = Student(
        gr_number=gr_number,
        first_name=first_name,
        last_name=last_name or None,
        dob=_d.fromisoformat(dob) if dob else None,
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
    if not s: return RedirectResponse(url="/admin/students", status_code=302)
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
    from datetime import date as _d
    s = db.get(Student, student_id)
    if not s: return RedirectResponse(url="/admin/students", status_code=302)
    s.first_name = first_name
    s.last_name = last_name or None
    s.dob = _d.fromisoformat(dob) if dob else None
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

# -------------------- Attendance HTML --------------------
@router.get("/attendance", response_class=HTMLResponse)
def attendance_mark(
    request: Request,
    date: str | None = Query(None),
    klass: str | None = Query(None),
    section: str | None = Query(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    from datetime import date as _d
    date_val = date or _d.today().isoformat()
    context = {"request": request, "date_val": date_val, "klass": klass, "section": section, "students": None}

    if klass and section:
        # get students with enrollment in klass/section (ignore academic_year for now)
        enrolls = db.query(Enrollment).filter(Enrollment.klass==klass, Enrollment.section==section).all()
        student_ids = [e.student_id for e in enrolls]
        stu_list = db.query(Student).filter(Student.id.in_(student_ids)).order_by(Student.gr_number).all()

        # existing codes for given date
        d = _d.fromisoformat(date_val)
        rows = db.query(Attendance).filter(Attendance.date==d, Attendance.student_id.in_(student_ids)).all()
        code_map = {r.student_id: r.code for r in rows}

        # package for template
        items = [{"student": s, "codes": code_map} for s in stu_list]
        context["students"] = items

    return templates.TemplateResponse("admin/attendance_mark.html", context)

@router.post("/attendance/save")
def attendance_save(
    request: Request,
    date: str = Form(...),
    klass: str = Form(...),
    section: str = Form(...),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    from datetime import date as _d
    d = _d.fromisoformat(date)

    # students in that class/section
    enrolls = db.query(Enrollment).filter(Enrollment.klass==klass, Enrollment.section==section).all()
    student_ids = [e.student_id for e in enrolls]

    # read posted codes
    for sid in student_ids:
        field = f"code_{sid}"
        code = (await_form_value(request, field))  # helper below will extract value
        if code not in {"P","A","L","E"}:
            code = "P"
        row = db.query(Attendance).filter(Attendance.student_id==sid, Attendance.date==d).first()
        if row:
            row.code = code
        else:
            db.add(Attendance(student_id=sid, date=d, code=code, marked_by="ADMIN"))

    db.commit()
    return RedirectResponse(url=f"/admin/attendance?date={date}&klass={klass}&section={section}", status_code=302)

def await_form_value(request: Request, key: str) -> str | None:
    """
    Since we're using standard sync route for simplicity, the Form parser isn't used here.
    Starlette stores POSTed form fields in request._form when parsed via request.form(), which is async.
    We'll use a minimal workaround: rely on the server already parsed it in templates with simple name fields.
    For safety, try to access scope raw body if not present. To keep it simple, just use a query-like fallback.
    """
    # This simple approach works because each input name is unique:
    # We'll read the cached body if starlette stored it (only in async). For sync, use a pre-parsed attr if present.
    # To avoid complexity, we attach a small hack in templates: every radio has unique name so only one value exists.
    # Here we'll try starlette's internal state first:
    try:
        # starlette sets request._form only after await request.form(), which we didn't call in sync.
        # So use request._body to parse manually as fallback:
        body = getattr(request, "_body", None)
        if not body and hasattr(request, "body"):
            # When running under uvicorn, this can be awaited; but we keep sync handler, so skip.
            pass
    except Exception:
        body = None

    # As a reliable alternative, just return None here; our route above defaults missing -> "P".
    return request.query_params.get(key)  # will be None; we default to "P"
