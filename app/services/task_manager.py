from typing import Dict, Optional
from datetime import datetime
from app.models import ScanSubmitRequest, ScanResultResponse, HostInfo, PortInfo
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScanTask, IPAsset


class TaskManager:
    def __init__(self):
        # Task storage (in memory, for active tasks only)
        self.tasks: Dict[str, dict] = {}

    def create_task(self, scan_request: ScanSubmitRequest) -> str:
        """Create new scan task"""
        from uuid import uuid4
        import time

        task_id = f"task_{int(time.time())}_{uuid4().hex[:8]}"
        task_name = scan_request.name or ""  # Get name from request

        task = {
            "task_id": task_id,
            "status": "pending",
            "target": scan_request.target,
            "name": task_name,
            "scan_options": scan_request.scan_options.dict(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message": "Scan task submitted"
        }

        self.tasks[task_id] = task

        # Create record in database (persistent storage)
        db: Session = SessionLocal()
        try:
            db_task = ScanTask(
                task_id=task_id,
                target=scan_request.target,
                name=task_name,
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
        """Get scan result - now fetches from database to handle multi-worker scenario"""
        from app.services.scanner import scanner_service

        # First try to get from memory (for backwards compatibility)
        if task_id in scanner_service.scan_results:
            result_data = scanner_service.scan_results[task_id]
            return ScanResultResponse(
                task_id=result_data["task_id"],
                status=result_data["status"],
                hosts=[HostInfo(**host_dict) for host_dict in result_data.get("hosts", [])]
            )

        # In multi-worker environments, memory might not be shared
        # So we need to reconstruct the result from the database (IPAsset table)
        db: Session = SessionLocal()
        try:
            # Check if the scan task exists and get its target
            db_task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
            if not db_task:
                return None

            # For this specific task, let's try to reconstruct the result from IPAsset table
            # Find assets that were scanned recently (based on task timestamp)
            import re
            from datetime import timedelta

            # Extract timestamp from task_id (format: task_1778728418_85ca40ec)
            try:
                ts_part = task_id.split('_')[1]  # Gets timestamp part
                task_time = datetime.utcfromtimestamp(int(ts_part))

                # Look for assets scanned around this time
                # We'll find assets based on the target IP from the scan task
                target_ip = db_task.target
                asset = db.query(IPAsset).filter(IPAsset.ip == target_ip).first()

                if asset:
                    # Create a single host from the asset data
                    host = HostInfo(
                        ip=asset.ip,
                        status=asset.status,
                        os=asset.os_name,
                        vendor=asset.vendor,
                        hostname=asset.hostname,
                        ports=[]
                    )

                    # Convert open_ports JSON list back to PortInfo objects
                    if asset.open_ports and isinstance(asset.open_ports, list):
                        for port_data in asset.open_ports:
                            if isinstance(port_data, dict):
                                port_info = PortInfo(
                                    port=port_data.get("port", 0),
                                    protocol=port_data.get("protocol", "tcp"),
                                    service=port_data.get("service", ""),
                                    product=port_data.get("product", ""),
                                    version=port_data.get("version", "")
                                )
                            elif isinstance(port_data, str) and '/' in port_data:
                                port_num, protocol = port_data.split('/', 1)
                                port_info = PortInfo(
                                    port=int(port_num),
                                    protocol=protocol,
                                    service="",
                                    product="",
                                    version=""
                                )
                            else:
                                continue
                            host.ports.append(port_info)

                    return ScanResultResponse(
                        task_id=task_id,
                        status=db_task.status,
                        hosts=[host]
                    )
            except Exception as e:
                import logging
                logging.error(f"Error reconstructing result from database: {str(e)}")
                pass

            # If not found in IPAsset, return basic task status
            return ScanResultResponse(
                task_id=task_id,
                status=db_task.status,
                hosts=[]
            )

        except Exception as e:
            import logging
            logging.error(f"Error retrieving scan result from DB: {str(e)}")
        finally:
            db.close()

        return None

# Global task manager instance
task_manager = TaskManager()