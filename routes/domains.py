from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Query
from database import db
from models import Domain, UserData
from utils import require_user_session

router = APIRouter(prefix="/domains", tags=["Domains"])


@router.get("/", response_model=List[Domain])
def get_domains(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):

    responce = (
        db().table("domains").select("*").limit(limit).offset(offset).execute()
    ).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no domains found"
        )
    else:
        domains = responce

    return domains


@router.get("/domain/{id}", response_model=Domain)
def get_domain(id: int, user=Depends(require_user_session)):

    responce = (db().table("domains").select("*").eq("id", id).execute()).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="domain not found"
        )
    else:
        domain = responce[0]

    return domain
