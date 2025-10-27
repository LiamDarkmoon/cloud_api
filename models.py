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


class EventData(BaseModel):
    id: int
    page: str
    element: str
    event_type: str
    time_spent: float


class User(BaseModel):
    email: EmailStr
    password: str


class UserData(BaseModel):
    id: int
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
