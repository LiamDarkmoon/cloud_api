from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
import jwt
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from models import TokenData, UserData
from database import db
from config import config
from pwdlib import PasswordHash

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash password plano"""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return password_hash.verify(plain_password, hashed_password)


async def get_user(username: str):

    user = (db().table("users").select("*").eq("email", username).execute()).data

    if not user:
        return None

    return UserData(**user[0])


def create_access_token(data: dict):

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

    return encoded_jwt


def verify_token(token: str, credentials_exception):

    try:
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM],
        )
        email = payload.get("email")
        if not email:
            raise credentials_exception
        token_data = TokenData(email=email)

    except jwt.ExpiredSignatureError:
        print("Token expirado")
        raise credentials_exception

    except InvalidTokenError as e:
        print("Token inválido:", str(e))
        raise credentials_exception

    return token_data


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """Get the current user based on the provided JWT token."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(token, credentials_exception)

    user = (
        db().table("users").select("*").eq("email", token_data.email).execute()
    ).data[0]

    if user is None:
        raise credentials_exception

    return UserData(**user)
