from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional


class SessionCreate(BaseModel):
    type: Literal["work", "short_break", "long_break"]
    duration: int = Field(ge=1, le=14_400)


class SessionResponse(BaseModel):
    id: int
    type: str
    duration: int
    completed_at: datetime

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    work_duration: Optional[int] = Field(default=None, ge=1, le=120)
    short_break: Optional[int] = Field(default=None, ge=1, le=30)
    long_break: Optional[int] = Field(default=None, ge=1, le=60)
    cycles_before_long: Optional[int] = Field(default=None, ge=2, le=10)


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
