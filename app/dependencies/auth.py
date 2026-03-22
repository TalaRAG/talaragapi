from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.helpers.api_helpers import decode_jwt
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="authentication required")

    payload = decode_jwt(credentials.credentials, request.app.state.settings.SECRET_KEY)
    if not payload or "id" not in payload:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid authorization")

    user = session.get(User, payload["id"])
    if user is None or user.status == "deleted":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid authorization")

    return user


def require_active_user(current_user: User = Depends(get_current_user)):
    if current_user.status == "inactive":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    return current_user


def require_admin_user(request: Request, current_user: User = Depends(require_active_user)):
    if not current_user.admin(request.app.state.settings.ADMIN_EMAILS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin required")
    return current_user
