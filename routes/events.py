from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Query
from database import db
from models import Event, EventData, ApiKey
from utils import (
    get_domain,
    require_domain_session,
    require_user_session,
    verify_api_key,
)

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=List[EventData])
def get_events(
    user=Depends(require_user_session),
    user_id: int | None = None,
    domain_id: int | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    req_id = user_id or user.id
    event_query = db().table("events").select("*")

    if domain_id:
        domain = (
            db()
            .table("domains")
            .select("id, owner_id")
            .eq("id", domain_id)
            .single()
            .execute()
        ).data

        if not domain or domain["owner_id"] != user.id:
            raise HTTPException(403, "Not authorized")

        event_query = event_query.eq("domain_id", domain_id)

        if req_id == user_id:
            event_query = event_query.eq("user_id", req_id)

    else:
        if req_id != user.id:
            raise HTTPException(403, "Not authorized")

        event_query = event_query.eq("user_id", req_id)

    events = (
        event_query.order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
        .execute()
        .data
    )

    return events or []


@router.post("/track", status_code=status.HTTP_201_CREATED, response_model=EventData)
def track_event(event: Event, api_key: ApiKey = Depends(verify_api_key)):

    print(api_key)
    owner = get_domain(api_key["domain"]).owner_id
    new_event = event.model_dump()
    new_event.update(
        {
            "domain_id": api_key["domain_id"],
            "user_id": owner.owner_id,
        }
    )

    created_event = (db().table("events").insert(new_event).execute()).data[0]

    return created_event


@router.get(
    "/event/latest", status_code=status.HTTP_202_ACCEPTED, response_model=EventData
)
def get_last_event():

    responce = (
        db()
        .table("events")
        .select("*")
        .limit(1)
        .order("id", desc=True)
        .single()
        .execute()
    ).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="event not found"
        )
    else:
        event = responce

    return event


@router.get("/event/{id}", response_model=EventData)
def get_event(id: int, user=Depends(require_user_session)):

    responce = (
        db().table("events").select("*").eq("id", id).limit(1).single().execute()
    ).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="event not found"
        )
    else:
        event = responce

    return event


@router.delete("/event/latest", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(user=Depends(require_user_session)):

    id = (
        db().table("events").select("id").order("id", desc=True).limit(1).execute()
    ).data[0]["id"]

    if not id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="not events found"
        )
    else:
        responce = (db().table("events").delete().eq("id", id).execute()).data


@router.delete("/event/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(id: int, user=Depends(require_user_session)):

    responce = (db().table("events").delete().eq("id", id).execute()).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="event not found"
        )
