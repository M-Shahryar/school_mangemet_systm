from datetime import date as dt_date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from ..models.attendance import Attendance
from ..models.student import Student
from ..models.enrollment import Enrollment
from ..models.fees import Challan, Payment
from ..models.expenditure import Expenditure
from ..models.stationery import StationerySale

def _to_f(v) -> float:
    if v is None: return 0.0
    if isinstance(v, Decimal): return float(v)
    try: return float(v)
    except: return 0.0

def attendance_rate_on(db: Session, the_date: dt_date) -> float:
    total = db.query(Attendance).filter(Attendance.date == the_date).count()
    if total == 0: return 0.0
    present = db.query(Attendance).filter(Attendance.date == the_date, Attendance.code == "P").count()
    return round((present / total) * 100.0, 2)

def month_fee_kpis(db: Session, month_first: dt_date):
    gross_sum = db.query(func.coalesce(func.sum(Challan.gross), 0)).filter(Challan.month == month_first).scalar()
    disc_sum  = db.query(func.coalesce(func.sum(Challan.discount), 0)).filter(Challan.month == month_first).scalar()
    net_billed = _to_f(gross_sum) - _to_f(disc_sum)

    pay_sum = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
          .join(Challan, Challan.id == Payment.challan_id)
          .filter(Challan.month == month_first)
          .scalar()
    )
    collected = _to_f(pay_sum)
    pending = max(0.0, net_billed - collected)
    challans_count = db.query(Challan).filter(Challan.month == month_first).count()
    unpaid_count   = db.query(Challan).filter(Challan.month == month_first, Challan.status != "PAID").count()
    return dict(challans_count=challans_count, net_billed=round(net_billed,2),
                collected=round(collected,2), pending=round(pending,2), unpaid_count=unpaid_count)

def year_fee_kpis(db: Session, year: int):
    gross_sum = db.query(func.coalesce(func.sum(Challan.gross), 0)).filter(extract("year", Challan.month)==year).scalar()
    disc_sum  = db.query(func.coalesce(func.sum(Challan.discount), 0)).filter(extract("year", Challan.month)==year).scalar()
    net_billed = _to_f(gross_sum) - _to_f(disc_sum)

    pay_sum = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
          .join(Challan, Challan.id == Payment.challan_id)
          .filter(extract("year", Challan.month)==year)
          .scalar()
    )
    collected = _to_f(pay_sum)
    pending = max(0.0, net_billed - collected)
    challans_count = db.query(Challan).filter(extract("year", Challan.month)==year).count()
    unpaid_count   = db.query(Challan).filter(extract("year", Challan.month)==year, Challan.status!="PAID").count()
    return dict(challans_count=challans_count, net_billed=round(net_billed,2),
                collected=round(collected,2), pending=round(pending,2), unpaid_count=unpaid_count)

def month_expenditure(db: Session, month_first: dt_date) -> float:
    y, m = month_first.year, month_first.month
    s = db.query(func.coalesce(func.sum(Expenditure.amount), 0)).filter(
        extract("year", Expenditure.spent_on)==y, extract("month", Expenditure.spent_on)==m
    ).scalar()
    return round(_to_f(s), 2)

def year_expenditure(db: Session, year: int) -> float:
    s = db.query(func.coalesce(func.sum(Expenditure.amount), 0)).filter(
        extract("year", Expenditure.spent_on)==year
    ).scalar()
    return round(_to_f(s), 2)

def month_stationery_income(db: Session, month_first: dt_date) -> float:
    y, m = month_first.year, month_first.month
    s = db.query(func.coalesce(func.sum(StationerySale.amount), 0)).filter(
        extract("year", StationerySale.sale_date)==y, extract("month", StationerySale.sale_date)==m
    ).scalar()
    return round(_to_f(s), 2)

def year_stationery_income(db: Session, year: int) -> float:
    s = db.query(func.coalesce(func.sum(StationerySale.amount), 0)).filter(
        extract("year", StationerySale.sale_date)==year
    ).scalar()
    return round(_to_f(s), 2)

def headline_counts(db: Session):
    students = db.query(Student).count()
    classes  = db.query(Enrollment.klass, Enrollment.section).distinct().count()
    return {"students": students, "classes": classes}
