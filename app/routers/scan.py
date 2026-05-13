from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime
import uuid
from app.models import ScanSubmitRequest, ScanTaskResponse, ScanOptions
import asyncio

router = APIRouter()

# 使用内存字典存储任务 - 模拟数据库
tasks_db: Dict[str, dict] = {}

@router.post("/scan/submit", response_model=ScanTaskResponse)
async def submit_scan(request: ScanSubmitRequest):
    """提交扫描目标"""
    # 生成任务ID
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    # 创建任务对象
    task = {
        "task_id": task_id,
        "status": "pending",  # 仅返回pending，不执行实际扫描
        "target": request.target,
        "scan_options": request.scan_options.dict(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "message": "扫描任务已提交"
    }

    # 存储到内存中
    tasks_db[task_id] = task

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
    """获取所有扫描任务列表"""
    task_list = list(tasks_db.values())

    return {
        "tasks": task_list,
        "total": len(task_list)
    }

@router.get("/scan/tasks/{task_id}", response_model=ScanTaskResponse)
async def get_scan_task(task_id: str):
    """获取单个扫描任务详情"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_db[task_id]
    return ScanTaskResponse(
        task_id=task["task_id"],
        status=task["status"],
        target=task["target"],
        scan_options=ScanOptions(**task["scan_options"]),
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        message=task.get("message")
    )