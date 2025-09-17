from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

from ..settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

FAKE_USERS = {
    "director": {"username": "director", "password": pwd_context.hash("1234"), "role": "DIRECTOR"},
    "admin": {"username": "admin", "password": pwd_context.hash("1234"), "role": "ADMIN"}
}

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.get("/login")
async def login_form(request: Request):
    return {"msg": "Render login form here (HTML template)"}

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = FAKE_USERS.get(username)
    if not user or not pwd_context.verify(password, user["password"]):
        return {"error": "Invalid credentials"}
    token = create_access_token({"sub": username, "role": user["role"]})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie("access_token", token, httponly=True)
    return response
