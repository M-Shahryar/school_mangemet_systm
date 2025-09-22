# app/security/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import jwt, JWTError

from ..settings import settings
from ..views.base import templates  # to render login form

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Simple built-in accounts (change these later or replace with DB lookup) ---
# username -> (password, ROLE)
BUILTIN_USERS = {
    "admin": ("1234", "ADMIN"),
    "director": ("1234", "DIRECTOR"),
}

# --- JWT helpers ---
def create_access_token(data: dict, expires_minutes: int = 8 * 60) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# --- Routes ---
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, error: Optional[str] = None):
    # Slim page: only login — welcome is handled by "/" route
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "error": error}
    )

@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    # 1) Check built-in accounts
    creds = BUILTIN_USERS.get(username.strip().lower())
    if not creds or password != creds[0]:
        # Invalid credentials
        return RedirectResponse(url="/auth/login?error=Invalid+username+or+password", status_code=302)

    role = creds[1]

    # 2) Create token with role
    token = create_access_token({"sub": username, "role": role})

    # 3) Redirect by role
    redirect_to = "/admin/dashboard" if role == "ADMIN" else "/director/dashboard"

    resp = RedirectResponse(url=redirect_to, status_code=302)
    # Cookie settings: httponly keeps it out of JS; adjust 'secure' if you serve on HTTPS
    resp.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # set True if you're serving over HTTPS
        max_age=60 * 60 * 8,
    )
    return resp

@router.post("/logout")
def logout():
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("access_token")
    return resp
