from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from datetime import datetime, timedelta, timezone
import jwt
import secrets
from typing import Annotated, Optional
from jwt.exceptions import InvalidTokenError
from models import DomainData, RefreshToken, User, UserData
from database import db
from config import config
from pwdlib import PasswordHash
from hashlib import sha256

security = HTTPBearer(auto_error=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
password_hash = PasswordHash.recommended()


def refresh_expire_time():
    return datetime.now(timezone.utc) + timedelta(days=30)


def parse_db_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def generate_api_key(domain: str):
    raw = secrets.token_urlsafe(32)
    return f"cKey_{domain}_{raw}"


def hash_api_key(key: str):
    return sha256(key.encode()).hexdigest()


def hash_password(password: str) -> str:
    """Hash password plano"""
    return password_hash.hash(password)


def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return password_hash.verify(plain_password, hashed_password)


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    api_key = credentials.credentials
    key_hash = hash_api_key(api_key)

    record = (
        db()
        .table("api_keys")
        .select("*")
        .eq("key_hash", key_hash)
        .eq("revoked", False)
        .execute()
        .data
    )

    if not record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return record[0]


def store_refresh_token_db(token_data: dict):
    result = db().table("tokens").insert(token_data).execute().data[0]["id"]
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store refresh token",
        )
    return result


def verify_refresh_token_db(token: str):

    token_hash = hash_token(token)

    record = (
        db()
        .table("tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .eq("revoked", False)
        .execute()
    ).data[0]
    expire = parse_db_datetime(record["expires_at"])
    if not record or expire < datetime.now(timezone.utc):
        return None

    return record


def revoke_refresh_token_db(id: int):
    db().table("tokens").update({"revoked": True}).eq("id", id).execute()
    return


def get_user(email: str):

    user = (db().table("users").select("*").eq("email", email).execute()).data[0]

    if not user:
        return None

    return UserData(**user)


def get_domain(domain: str):

    user = (db().table("domains").select("*").eq("domain", domain).execute()).data[0]

    if not user:
        return None

    return DomainData(**user)


def create_refresh_token():
    return secrets.token_urlsafe(64)


def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM],
        )

        user_id = payload.get("sub")
        if user_id is None:
            return None

        return int(user_id)

    except jwt.ExpiredSignatureError:
        return None
    except InvalidTokenError:
        return None


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM],
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return int(user_id)

    except jwt.ExpiredSignatureError:
        raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception


def get_token_data(token: Annotated[str, Depends(oauth2_scheme)]):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    return verify_access_token(token, credentials_exception)


def require_user_session(
    token_id: int,
):

    user = db().table("users").select("*").eq("id", token_id).execute().data
    if not user:
        raise HTTPException(status_code=401)

    return UserData(**user[0])


def require_domain_session(
    token_data: int = Depends(get_token_data),
):
    print(token_data.domain)

    domain = (
        db().table("domains").select("*").eq("domain", token_data.domain).execute().data
    )
    if not domain:
        raise HTTPException(status_code=401)

    return DomainData(**domain[0])
