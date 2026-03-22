from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_active_user
from app.models.user import User
from app.operations.users.save import Save as SaveUser
from app.schemas.user import UserCollection, UserCreate, UserOut, UserUpdate


ITEMS_PER_PAGE = 20
router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserCollection)
def index(
    query: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = ITEMS_PER_PAGE,
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    filters = []
    if query:
        pattern = f"%{query}%"
        filters.append(
            or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )
    if status:
        filters.append(User.status == status)

    count_stmt = select(func.count()).select_from(User)
    for entry in filters:
        count_stmt = count_stmt.where(entry)

    users_stmt = select(User).order_by(User.last_name.asc())
    for entry in filters:
        users_stmt = users_stmt.where(entry)

    total = session.scalar(count_stmt) or 0
    total_pages = max((total + per_page - 1) // per_page, 1)
    users = (
        session.execute(users_stmt.offset((page - 1) * per_page).limit(per_page)).scalars().all()
        if total > 0
        else []
    )

    return {
        "records": [user.to_dict() for user in users],
        "total_pages": total_pages,
        "current_page": page,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None,
    }


@router.get("/{user_id}", response_model=UserOut)
def show(
    user_id: str,
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    user = session.get(User, user_id)
    if user is None:
        return JSONResponse(status_code=404, content={"message": "not found"})
    return user.to_dict()


@router.post("", response_model=UserOut, status_code=201)
def create(
    payload: UserCreate,
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    cmd = SaveUser(
        session=session,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password=payload.password,
        password_confirmation=payload.password_confirmation,
    )
    cmd.execute()

    if cmd.valid():
        return cmd.user.to_dict()
    return JSONResponse(status_code=422, content=cmd.payload)


@router.put("/{user_id}", response_model=UserOut)
def update(
    user_id: str,
    payload: UserUpdate,
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    user = session.get(User, user_id)
    if user is None:
        return JSONResponse(status_code=404, content={"message": "not found"})

    cmd = SaveUser(
        session=session,
        user=user,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password=payload.password,
        password_confirmation=payload.password_confirmation,
    )
    cmd.execute()

    if cmd.valid():
        return cmd.user.to_dict()
    return JSONResponse(status_code=422, content=cmd.payload)


@router.delete("/{user_id}")
def delete(
    user_id: str,
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    user = session.get(User, user_id)
    if user is None:
        return JSONResponse(status_code=404, content={"message": "not found"})

    user.soft_delete()
    session.commit()
    session.refresh(user)
    return {"message": "ok"}
