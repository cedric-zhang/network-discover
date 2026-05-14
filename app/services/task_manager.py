from typing import Dict, Optional
from datetime import datetime
from app.models import ScanSubmitRequest, ScanResultResponse, HostInfo
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScanTask


class TaskManager:
    def __init__(self):
        # Task storage (in memory, for v0.3.0)
        self.tasks: Dict[str, dict] = {}

    def create_task(self, scan_request: ScanSubmitRequest) -> str:
        """Create new scan task"""
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
            "message": "Scan task submitted"
        }

        self.tasks[task_id] = task

        # Also create record in database
        db: Session = SessionLocal()
        try:
            db_task = ScanTask(
                task_id=task_id,
                target=scan_request.target,
                status="pending"
            )
            db.add(db_task)
            db.commit()
        except Exception as e:
            import logging
            logging.error(f"Error creating scan task in DB: {str(e)}")
        finally:
            db.close()

        return task_id

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get task details"""
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str, **kwargs):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            for key, value in kwargs.items():
                self.tasks[task_id][key] = value

    def get_scan_result(self, task_id: str) -> Optional[ScanResultResponse]:
        """Get scan result (from scanner_service)"""
        from app.services.scanner import scanner_service

        if task_id in scanner_service.scan_results:
            result_data = scanner_service.scan_results[task_id]
            return ScanResultResponse(
                task_id=result_data["task_id"],
                status=result_data["status"],
                hosts=[HostInfo(**host_dict) for host_dict in result_data.get("hosts", [])]
            )

        # If task exists but not in results, check task status
        task = self.get_task(task_id)
        if task:
            return ScanResultResponse(
                task_id=task_id,
                status=task["status"],
                hosts=[]
            )

        # If not in memory, try to get from database
        db: Session = SessionLocal()
        try:
            db_task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
            if db_task:
                return ScanResultResponse(
                    task_id=task_id,
                    status=db_task.status,
                    hosts=[]
                )
        except Exception as e:
            import logging
            logging.error(f"Error retrieving scan task from DB: {str(e)}")
        finally:
            db.close()

        return None

# Global task manager instance
task_manager = TaskManager()
