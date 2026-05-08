from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SessionCreate(BaseModel):
    type: str
    duration: int


class SessionResponse(BaseModel):
    id: int
    type: str
    duration: int
    completed_at: datetime

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    work_duration: Optional[int] = None
    short_break: Optional[int] = None
    long_break: Optional[int] = None
    cycles_before_long: Optional[int] = None


class WeekData(BaseModel):
    date: str
    weekday: str
    seconds: int


class MonthlyData(BaseModel):
    month: int
    seconds: int
    count: int


class YearlyStatsResponse(BaseModel):
    year: int
    monthly_data: list[MonthlyData]


class StatsResponse(BaseModel):
    today_focus_seconds: int
    today_sessions: int
    week_data: list[WeekData]
    total_focus_seconds: int
    total_sessions: int
    current_streak: int
