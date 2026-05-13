from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
from datetime import datetime
import uuid
from app.models import ScanSubmitRequest, ScanTaskResponse, ScanOptions, ScanResultResponse
from app.services.task_manager import task_manager
from app.services.scanner import scanner_service


router = APIRouter()


@router.post("/scan/submit", response_model=ScanTaskResponse)
async def submit_scan(request: ScanSubmitRequest, background_tasks: BackgroundTasks):
    """提交扫描目标"""
    # 创建任务
    task_id = task_manager.create_task(request)

    # 将任务信息存储到scanner_service的active_scans中，便于更新状态
    task_details = task_manager.get_task(task_id)
    scanner_service.active_scans[task_id] = task_details

    # 将扫描任务添加到后台任务队列
    background_tasks.add_task(scanner_service.run_scan, task_id, request)

    # 返回任务信息
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
    """获取所有扫描任务列表"""
    from app.services.scanner import scanner_service
    task_list = list(scanner_service.active_scans.values())

    return {
        "tasks": task_list,
        "total": len(task_list)
    }


@router.get("/scan/tasks/{task_id}", response_model=ScanTaskResponse)
async def get_scan_task(task_id: str):
    """获取单个扫描任务详情"""
    from app.services.scanner import scanner_service
    if task_id not in scanner_service.active_scans:
        raise HTTPException(status_code=404, detail="Task not found")

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


@router.get("/scan/tasks/{task_id}/result", response_model=ScanResultResponse)
async def get_scan_result(task_id: str):
    """获取扫描结果"""
    result = task_manager.get_scan_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result