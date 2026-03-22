from sqlalchemy import select

from app.helpers.api_helpers import build_password_hash
from app.models.user import User


DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "password"
DEFAULT_ADMIN_FIRST_NAME = "Admin"
DEFAULT_ADMIN_LAST_NAME = "User"


class Seed:
    def __init__(self, session):
        self.session = session
        self.user = None
        self.created = False

    def execute(self):
        self.user = self.session.scalar(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))

        if self.user is None:
            self.user = User(
                email=DEFAULT_ADMIN_EMAIL,
                first_name=DEFAULT_ADMIN_FIRST_NAME,
                last_name=DEFAULT_ADMIN_LAST_NAME,
                password_hash=build_password_hash(DEFAULT_ADMIN_PASSWORD),
                status="active",
                is_admin=True,
            )
            self.session.add(self.user)
            self.created = True
        else:
            self.user.first_name = DEFAULT_ADMIN_FIRST_NAME
            self.user.last_name = DEFAULT_ADMIN_LAST_NAME
            self.user.password_hash = build_password_hash(DEFAULT_ADMIN_PASSWORD)
            self.user.status = "active"
            self.user.is_admin = True

        self.session.commit()
        self.session.refresh(self.user)
