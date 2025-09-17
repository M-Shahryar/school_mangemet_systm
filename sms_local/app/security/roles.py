from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from ..settings import settings

def get_current_role(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("role")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

def require_role(required: str):
    def wrapper(request: Request):
        role = get_current_role(request)
        if role != required:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
        return role
    return wrapper
