from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import date as dt_date

from ..security.roles import require_role
from ..db import get_db
from ..services.kpis import (
    attendance_rate_on, month_fee_kpis, year_fee_kpis,
    month_expenditure, year_expenditure,
    month_stationery_income, year_stationery_income,
    headline_counts
)
from ..models.expenditure import Expenditure
from .base import templates

router = APIRouter(prefix="/director", tags=["director"])

@router.get("/dashboard", response_class=HTMLResponse)
def director_dashboard(
    request: Request,
    month: str | None = Query(None, description="YYYY-MM-01"),
    year: int | None = Query(None),
    db: Session = Depends(get_db),
    role=Depends(require_role("DIRECTOR")),
):
    today = dt_date.today()
    month_first = dt_date.fromisoformat(month) if month else today.replace(day=1)
    year_val = year or today.year

    heads = headline_counts(db)
    att_today = attendance_rate_on(db, today)

    fee_m = month_fee_kpis(db, month_first)
    exp_m = month_expenditure(db, month_first)
    stn_m = month_stationery_income(db, month_first)
    profit_m = round((fee_m["collected"] + stn_m) - exp_m, 2)

    fee_y = year_fee_kpis(db, year_val)
    exp_y = year_expenditure(db, year_val)
    stn_y = year_stationery_income(db, year_val)
    profit_y = round((fee_y["collected"] + stn_y) - exp_y, 2)

    ctx = {
        "request": request,
        "month": month_first.isoformat(),
        "year": year_val,
        "heads": heads,
        "m": {
            "attendance_today": f"{att_today:.2f}%",
            "challans": fee_m["challans_count"],
            "net_billed": f"{fee_m['net_billed']:.2f}",
            "collected": f"{fee_m['collected']:.2f}",
            "stationery_income": f"{stn_m:.2f}",
            "expenditure": f"{exp_m:.2f}",
            "pending": f"{fee_m['pending']:.2f}",
            "unpaid": fee_m["unpaid_count"],
            "profit": f"{profit_m:.2f}",
        },
        "y": {
            "challans": fee_y["challans_count"],
            "net_billed": f"{fee_y['net_billed']:.2f}",
            "collected": f"{fee_y['collected']:.2f}",
            "stationery_income": f"{stn_y:.2f}",
            "expenditure": f"{exp_y:.2f}",
            "pending": f"{fee_y['pending']:.2f}",
            "unpaid": fee_y["unpaid_count"],
            "profit": f"{profit_y:.2f}",
        },
    }
    return templates.TemplateResponse("director/dashboard.html", ctx)

@router.get("/expenditures/today", response_class=HTMLResponse)
def director_exp_today(
    request: Request,
    db: Session = Depends(get_db),
    role=Depends(require_role("DIRECTOR")),
):
    today = dt_date.today()
    rows = (
        db.query(Expenditure)
        .filter(Expenditure.spent_on == today)
        .order_by(Expenditure.spent_on.desc())
        .all()
    )
    total = sum(float(r.amount) for r in rows) if rows else 0.0
    ctx = {"request": request, "rows": rows, "total": f"{total:.2f}", "date": today.isoformat()}
    return templates.TemplateResponse("director/expenditures_today.html", ctx)
