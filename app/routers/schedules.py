from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Schedule
from pydantic import BaseModel
from datetime import datetime


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter()


class ScheduleCreateRequest(BaseModel):
    name: str
    target: str
    cron_expr: str


class ScheduleResponse(BaseModel):
    id: int
    name: str
    target: str
    cron_expr: str
    is_active: bool
    last_run_at: str = None
    created_at: str


@router.post(/schedules/, response_model=ScheduleResponse)
def create_schedule(schedule: ScheduleCreateRequest, db: Session = Depends(get_db)):
    创建新的定时扫描任务
    from app.models import Schedule
    
    db_schedule = Schedule(
        name=schedule.name,
        target=schedule.target,
        cron_expr=schedule.cron_expr,
        is_active=True
    )
    
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    return ScheduleResponse(
        id=db_schedule.id,
        name=db_schedule.name,
        target=db_schedule.target,
        cron_expr=db_schedule.cron_expr,
        is_active=db_schedule.is_active,
        last_run_at=db_schedule.last_run_at.isoformat() if db_schedule.last_run_at else None,
        created_at=db_schedule.created_at.isoformat()
    )


@router.get(/schedules/, response_model=List[ScheduleResponse])
def get_schedules(db: Session = Depends(get_db)):
    获取所有定时扫描任务
    schedules = db.query(Schedule).all()
    
    return [
        ScheduleResponse(
            id=sched.id,
            name=sched.name,
            target=sched.target,
            cron_expr=sched.cron_expr,
            is_active=sched.is_active,
            last_run_at=sched.last_run_at.isoformat() if sched.last_run_at else None,
            created_at=sched.created_at.isoformat()
        )
        for sched in schedules
    ]


@router.get(/schedules/{schedule_id}, response_model=ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    获取特定定时扫描任务
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail=Schedule not found)
    
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        target=schedule.target,
        cron_expr=schedule.cron_expr,
        is_active=schedule.is_active,
        last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        created_at=schedule.created_at.isoformat()
    )


@router.put(/schedules/{schedule_id}/toggle, response_model=ScheduleResponse)
def toggle_schedule(schedule_id: int, db: Session = Depends(get_db)):
    激活/暂停定时扫描任务
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail=Schedule not found)
    
    schedule.is_active = not schedule.is_active
    db.commit()
    db.refresh(schedule)
    
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        target=schedule.target,
        cron_expr=schedule.cron_expr,
        is_active=schedule.is_active,
        last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        created_at=schedule.created_at.isoformat()
    )


@router.delete(/schedules/{schedule_id})
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    删除定时扫描任务
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail=Schedule not found)
    
    db.delete(schedule)
    db.commit()
    
    return {message: Schedule deleted successfully}
