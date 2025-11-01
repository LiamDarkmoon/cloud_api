from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from database import db
from models import Event, EventData
from utils import get_current_session

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=List[EventData])
def get_events(user=Depends(get_current_session)):

    events = (db().table("events").select("*").execute()).data

    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no events found"
        )

    return events


@router.post("/track", status_code=status.HTTP_201_CREATED, response_model=EventData)
def track_event(event: Event, user=Depends(get_current_session)):

    event = (db().table("events").insert(event.model_dump()).execute()).data[0]

    return event


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
def get_event(id: int, user=Depends(get_current_session)):

    responce = (db().table("events").select("*").eq("id", id).execute()).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="event not found"
        )
    else:
        event = responce[0]

    return event


@router.delete("/event/latest", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(user=Depends(get_current_session)):

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
def delete_event(id: int, user=Depends(get_current_session)):

    responce = (db().table("events").delete().eq("id", id).execute()).data

    if not responce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="event not found"
        )
