from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from database import db
from models import DomainData, Session
from utils import (
    build_session,
    get_domain,
    require_user_session,
    sort_events_by_session,
    sort_events_by_time,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/sessions", response_model=List[Session])
def get_sessions(
    user=Depends(require_user_session),
    domain: DomainData = Depends(get_domain),
    start: datetime = Query(...),
    end: datetime = Query(...),
):

    existing = (
        db()
        .table("sessions")
        .select("*")
        .eq("domain_id", domain.id)
        .gte("start", start)
        .lte("end", end)
        .execute()
    ).data

    if existing:
        return existing

    events = (
        db()
        .table("events")
        .select("*")
        .eq("domain", domain.domain)
        .gte("timestamp", start)
        .lte("timestamp", end)
        .execute()
    ).data

    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no session found in {domain.domain} between {start} and {end}",
        )

    sessions = sort_events_by_session(events)
    new_sessions = []
    for session_events in sessions.values():
        sorted_by_time = sort_events_by_time(session_events)
        new_sessions.append(build_session(sorted_by_time))

    recorded_sessions = db().table("sessions").insert(new_sessions).execute()

    return new_sessions


@router.get("/session{session_id}", response_model=List[Session])
def get_session(session_id: str, user=Depends(require_user_session)):

    session = (
        db().table("sessions").select("*").eq("session_id", session_id).execute()
    ).data

    if not session:
        raise HTTPException(404, "session not found")

    return session
