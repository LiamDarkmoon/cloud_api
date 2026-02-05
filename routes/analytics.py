from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from database import db
from models import DateRange, DomainData, Session, UserData
from utils import (
    build_session,
    get_domain,
    parse_db_datetime,
    require_user_session,
    sort_events_by_session,
    sort_events_by_time,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/session", response_model=List[Session])
def get_session(
    start: datetime, end: datetime, domain: DomainData = Depends(get_domain)
):

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

    existing = (
        db()
        .table("sessions")
        .select("id")
        .eq("domain_id", domain.domain_id)
        .gte("start", start)
        .lte("end", end)
        .execute()
    ).data

    if existing:
        raise HTTPException(409, "Sessions already recorded for this range")

    recorded_sessions = db().table("sessions").insert(new_sessions).execute()

    return new_sessions
