from typing import Annotated
from fastapi import APIRouter, Body, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import db
from models import Domain, User
from utils import verify_password, create_access_token, get_user, hash_password

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

    return {"user_token": user_token, "token_type": "user"}


@router.post("/login", status_code=status.HTTP_201_CREATED)
async def login(credentials: Annotated[OAuth2PasswordRequestForm, Depends()]):

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

    print(type(user.email))
    user_token = create_access_token(data={"email": user.email}, token_type="user")

    return {"user_token": user_token, "token_type": "user"}


@router.post("/domain", status_code=status.HTTP_201_CREATED)
async def auth_domain(domain: str = Body()):

    domain_query = await (
        db().table("domains").select("*").eq("domain", domain).execute()
    ).data

    if not domain_query:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="unauthorized domain"
        )
    else:
        domain_value = domain_query[0]["domain"]

    domain_token = create_access_token(
        data={"domain": domain_value}, token_type="domain"
    )

    return {"domain_token": domain_token, "token_type": "domain"}


@router.post("/domain/add", status_code=status.HTTP_201_CREATED)
async def add_domain(domain: str = Body()):

    domain_query = await (
        db().table("domains").select("*").eq("domain", domain).execute()
    ).data

    if not domain_query:
        new_domain = Domain(
            domain=domain,
            is_active=True,
        )

        added_domain = (
            db()
            .table("domains")
            .insert(new_domain.model_dump(exclude={"id"}))
            .execute()
        ).data[0]
        domain_value = added_domain["domain"]
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="already added domain"
        )
    domain_token = create_access_token(
        data={"domain": domain_value}, token_type="domain"
    )

    return {"domain_token": domain_token, "token_type": "domain"}
