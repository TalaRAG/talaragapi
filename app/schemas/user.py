from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    password_confirmation: str | None = None


class UserUpdate(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    password_confirmation: str | None = None


class UserOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    status: str


class UserCollection(BaseModel):
    records: list[UserOut]
    total_pages: int
    current_page: int
    next_page: int | None
    prev_page: int | None
