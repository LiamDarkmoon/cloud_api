from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Query
from database import db
from models import Event, EventData
from utils import get_current_session, require_domain_session, require_user_session

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=List[EventData])
def get_events(
    user=Depends(require_user_session),
    user_id: int | None = None,
    domain_id: int | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    print(user)

    if user_id is not None:
        events = (
            db()
            .table("events")
            .select("*")
            .eq("user_id", user_id)
            .limit(limit)
            .offset(offset)
            .execute()
        ).data
    elif domain_id is not None:
        domain_events = (
            db()
            .table("events")
            .select("*")
            .eq("domain_id", domain_id)
            .limit(limit)
            .offset(offset)
            .execute()
        ).data
        events = domain_events
    else user.id:
        events = (
            db()
            .table("events")
            .select("*")
            .eq("user_id", user.id)
            .limit(limit)
            .offset(offset)
            .execute()
        ).data

    return events or []


@router.post("/track", status_code=status.HTTP_201_CREATED, response_model=EventData)
def track_event(event: Event, session=Depends(require_domain_session)):

    if session["session_type"] == "domain":
        new_event = event.model_dump()
        new_event.update(
            {
                "domain_id": session["data"].id,
                "user_id": session["data"].owner_id,
            }
        )
    else:
        owned_domain = (
            db()
            .table("domains")
            .select("*")
            .eq("owner_id", session["data"].id)
            .execute()
        ).data[0]
        new_event = event.model_dump()
        new_event.update(
            {
                "domain_id": owned_domain.id,
                "user_id": session["data"].id,
            }
        )

    created_event = (db().table("events").insert(new_event).execute()).data[0]

    return EventData(**created_event)


@router.get("/event/latest", status_code=status.HTTP_202_ACCEPTED)
def get_last_event():

    responce = (
        db().table("events").select("*").order("id", desc=True).limit(1).execute()
    ).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="event not found"
        )
    else:
        event = responce[0]

    return event


@router.get("/event/{id}", response_model=EventData)
def get_event(id: int, user=Depends(require_user_session)):

    responce = (db().table("events").select("*").eq("id", id).execute()).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="event not found"
        )
    else:
        event = responce[0]

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
