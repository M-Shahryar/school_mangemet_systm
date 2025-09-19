from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from ..settings import settings
from ..views.base import templates

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Demo users (we’ll move to DB later)
FAKE_USERS = {
    "director": {"username": "director", "password": pwd_context.hash("1234"), "role": "DIRECTOR"},
    "admin":    {"username": "admin",    "password": pwd_context.hash("1234"), "role": "ADMIN"},
}

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, error: str | None = None):
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": error})

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = FAKE_USERS.get(username)
    if not user or not pwd_context.verify(password, user["password"]):
        # redirect back with error
        resp = RedirectResponse(url="/auth/login?error=Invalid%20credentials", status_code=302)
        return resp

    token = create_access_token({"sub": username, "role": user["role"]})
    resp = RedirectResponse(url="/", status_code=302)
    # secure cookie: httponly; set samesite=lax so form POSTs work
    resp.set_cookie("access_token", token, httponly=True, samesite="lax")
    return resp

@router.post("/logout")
async def logout():
    resp = RedirectResponse(url="/auth/login", status_code=302)
    resp.delete_cookie("access_token")
    return resp
