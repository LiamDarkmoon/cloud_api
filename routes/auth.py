from typing import Annotated
from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ..database import db
from ..models import User
from ..utils import verify_password, create_access_token, get_user, hash_password

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

    access_token = create_access_token(data={"email": created_user["email"]})

    return {"access_token": access_token, "token_type": "bearer"}


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
    access_token = create_access_token(data={"email": user.email})

    return {"access_token": access_token, "token_type": "bearer"}
