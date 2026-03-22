from pydantic import BaseModel


class LoginPayload(BaseModel):
    email: str | None = None
    password: str | None = None


class LoginResponse(BaseModel):
    token: str
