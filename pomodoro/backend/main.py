import os
import sys
from datetime import datetime, timedelta, timezone

BEIJING = timezone(timedelta(hours=8))

def now_beijing() -> datetime:
    return datetime.now(BEIJING)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import engine, Base, get_db
from .models import PomodoroSession, Settings
from .schemas import SessionCreate, SessionResponse, SettingsUpdate, StatsResponse, WeekData, MonthlyData, YearlyStatsResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_SETTINGS = {
    "work_duration": "25",
    "short_break": "5",
    "long_break": "15",
    "cycles_before_long": "4",
}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/sessions", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    db_session = PomodoroSession(
        type=session.type,
        duration=session.duration,
        completed_at=now_beijing(),
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@app.get("/api/sessions", response_model=list[SessionResponse])
def get_sessions(limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(PomodoroSession)
        .order_by(PomodoroSession.completed_at.desc())
        .limit(limit)
        .all()
    )


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    now = now_beijing()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Today
    today_sessions = (
        db.query(PomodoroSession)
        .filter(
            PomodoroSession.type == "work",
            PomodoroSession.completed_at >= today_start,
        )
        .all()
    )
    today_focus = sum(s.duration for s in today_sessions)
    today_count = len(today_sessions)

    # All time
    all_work = (
        db.query(PomodoroSession).filter(PomodoroSession.type == "work").all()
    )
    total_focus = sum(s.duration for s in all_work)
    total_count = len(all_work)

    # Week data
    week_data = []
    for i in range(7):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)
        day_sessions = (
            db.query(PomodoroSession)
            .filter(
                PomodoroSession.type == "work",
                PomodoroSession.completed_at >= day,
                PomodoroSession.completed_at < day_end,
            )
            .all()
        )
        week_data.append(
            WeekData(
                date=day.strftime("%Y-%m-%d"),
                weekday=_weekday_cn(day),
                seconds=sum(s.duration for s in day_sessions),
            )
        )
    week_data.reverse()

    # Streak: consecutive days with at least one work session
    streak = 0
    check_date = today_start
    for _ in range(365):
        day_end = check_date + timedelta(days=1)
        count = (
            db.query(PomodoroSession)
            .filter(
                PomodoroSession.type == "work",
                PomodoroSession.completed_at >= check_date,
                PomodoroSession.completed_at < day_end,
            )
            .count()
        )
        if count > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return StatsResponse(
        today_focus_seconds=today_focus,
        today_sessions=today_count,
        week_data=week_data,
        total_focus_seconds=total_focus,
        total_sessions=total_count,
        current_streak=streak,
    )


@app.get("/api/stats/yearly", response_model=YearlyStatsResponse)
def get_yearly_stats(year: int, db: Session = Depends(get_db)):
    month_col = func.strftime('%m', PomodoroSession.completed_at)
    rows = (
        db.query(
            month_col.label('month'),
            func.coalesce(func.sum(PomodoroSession.duration), 0).label('seconds'),
            func.count(PomodoroSession.id).label('count'),
        )
        .filter(
            PomodoroSession.type == 'work',
            func.strftime('%Y', PomodoroSession.completed_at) == str(year),
        )
        .group_by(month_col)
        .order_by(month_col)
        .all()
    )

    month_map = {int(r.month): {'seconds': r.seconds, 'count': r.count} for r in rows}
    monthly_data = [
        MonthlyData(
            month=m,
            seconds=month_map[m]['seconds'] if m in month_map else 0,
            count=month_map[m]['count'] if m in month_map else 0,
        )
        for m in range(1, 13)
    ]
    return YearlyStatsResponse(year=year, monthly_data=monthly_data)


@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    result = {}
    for key, default in DEFAULT_SETTINGS.items():
        setting = db.query(Settings).filter(Settings.key == key).first()
        result[key] = int(setting.value) if setting else int(default)
    return result


@app.put("/api/settings")
def update_settings(settings: SettingsUpdate, db: Session = Depends(get_db)):
    for key, value in settings.dict(exclude_none=True).items():
        setting = db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            db.add(Settings(key=key, value=str(value)))
    db.commit()
    return get_settings(db)


@app.delete("/api/sessions")
def clear_sessions(db: Session = Depends(get_db)):
    db.query(PomodoroSession).delete()
    db.commit()
    return {"status": "ok"}


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(PomodoroSession).filter(PomodoroSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
    return {"status": "ok"}


def _weekday_cn(d: datetime) -> str:
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return names[d.weekday()]


# Serve frontend in production
if getattr(sys, 'frozen', False):
    frontend_dir = os.path.join(sys._MEIPASS, 'frontend', 'dist')
else:
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
