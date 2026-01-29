from datetime import datetime
from typing import Literal, Optional
from pydantic.v1 import BaseConfig as BaseConfig  # type: ignore[assignment]
from pydantic import BaseModel, EmailStr


class Event(BaseModel):
    domain: str
    pathname: str
    referrer: str | None
    user_agent: str
    screen_width: int
    screen_height: int
    session_id: str
    event_type: str
    element: str
    time_spent: float
    user_id: Optional[int] = None
    domain_id: Optional[int] = None


class EventData(BaseModel):
    id: int
    domain: str
    pathname: str
    referrer: str | None
    user_agent: str
    screen_width: int
    screen_height: int
    session_id: str
    event_type: str
    element: str
    time_spent: float
    created_at: datetime
    user_id: int
    domain_id: int


class User(BaseModel):
    email: EmailStr
    password: str


class UserData(BaseModel):
    id: int
    email: EmailStr
    password: str


class Domain(BaseModel):
    domain: str
    is_active: bool = True
    owner_id: int | None = None


class DomainData(BaseModel):
    id: int
    domain: str
    is_active: bool = True
    owner_id: int | None = None
    created_at: datetime
    last_activity: datetime | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    type: Literal["user", "domain"]
    email: Optional[str] = None
    domain: Optional[str] = None
