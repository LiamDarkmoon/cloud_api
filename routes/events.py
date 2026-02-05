import datetime
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


@router.post("/track", status_code=status.HTTP_201_CREATED)
def track_event(events: List[Event], api_key: ApiKey = Depends(verify_api_key)):

    if api_key["revoked"]:
        raise HTTPException(403, "revoked API key please renew")

    owner = get_domain(api_key["domain"])
    if not owner:
        raise HTTPException(404, "Domain not found")
    if not owner["is_active"]:
        raise HTTPException(403, "Domain is not active")

    if len(events) < 1:
        raise HTTPException(400, "no events found to track")
    if len(events) > 50:
        raise HTTPException(400, "events exeded")

    rows = []
    for event in events:
        new_event = event.model_dump()
        new_event.update(
            {
                "domain_id": api_key["domain_id"],
                "user_id": owner["owner_id"],
            }
        )
        rows.append(new_event)

    db().table("events").insert(rows).execute()

    return {"status": "ok", "inserted": len(events)}


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
