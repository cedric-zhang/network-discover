from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
from datetime import datetime
import uuid
from app.models import ScanSubmitRequest, ScanTaskResponse, ScanOptions, ScanResultResponse
from app.services.task_manager import task_manager
from app.services.scanner import scanner_service
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScanTask


router = APIRouter()


@router.post("/scan/submit", response_model=ScanTaskResponse)
async def submit_scan(request: ScanSubmitRequest, background_tasks: BackgroundTasks):
    """Submit scan target"""
    # Create task
    task_id = task_manager.create_task(request)

    # Store task info in scanner_service's active_scans for status updates
    task_details = task_manager.get_task(task_id)
    scanner_service.active_scans[task_id] = task_details

    # Add scan task to background task queue
    background_tasks.add_task(scanner_service.run_scan, task_id, request)

    # Return task info
    task = task_manager.get_task(task_id)
    return ScanTaskResponse(
        task_id=task["task_id"],
        status=task["status"],
        target=task["target"],
        scan_options=ScanOptions(**task["scan_options"]),
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        message=task["message"]
    )


@router.get("/scan/tasks")
async def get_scan_tasks():
    """Get all scan tasks list"""
    from app.services.scanner import scanner_service
    task_list = list(scanner_service.active_scans.values())

    return {
        "tasks": task_list,
        "total": len(task_list)
    }


@router.get("/scan/tasks/{task_id}", response_model=ScanTaskResponse)
async def get_scan_task(task_id: str):
    """Get single scan task details"""
    from app.services.scanner import scanner_service

    # First check tasks in memory
    if task_id in scanner_service.active_scans:
        task = scanner_service.active_scans[task_id]
        return ScanTaskResponse(
            task_id=task["task_id"],
            status=task["status"],
            target=task["target"],
            scan_options=ScanOptions(**task["scan_options"]),
            created_at=task["created_at"],
            updated_at=task["updated_at"],
            message=task.get("message")
        )

    # If not in memory, look up in database
    db: Session = SessionLocal()
    try:
        db_task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
        if db_task:
            return ScanTaskResponse(
                task_id=db_task.task_id,
                status=db_task.status,
                target=db_task.target,
                scan_options=ScanOptions(port_scan=True, os_detection=True, vendor_detection=True),  # default values
                created_at=str(db_task.created_at),
                updated_at=str(db_task.updated_at),
                message=f"Task from DB with status: {db_task.status}"
            )
    except Exception as e:
        import logging
        logging.error(f"Error retrieving scan task from DB: {str(e)}")
    finally:
        db.close()

    # If not found anywhere, return 404
    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/scan/tasks/{task_id}/result", response_model=ScanResultResponse)
async def get_scan_result(task_id: str):
    """Get scan result"""
    result = task_manager.get_scan_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result
