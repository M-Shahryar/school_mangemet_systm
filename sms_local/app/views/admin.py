from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from ..security.roles import require_role
from .base import templates

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, role=Depends(require_role("ADMIN"))):
    kpis = {
        "unpaid_students": 0,
        "low_stock": 0,
        "attendance_marked": "0%"
    }
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "kpis": kpis})
