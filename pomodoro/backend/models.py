from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timedelta, timezone

from .database import Base

BEIJING = timezone(timedelta(hours=8))

def now_beijing():
    return datetime.now(BEIJING)


class PomodoroSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # "work", "short_break", "long_break"
    duration = Column(Integer, nullable=False)  # seconds
    completed_at = Column(DateTime, default=now_beijing)


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)
