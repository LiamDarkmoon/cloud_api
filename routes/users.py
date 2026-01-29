from typing import List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from database import db
from models import UserData
from utils import require_user_session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserData])
def get_user(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):

    responce = (
        db().table("users").select("*").limit(limit).offset(offset).execute()
    ).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no users found"
        )
    else:
        users = responce

    return users


@router.get("/user/{id}", response_model=UserData)
def get_user(id: int, user=Depends(require_user_session)):

    responce = (db().table("users").select("*").eq("id", id).execute()).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    else:
        user = responce[0]

    return user
