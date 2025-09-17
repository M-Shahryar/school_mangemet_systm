from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from ..security.roles import require_role
from .base import templates

router = APIRouter(prefix="/director", tags=["director"])

@router.get("/dashboard", response_class=HTMLResponse)
async def director_dashboard(request: Request, role=Depends(require_role("DIRECTOR"))):
    kpis = {
        "today_fee": 0,
        "month_fee": 0,
        "month_expense": 0,
        "attendance_rate": "0%"
    }
    return templates.TemplateResponse("director/dashboard.html", {"request": request, "kpis": kpis})
