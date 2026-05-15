from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from app.models import ScanSubmitRequest, ScanTaskResponse, ScanOptions, ScanResultResponse
from app.services.task_manager import task_manager
from app.services.scanner import scanner_service
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScanTask
from pydantic import BaseModel


router = APIRouter()


# 批量删除请求模型
class BatchDeleteRequest(BaseModel):
    ids: List[str]


@router.post("/scan/submit", response_model=ScanTaskResponse)
async def submit_scan(request: ScanSubmitRequest, background_tasks: BackgroundTasks):
    """Submit scan target"""
    task_id = task_manager.create_task(request)
    task_details = task_manager.get_task(task_id)
    scanner_service.active_scans[task_id] = task_details
    background_tasks.add_task(scanner_service.run_scan, task_id, request)
    task = task_manager.get_task(task_id)
    return ScanTaskResponse(
        task_id=task["task_id"],
        status=task["status"],
        target=task["target"],
        name=task.get("name"),
        scan_options=ScanOptions(**task["scan_options"]),
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        message=task["message"]
    )


@router.get("/scan/tasks")
async def get_scan_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选")
):
    """Get scan tasks list with pagination - read from database for persistence"""
    db: Session = SessionLocal()
    try:
        query = db.query(ScanTask).order_by(ScanTask.created_at.desc())
        
        # 状态筛选
        if status:
            status_map = {
                "queued": ["pending", "queued"],
                "running": ["running", "scanning"],
                "completed": ["completed"],
                "failed": ["failed"]
            }
            if status in status_map:
                query = query.filter(ScanTask.status.in_(status_map[status]))
            else:
                query = query.filter(ScanTask.status == status)
        
        total = query.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        # 边界处理
        if page > total_pages:
            return {
                "tasks": [],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        
        offset = (page - 1) * page_size
        db_tasks = query.offset(offset).limit(page_size).all()
        
        task_list = []
        for db_task in db_tasks:
            memory_task = scanner_service.active_scans.get(db_task.task_id)
            if memory_task:
                task_data = memory_task.copy()
                if not task_data.get("name") and db_task.name:
                    task_data["name"] = db_task.name
            else:
                task_data = {
                    "task_id": db_task.task_id,
                    "name": db_task.name or "",
                    "status": db_task.status,
                    "target": db_task.target,
                    "scan_options": {
                        "port_scan": True,
                        "os_detection": True,
                        "vendor_detection": True
                    },
                    "created_at": str(db_task.created_at),
                    "updated_at": str(db_task.updated_at),
                    "message": db_task.result_summary or ""
                }
            task_list.append(task_data)
        
        return {
            "tasks": task_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    except Exception as e:
        import logging
        logging.error(f"Error getting scan tasks: {str(e)}")
        return {"tasks": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0, "error": str(e)}
    finally:
        db.close()


@router.get("/scan/tasks/{task_id}", response_model=ScanTaskResponse)
async def get_scan_task(task_id: str):
    """Get single scan task details"""
    if task_id in scanner_service.active_scans:
        task = scanner_service.active_scans[task_id]
        return ScanTaskResponse(
            task_id=task["task_id"],
            status=task["status"],
            target=task["target"],
            name=task.get("name"),
            scan_options=ScanOptions(**task["scan_options"]),
            created_at=task["created_at"],
            updated_at=task["updated_at"],
            message=task.get("message")
        )
    db: Session = SessionLocal()
    try:
        db_task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
        if db_task:
            return ScanTaskResponse(
                task_id=db_task.task_id,
                status=db_task.status,
                target=db_task.target,
                name=db_task.name,
                scan_options=ScanOptions(port_scan=True, os_detection=True, vendor_detection=True),
                created_at=str(db_task.created_at),
                updated_at=str(db_task.updated_at),
                message=db_task.result_summary or f"Task from DB with status: {db_task.status}"
            )
    except Exception as e:
        import logging
        logging.error(f"Error retrieving scan task from DB: {str(e)}")
    finally:
        db.close()
    raise HTTPException(status_code=404, detail="Task not found")


@router.delete("/scan/tasks/{task_id}")
async def delete_scan_task(task_id: str):
    """Delete a single scan task"""
    import logging

    deleted_from_memory = False
    deleted_from_db = False

    if task_id in scanner_service.active_scans:
        del scanner_service.active_scans[task_id]
        deleted_from_memory = True
    if task_id in scanner_service.scan_results:
        del scanner_service.scan_results[task_id]
    if task_id in task_manager.tasks:
        del task_manager.tasks[task_id]

    db: Session = SessionLocal()
    try:
        db_task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
        if db_task:
            db.delete(db_task)
            db.commit()
            deleted_from_db = True
        else:
            logging.warning(f"Task {task_id} not found in database")
    except Exception as e:
        logging.error(f"Error deleting scan task from DB: {str(e)}")
        db.rollback()
    finally:
        db.close()

    if not deleted_from_memory and not deleted_from_db:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted", "task_id": task_id}


@router.post("/scan/tasks/batch")
async def delete_scan_tasks_batch(request: BatchDeleteRequest):
    """Delete multiple scan tasks - uses POST method for body support"""
    import logging

    task_ids = request.ids
    deleted_count = 0
    not_found = []

    db: Session = SessionLocal()
    try:
        for task_id in task_ids:
            # Delete from memory
            if task_id in scanner_service.active_scans:
                del scanner_service.active_scans[task_id]
            if task_id in scanner_service.scan_results:
                del scanner_service.scan_results[task_id]
            if task_id in task_manager.tasks:
                del task_manager.tasks[task_id]

            # Delete from database
            db_task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
            if db_task:
                db.delete(db_task)
                deleted_count += 1
            else:
                not_found.append(task_id)
                logging.warning(f"Task {task_id} not found in database for batch delete")

        db.commit()
        logging.info(f"Batch delete completed: {deleted_count} tasks deleted, {len(not_found)} not found")
    except Exception as e:
        logging.error(f"Error batch deleting scan tasks: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")
    finally:
        db.close()

    return {
        "message": f"已删除 {deleted_count} 条任务",
        "deleted": deleted_count,
        "not_found": not_found
    }


@router.get("/scan/tasks/{task_id}/result", response_model=ScanResultResponse)
async def get_scan_result(task_id: str):
    """Get scan result"""
    result = task_manager.get_scan_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result