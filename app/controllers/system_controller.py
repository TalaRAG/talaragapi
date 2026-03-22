from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_admin_user
from app.helpers.api_helpers import generate_jwt
from app.models.user import User
from app.operations.system.login import Login
from app.schemas.system import EnvironmentResponse, LoginPayload, LoginResponse


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(request: Request, payload: LoginPayload, session: Session = Depends(get_db)):
    cmd = Login(session=session, email=payload.email, password=payload.password)
    cmd.execute()

    if cmd.valid():
        token = generate_jwt(cmd.user.to_dict(), request.app.state.settings.SECRET_KEY)
        return {"token": token}

    return JSONResponse(status_code=422, content=cmd.payload)


@router.get("/system/environment", response_model=EnvironmentResponse)
def environment(
    request: Request,
    _current_user: User = Depends(require_admin_user),
):
    return {
        "variables": request.app.state.settings.public_environment(),
        "secret_statuses": request.app.state.settings.secret_statuses(),
    }
