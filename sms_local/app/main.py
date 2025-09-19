from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .settings import settings
from .security.auth import router as auth_router
from .views.director import router as director_router
from .views.admin import router as admin_router
from .routers.students import router as students_api_router


app = FastAPI(title=settings.APP_NAME)

# Static files & templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(auth_router)
app.include_router(director_router)
app.include_router(admin_router)
app.include_router(students_api_router)  # JSON API (ADMIN-only)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "title": "Home"})
