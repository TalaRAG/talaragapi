import re

from sqlalchemy import select

from app.helpers.api_helpers import build_password_hash
from app.models.user import User
from app.operations.validator import Validator


EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


class Save(Validator):
    def __init__(
        self,
        session,
        email=None,
        first_name=None,
        last_name=None,
        password=None,
        password_confirmation=None,
        user=None,
    ):
        super().__init__()
        self.session = session
        self.user = user
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
        self.password_confirmation = password_confirmation
        self.payload = {
            "email": [],
            "first_name": [],
            "last_name": [],
            "password": [],
            "password_confirmation": [],
        }

    def execute(self):
        self._validate()

        if self.valid():
            if self.user is None:
                self.user = User(
                    email=self.email,
                    first_name=self.first_name,
                    last_name=self.last_name,
                    password_hash=build_password_hash(self.password),
                    status="active",
                )
                self.session.add(self.user)
            else:
                if self.email:
                    self.user.email = self.email
                if self.first_name:
                    self.user.first_name = self.first_name
                if self.last_name:
                    self.user.last_name = self.last_name
                if self.password:
                    self.user.password_hash = build_password_hash(self.password)

            self.session.commit()
            self.session.refresh(self.user)

    def _validate(self):
        if self.user is None:
            if not self.email:
                self.payload["email"].append("required")
            elif not EMAIL_REGEX.match(self.email):
                self.payload["email"].append("invalid format")
            elif self.session.scalar(select(User).where(User.email == self.email)) is not None:
                self.payload["email"].append("already taken")

            if not self.first_name:
                self.payload["first_name"].append("required")

            if not self.last_name:
                self.payload["last_name"].append("required")

            if not self.password:
                self.payload["password"].append("required")

            if not self.password_confirmation:
                self.payload["password_confirmation"].append("required")

            if self.password and self.password_confirmation and self.password != self.password_confirmation:
                self.payload["password"].append("does not match")
                self.payload["password_confirmation"].append("does not match")
        else:
            if self.email:
                existing = self.session.scalar(
                    select(User).where(User.id != self.user.id).where(User.email == self.email)
                )
                if existing is not None:
                    self.payload["email"].append("already taken")
                elif not EMAIL_REGEX.match(self.email):
                    self.payload["email"].append("invalid format")

            if self.password or self.password_confirmation:
                if not self.password:
                    self.payload["password"].append("required")
                if not self.password_confirmation:
                    self.payload["password_confirmation"].append("required")
                if self.password and self.password_confirmation and self.password != self.password_confirmation:
                    self.payload["password"].append("does not match")
                    self.payload["password_confirmation"].append("does not match")

        self.count_errors()
