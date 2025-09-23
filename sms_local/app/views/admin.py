# app/views/admin.py
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload
from datetime import date as dt_date
from decimal import Decimal

import io, csv
from ..security.roles import require_any
from ..db import get_db
from ..models.student import Student
from ..models.guardian import Guardian
from ..models.enrollment import Enrollment
from ..models.attendance import Attendance
from ..models.fees import Challan, Payment
from .base import templates
from ..models.expenditure import Expenditure
from ..models.stationery import StationerySale

router = APIRouter(prefix="/admin", tags=["admin"])

# ===================== Dashboard =====================
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, role=Depends(require_any("ADMIN", "DIRECTOR"))):
    # TODO: replace with real KPIs
    kpis = {"unpaid_students": 0, "low_stock": 0, "attendance_marked": "0%"}
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "kpis": kpis})

# ===================== Students (CRUD) =====================
@router.get("/students", response_class=HTMLResponse)
def students_list(
    request: Request,
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
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
def student_edit(
    student_id: str,
    request: Request,
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
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
    from datetime import date as _d
    s = db.get(Student, student_id)
    if not s:
        return RedirectResponse(url="/admin/students", status_code=302)
    s.first_name = first_name
    s.last_name = last_name or None
    s.dob = _d.fromisoformat(dob) if dob else None
    s.gender = gender or None
    s.status = status or "ACTIVE"
    db.commit()
    return RedirectResponse(url="/admin/students", status_code=302)

@router.post("/students/{student_id}/delete")
def student_delete(
    student_id: str,
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    s = db.get(Student, student_id)
    if s:
        db.delete(s); db.commit()
    return RedirectResponse(url="/admin/students", status_code=302)

# ===================== Attendance =====================
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
        enrolls = db.query(Enrollment).filter(Enrollment.klass == klass, Enrollment.section == section).all()
        student_ids = [e.student_id for e in enrolls]
        stu_list = db.query(Student).filter(Student.id.in_(student_ids)).order_by(Student.gr_number).all()

        d = _d.fromisoformat(date_val)
        rows = db.query(Attendance).filter(Attendance.date == d, Attendance.student_id.in_(student_ids)).all()
        code_map = {r.student_id: r.code for r in rows}

        items = [{"student": s, "codes": code_map} for s in stu_list]
        context["students"] = items

    return templates.TemplateResponse("admin/attendance_mark.html", context)

@router.post("/attendance/save")
async def attendance_save(
    request: Request,
    date: str = Form(...),
    klass: str = Form(...),
    section: str = Form(...),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    from datetime import date as _d
    from ..models.attendance import Attendance
    d = _d.fromisoformat(date)

    enrolls = db.query(Enrollment).filter(Enrollment.klass == klass, Enrollment.section == section).all()
    student_ids = [e.student_id for e in enrolls]

    form = await request.form()
    for sid in student_ids:
        code = form.get(f"code_{sid}", "P")
        if code not in {"P", "A", "L", "E"}:
            code = "P"
        row = db.query(Attendance).filter(Attendance.student_id == sid, Attendance.date == d).first()
        if row:
            row.code = code
        else:
            db.add(Attendance(student_id=sid, date=d, code=code, marked_by="ADMIN"))

    db.commit()
    return RedirectResponse(url=f"/admin/attendance?date={date}&klass={klass}&section={section}", status_code=302)

@router.get("/attendance/list", response_class=HTMLResponse)
def attendance_list(
    request: Request,
    date: str | None = Query(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    from datetime import date as _d
    dval = date or _d.today().isoformat()
    d = _d.fromisoformat(dval)
    rows = (
        db.query(Attendance, Student)
          .join(Student, Student.id == Attendance.student_id)
          .filter(Attendance.date == d)
          .order_by(Student.gr_number)
          .all()
    )
    view_rows = [{"student": s, "code": a.code} for a, s in rows]
    ctx = {"request": request, "rows": view_rows, "date_val": dval}
    return templates.TemplateResponse("admin/attendance_list.html", ctx)

# ===================== Fees / Challans =====================
@router.get("/fees/new", response_class=HTMLResponse)
def fees_new(request: Request, role=Depends(require_any("ADMIN", "DIRECTOR"))):
    return templates.TemplateResponse("admin/fees_batch.html", {"request": request})

@router.post("/fees/challan")
def fees_create_single(
    request: Request,
    student_id: str | None = Form(None),
    gr_number: str | None = Form(None),
    month: str = Form(...),          # YYYY-MM-01
    gross: float = Form(...),
    discount: float = Form(0),
    due_date: str | None = Form(None),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    from datetime import date as _d

    # resolve student by id or GR#
    s = None
    if student_id:
        s = db.get(Student, student_id)
    if not s and gr_number:
        s = db.query(Student).filter(Student.gr_number == gr_number).first()
    if not s:
        return RedirectResponse(url="/admin/fees/new?error=Student+not+found", status_code=302)

    # parse dates
    try:
        m = _d.fromisoformat(month)
    except ValueError:
        return RedirectResponse(url="/admin/fees/new?error=Month+must+be+YYYY-MM-01", status_code=302)
    d = None
    if due_date:
        try:
            d = _d.fromisoformat(due_date)
        except ValueError:
            return RedirectResponse(url="/admin/fees/new?error=Due+date+must+be+YYYY-MM-DD", status_code=302)

    exists = db.query(Challan).filter(Challan.student_id == s.id, Challan.month == m).first()
    if exists:
        return RedirectResponse(url=f"/admin/fees/challans?month={month}&info=Challan+already+exists", status_code=302)

    c = Challan(student_id=s.id, month=m, due_date=d, gross=gross, discount=discount, note=note)
    db.add(c); db.commit()
    return RedirectResponse(url=f"/admin/fees/challans?month={month}&info=Created", status_code=302)

@router.get("/fees/challans", response_class=HTMLResponse)
def fees_list(
    request: Request,
    month: str | None = Query(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    from datetime import date as _d

    # Default month = first day of current month
    month_val = month or _d.today().replace(day=1).isoformat()
    try:
        m = _d.fromisoformat(month_val)
    except ValueError:
        m = _d.today().replace(day=1)
        month_val = m.isoformat()

    # Join students to show name/GR; convert Decimal/Date to plain types
    pairs = (
        db.query(Challan, Student)
          .join(Student, Student.id == Challan.student_id)
          .filter(Challan.month == m)
          .all()
    )

    rows = []
    for c, s in pairs:
        gross = float(c.gross) if isinstance(c.gross, Decimal) else float(c.gross or 0)
        discount = float(c.discount) if isinstance(c.discount, Decimal) else float(c.discount or 0)
        rows.append({
            "id": c.id,
            "student_name": f"{s.first_name} {s.last_name or ''}".strip(),
            "gr_number": s.gr_number,
            "month": c.month.isoformat(),
            "gross": gross,
            "discount": discount,
            "status": c.status,
        })

    ctx = {
        "request": request,
        "rows": rows,                    # safe, can be []
        "month": month_val,
        "today": _d.today().isoformat(),
        "info": request.query_params.get("info"),
        "error": request.query_params.get("error"),
    }
    return templates.TemplateResponse("admin/challan_list.html", ctx)

@router.post("/fees/pay")
def fees_pay(
    request: Request,
    challan_id: str = Form(...),
    amount: float = Form(...),
    paid_at: str = Form(...),
    method: str = Form("CASH"),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN", "DIRECTOR")),
):
    from datetime import date as _d
    c = db.get(Challan, challan_id)
    if not c:
        return RedirectResponse(url="/admin/fees/challans", status_code=302)

    p = Payment(challan_id=challan_id, amount=amount, method=method, paid_at=_d.fromisoformat(paid_at))
    db.add(p); db.flush()

    net = float(c.gross) - float(c.discount)
    total = sum(float(x.amount) for x in c.payments) + float(amount)
    c.status = "PAID" if total >= net - 1e-6 else ("PARTIAL" if total > 0 else "PENDING")
    db.commit()
    return RedirectResponse(url=f"/admin/fees/challans?month={c.month.isoformat()}", status_code=302)

# -------------------- Fees: Batch Generate & Unpaid CSV --------------------

@router.post("/fees/challan/batch")
def fees_create_batch(
    request: Request,
    klass: str = Form(...),
    section: str = Form(...),
    month: str = Form(...),
    gross: float = Form(...),
    discount: float = Form(0),
    due_date: str | None = Form(None),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN","DIRECTOR")),
):
    from datetime import date as _d
    from ..models.fees import Challan

    # parse dates
    try:
        m = _d.fromisoformat(month)
    except ValueError:
        return RedirectResponse(url="/admin/fees/new?error=Month+must+be+YYYY-MM-01", status_code=302)
    d = None
    if due_date:
        try:
            d = _d.fromisoformat(due_date)
        except ValueError:
            return RedirectResponse(url="/admin/fees/new?error=Due+date+must+be+YYYY-MM-DD", status_code=302)

    # all students enrolled in class/section
    enrolls = db.query(Enrollment).filter(Enrollment.klass==klass, Enrollment.section==section).all()
    student_ids = [e.student_id for e in enrolls]
    if not student_ids:
        return RedirectResponse(url="/admin/fees/new?error=No+students+found+for+that+class/section", status_code=302)

    created = 0
    skipped = 0
    for sid in student_ids:
        exists = db.query(Challan).filter(Challan.student_id==sid, Challan.month==m).first()
        if exists:
            skipped += 1
            continue
        c = Challan(student_id=sid, month=m, due_date=d, gross=gross, discount=discount, note=note)
        db.add(c)
        created += 1
    db.commit()

    info = f"Created:{created},Skipped:{skipped}"
    return RedirectResponse(url=f"/admin/fees/challans?month={month}&info={info}", status_code=302)

@router.get("/fees/unpaid.csv")
def fees_unpaid_csv(
    month: str = Query(..., description="YYYY-MM-01"),
    klass: str | None = Query(None),
    section: str | None = Query(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN","DIRECTOR")),
):
    from datetime import date as _d
    from ..models.fees import Challan

    # parse month
    try:
        m = _d.fromisoformat(month)
    except ValueError:
        # serve an empty CSV with note
        m = _d.today().replace(day=1)

    # base query: unpaid challans in the month
    q = db.query(Challan, Student).join(Student, Student.id==Challan.student_id).filter(
        Challan.month==m, Challan.status!="PAID"
    )

    # optional class/section filter via enrollment
    if klass and section:
        # get student ids for class/section
        erows = db.query(Enrollment.student_id).filter(Enrollment.klass==klass, Enrollment.section==section).all()
        ids = [r[0] for r in erows]
        if ids:
            q = q.filter(Challan.student_id.in_(ids))
        else:
            # no students — return empty CSV
            buffer = io.StringIO()
            w = csv.writer(buffer)
            w.writerow(["GR Number", "Student Name", "Month", "Gross", "Discount", "Status"])
            return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv",
                                     headers={"Content-Disposition": f'attachment; filename="unpaid_{month}.csv"'})

    rows = q.all()

    # write CSV
    buffer = io.StringIO()
    w = csv.writer(buffer)
    w.writerow(["GR Number", "Student Name", "Month", "Gross", "Discount", "Status"])
    for c, s in rows:
        w.writerow([
            s.gr_number,
            f"{s.first_name} {s.last_name or ''}".strip(),
            c.month.isoformat(),
            f"{float(c.gross):.2f}",
            f"{float(c.discount):.2f}",
            c.status,
        ])

    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="unpaid_{month}.csv"'})


# -------------------- Expenditures (CRUD lite) --------------------
@router.get("/expenses", response_class=HTMLResponse)
def expenses_list(request: Request, db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    rows = db.query(Expenditure).order_by(Expenditure.spent_on.desc()).all()
    return templates.TemplateResponse("admin/expenditures_list.html", {"request": request, "rows": rows})

@router.get("/expenses/new", response_class=HTMLResponse)
def expenses_new(request: Request, role=Depends(require_any("ADMIN","DIRECTOR"))):
    return templates.TemplateResponse("admin/expenditure_form.html", {"request": request})

@router.post("/expenses/new")
def expenses_create(
    spent_on: str = Form(...),
    head: str = Form(...),
    amount: float = Form(...),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN","DIRECTOR")),
):
    from datetime import date as _d
    e = Expenditure(spent_on=_d.fromisoformat(spent_on), head=head, amount=amount, note=note or None)
    db.add(e); db.commit()
    return RedirectResponse(url="/admin/expenses", status_code=302)

@router.post("/expenses/{eid}/delete")
def expenses_delete(eid: str, db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    e = db.get(Expenditure, eid)
    if e:
        db.delete(e); db.commit()
    return RedirectResponse(url="/admin/expenses", status_code=302)

# -------------------- Inventory Sales (income log) --------------------
@router.get("/inventory/sales", response_class=HTMLResponse)
def inv_sales_list(request: Request, db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    rows = db.query(InventorySale).order_by(InventorySale.sale_date.desc()).all()
    return templates.TemplateResponse("admin/inventory_sales_list.html", {"request": request, "rows": rows})

@router.get("/inventory/sales/new", response_class=HTMLResponse)
def inv_sales_new(request: Request, role=Depends(require_any("ADMIN","DIRECTOR"))):
    return templates.TemplateResponse("admin/inventory_sale_form.html", {"request": request})

@router.post("/inventory/sales/new")
def inv_sales_create(
    sale_date: str = Form(...),
    item: str = Form(...),
    qty: float = Form(...),
    amount: float = Form(...),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN","DIRECTOR")),
):
    from datetime import date as _d
    r = InventorySale(sale_date=_d.fromisoformat(sale_date), item=item, qty=qty, amount=amount, note=note or None)
    db.add(r); db.commit()
    return RedirectResponse(url="/admin/inventory/sales", status_code=302)

@router.post("/inventory/sales/{rid}/delete")
def inv_sales_delete(rid: str, db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    r = db.get(InventorySale, rid)
    if r:
        db.delete(r); db.commit()
    return RedirectResponse(url="/admin/inventory/sales", status_code=302)


# -------------------- Expenditures (CRUD lite) --------------------

@router.get("/expenses", response_class=HTMLResponse)
def expenses_list(request, db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    rows = db.query(Expenditure).order_by(Expenditure.spent_on.desc()).all()
    return templates.TemplateResponse("admin/expenditures_list.html", {"request": request, "rows": rows})

@router.get("/expenses/new", response_class=HTMLResponse)
def expenses_new(request, role=Depends(require_any("ADMIN","DIRECTOR"))):
    return templates.TemplateResponse("admin/expenditure_form.html", {"request": request})

@router.post("/expenses/new")
def expenses_create(
    spent_on: str = Form(...),
    head: str = Form(...),
    amount: float = Form(...),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
    role=Depends(require_any("ADMIN","DIRECTOR")),
):
    from datetime import date as _d
    e = Expenditure(spent_on=_d.fromisoformat(spent_on), head=head, amount=amount, note=note or None)
    db.add(e); db.commit()
    return RedirectResponse(url="/admin/expenses", status_code=302)

@router.post("/expenses/{eid}/delete")
def expenses_delete(eid: str, db: Session = Depends(get_db), role=Depends(require_any("ADMIN","DIRECTOR"))):
    e = db.get(Expenditure, eid)
    if e:
        db.delete(e); db.commit()
    return RedirectResponse(url="/admin/expenses", status_code=302)

