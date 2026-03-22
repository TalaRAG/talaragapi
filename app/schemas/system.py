from pydantic import BaseModel


class LoginPayload(BaseModel):
    email: str | None = None
    password: str | None = None


class LoginResponse(BaseModel):
    token: str


class InquirePayload(BaseModel):
    query: str | None = None
    document_types: list[str] = []
    k: int | None = None


class EnvironmentResponse(BaseModel):
    variables: dict[str, str]
