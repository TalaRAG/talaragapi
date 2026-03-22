from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash


def build_password_hash(password):
    return generate_password_hash(password)


def password_match(password, password_hash):
    return check_password_hash(password_hash, password)


def build_jwt_header(token):
    return {"Authorization": f"Bearer {token}"}


def generate_jwt(user_object, secret_key):
    payload = dict(user_object)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=60)
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt(token, secret_key):
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
