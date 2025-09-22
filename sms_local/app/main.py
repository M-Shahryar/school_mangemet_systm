# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .settings import settings
from .db import init_db
from .views.base import templates

# Routers / views
from .security.auth import router as auth_router
from .views.director import router as director_router
from .views.admin import router as admin_router
from .routers.students import router as students_api_router
from .routers.attendance import router as attendance_api_router
from .routers.fees import router as fees_api_router

app = FastAPI(title=settings.APP_NAME)

# Ensure DB tables exist on startup (models are imported inside init_db())
@app.on_event("startup")
def _startup():
    init_db()

# Static & templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Welcome page (login only)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request, "title": "Welcome"})

# Include routers
app.include_router(auth_router)
app.include_router(director_router)
app.include_router(admin_router)
app.include_router(students_api_router)
app.include_router(attendance_api_router)
app.include_router(fees_api_router)
