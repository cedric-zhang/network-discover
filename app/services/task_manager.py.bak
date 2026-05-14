from typing import Dict, Optional
from datetime import datetime
from app.models import ScanSubmitRequest, ScanResultResponse, HostInfo


class TaskManager:
    def __init__(self):
        # 任务存储（在内存中，用于v0.3.0版本）
        self.tasks: Dict[str, dict] = {}

    def create_task(self, scan_request: ScanSubmitRequest) -> str:
        """创建新扫描任务"""
        from uuid import uuid4
        import time

        task_id = f"task_{int(time.time())}_{uuid4().hex[:8]}"

        task = {
            "task_id": task_id,
            "status": "pending",
            "target": scan_request.target,
            "scan_options": scan_request.scan_options.dict(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message": "扫描任务已提交"
        }

        self.tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务详情"""
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str, **kwargs):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            for key, value in kwargs.items():
                self.tasks[task_id][key] = value

    def get_scan_result(self, task_id: str) -> Optional[ScanResultResponse]:
        """获取扫描结果（从scanner_service获取）"""
        from app.services.scanner import scanner_service

        if task_id in scanner_service.scan_results:
            result_data = scanner_service.scan_results[task_id]
            return ScanResultResponse(
                task_id=result_data["task_id"],
                status=result_data["status"],
                hosts=[HostInfo(**host_dict) for host_dict in result_data.get("hosts", [])]
            )

        # 如果任务存在但在结果中没有，则检查任务状态
        task = self.get_task(task_id)
        if task:
            return ScanResultResponse(
                task_id=task_id,
                status=task["status"],
                hosts=[]
            )

        return None

# 全局任务管理器实例
task_manager = TaskManager()