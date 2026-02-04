from turtle import update
from typing import Annotated
from fastapi import APIRouter, Body, Request, Response, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import db
from models import ApiKey, Domain, User, UserData, RefreshToken
from config import config
from utils import (
    generate_api_key,
    get_domain,
    hash_password,
    verify_password,
    create_access_token,
    get_user,
    get_domain,
    hash_token,
    create_refresh_token,
    verify_refresh_token_db,
    refresh_expire_time,
    store_refresh_token_db,
    revoke_refresh_token_db,
    generate_api_key,
    hash_api_key,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(credentials: Annotated[OAuth2PasswordRequestForm, Depends()]):

    user = await get_user(credentials.username)

    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user already exists"
        )

    new_user = User(
        email=credentials.username, password=hash_password(credentials.password)
    )

    created_user = (
        db().table("users").insert(new_user.model_dump(exclude={"id"})).execute()
    ).data[0]

    user_token = create_access_token(data={"email": created_user["email"]})

    return {
        "user_token": user_token,
        "user": UserData(**created_user).model_dump(exclude={"password"}),
        "token_type": "user",
    }


@router.post("/login", status_code=status.HTTP_201_CREATED)
async def login(
    credentials: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
):

    user = await get_user(credentials.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials"
        )

    verified = verify_password(credentials.password, user.password)

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials"
        )

    access = create_access_token(user.id)
    refresh = create_refresh_token()
    token_hash = hash_token(refresh)

    token_data = RefreshToken(
        **{
            "user_id": user.id,
            "token_hash": token_hash,
            "expires_at": refresh_expire_time(),
        }
    ).model_dump(mode="json")
    store_refresh_token_db(token_data)

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth/refresh",
    )

    return {"token": access}


@router.post("/logout", status_code=status.HTTP_201_CREATED)
async def logout(
    credentials: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
):
    session_id = get_user(email=credentials.username)

    revoke_refresh_token_db(session_id.id)

    response.delete_cookie(key="refresh_token", path="/auth/refresh")
    return {"ok": True}


@router.post("/logout-all", status_code=status.HTTP_201_CREATED)
async def logout(
    credentials: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
):
    session_id = get_user(email=credentials.username)

    revoke_refresh_token_db(session_id.id)

    response.delete_cookie(key="refresh_token", path="/auth/refresh")
    return {"ok": True}


@router.post("/refresh", status_code=status.HTTP_201_CREATED)
async def refresh(request: Request, response: Response):

    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    record = verify_refresh_token_db(refresh_token)
    if not record:
        raise HTTPException(status_code=401, detail="invalid refresh token")

    revoke_refresh_token_db(record["id"])

    new_refresh = create_refresh_token()
    token_hash = hash_token(new_refresh)

    token_data = RefreshToken(
        **{
            "user_id": record["user_id"],
            "token_hash": token_hash,
            "expires_at": refresh_expire_time(),
        }
    ).model_dump(mode="json")
    store_refresh_token_db(token_data)

    new_access = create_access_token(record["user_id"])

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth/refresh",
    )

    return {"token": new_access}


@router.post("/get/API-key", status_code=status.HTTP_201_CREATED)
async def get_api_key(domain: str = Body(..., embed=True)):
    new_api_key = generate_api_key(domain)
    hashed_key = hash_api_key(new_api_key)

    key_domain = get_domain(domain)

    if not key_domain:
        raise HTTPException(status_code=404, detail="domain not found")

    key_data = ApiKey(
        **{
            "domain_id": key_domain.id,
            "domain": domain,
            "key_hash": hashed_key,
        }
    ).model_dump()

    store_new_key = (db().table("api_keys").insert(key_data).execute()).data[0]

    if not store_new_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="API key already exists"
        )

    return {"API-KEY": new_api_key}
