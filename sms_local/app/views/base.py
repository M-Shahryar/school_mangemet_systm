# app/views/base.py
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from ..settings import settings

templates = Jinja2Templates(directory="app/templates")

def _role_from_request(request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("role")
    except JWTError:
        return None

# Make available inside Jinja: {{ current_role(request) }}
templates.env.globals["current_role"] = _role_from_request
