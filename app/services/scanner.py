import subprocess
import asyncio
from typing import Dict
import logging
from datetime import datetime
from app.models import ScanSubmitRequest, ScanOptions
import xml.etree.ElementTree as ET
from app.utils.nmap_parser import parse_nmap_xml
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScanTask, IPAsset


class ScannerService:
    def __init__(self):
        self.active_scans: Dict[str, dict] = {}
        self.scan_results: Dict[str, dict] = {}

    def build_nmap_command(self, target: str, scan_options: ScanOptions = None) -> list:
        """
        Build nmap scan command
        """
        if scan_options is None:
            scan_options = ScanOptions()

        cmd = ["nmap", "-sS"]  # SYN scan

        # Add parameters based on scan options
        if scan_options.port_scan:
            cmd.extend(["-sV"])  # version detection
        if scan_options.os_detection:
            cmd.extend(["-O"])   # OS detection
        if scan_options.vendor_detection:
            cmd.extend(["-A"])   # Enable script scan, OS detection and version detection (includes -O and -sV)

        # Add quick scan parameters and XML output
        cmd.extend(["-T4", "-oX", "-", target])

        return cmd

    def update_scan_task_in_db(self, task_id: str, status: str, result_summary: str = None):
        """
        Update scan task status in database
        """
        db: Session = SessionLocal()
        try:
            scan_task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
            if scan_task:
                scan_task.status = status
                if result_summary:
                    scan_task.result_summary = result_summary
                scan_task.updated_at = datetime.utcnow()
                db.commit()
            else:
                # If task doesn't exist, create a new task record
                new_task = ScanTask(
                    task_id=task_id,
                    target="",  # We don't have target here, but it should be set elsewhere
                    status=status,
                    result_summary=result_summary
                )
                db.add(new_task)
                db.commit()
        except Exception as e:
            logging.error(f"Error updating scan task in DB: {str(e)}")
        finally:
            db.close()


    def save_assets_to_db(self, hosts):
        """
        Save parsed hosts to the IP assets database with proper field mapping
        """
        logging.info(f"About to save {len(hosts)} hosts to database")
        db: Session = SessionLocal()
        try:
            for host in hosts:
                logging.info(f"Processing host: {host.ip} with {len(host.ports)} ports")
                # Store full port objects with service/product/version details
                port_list = [{
                    "port": port.port,
                    "protocol": port.protocol,
                    "service": port.service,
                    "product": port.product,
                    "version": port.version
                } for port in host.ports]
                existing_asset = db.query(IPAsset).filter(IPAsset.ip == host.ip).first()
                if existing_asset:
                    existing_asset.status = host.status
                    existing_asset.hostname = host.hostname
                    existing_asset.os_name = host.os
                    existing_asset.vendor = host.vendor
                    existing_asset.open_ports = port_list
                    existing_asset.last_scan_at = datetime.utcnow()
                    logging.info(f"Updated asset {host.ip} with ports: {port_list}")
                else:
                    new_asset = IPAsset(
                        ip=host.ip,
                        status=host.status,
                        hostname=host.hostname,
                        os_name=host.os,
                        vendor=host.vendor,
                        open_ports=port_list,
                        last_scan_at=datetime.utcnow()
                    )
                    db.add(new_asset)
                    logging.info(f"Created new asset {host.ip} with ports: {port_list}")
            db.commit()
            logging.info(f"Successfully committed {len(hosts)} hosts to database")
        except Exception as e:
            logging.error(f"Error saving assets to DB: {str(e)}")
        finally:
            db.close()

    async def run_scan(self, task_id: str, scan_request: ScanSubmitRequest):
        """
        Run nmap scan in background
        """
        try:
            # Update task status to scanning in memory
            if task_id in self.active_scans:
                self.active_scans[task_id]["status"] = "scanning"
                self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()

            # Update task status to scanning in database
            self.update_scan_task_in_db(task_id, "scanning")

            # Build command
            cmd = self.build_nmap_command(scan_request.target, scan_request.scan_options)

            logging.info(f"Executing nmap command: {' '.join(cmd)}")

            # Execute command asynchronously with timeout
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )

            try:
                # Wait for command execution with 5-minute timeout
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300.0)

                # Check exit code
                if proc.returncode == 0:
                    # Parse XML output
                    xml_output = stdout.decode('utf-8')

                    # Update task status to completed in memory
                    if task_id in self.active_scans:
                        self.active_scans[task_id]["status"] = "completed"
                        self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()

                    # Update task status to completed in database
                    self.update_scan_task_in_db(task_id, "completed", f"Scan completed successfully with {len(parse_nmap_xml(xml_output))} hosts found")

                    # Parse scan results
                    hosts = parse_nmap_xml(xml_output)

                    # Save parsed assets to database
                    logging.info(f"About to call save_assets_to_db for {len(hosts)} hosts")
                    self.save_assets_to_db(hosts)
                    logging.info(f"Finished save_assets_to_db")

                    # Save scan results
                    self.scan_results[task_id] = {
                        "task_id": task_id,
                        "status": "completed",
                        "hosts": [host.model_dump() for host in hosts],
                        "raw_output": xml_output
                    }

                else:
                    # Scan failed
                    error_msg = stderr.decode('utf-8') if stderr else "Unknown error"

                    # Update task status to failed in memory
                    if task_id in self.active_scans:
                        self.active_scans[task_id]["status"] = "failed"
                        self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                        self.active_scans[task_id]["error"] = error_msg

                    # Update task status to failed in database
                    self.update_scan_task_in_db(task_id, "failed", f"Scan failed: {error_msg}")

                    # Save failed results
                    self.scan_results[task_id] = {
                        "task_id": task_id,
                        "status": "failed",
                        "hosts": [],
                        "error": error_msg
                    }

            except asyncio.TimeoutError:
                # Scan timeout
                # Update task status to failed in memory
                if task_id in self.active_scans:
                    self.active_scans[task_id]["status"] = "failed"
                    self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                    self.active_scans[task_id]["error"] = "Scan timeout exceeded (5 minutes)"

                # Update task status to failed in database
                self.update_scan_task_in_db(task_id, "failed", "Scan timeout exceeded (5 minutes)")

                # Save timeout results
                self.scan_results[task_id] = {
                    "task_id": task_id,
                    "status": "failed",
                    "hosts": [],
                    "error": "Scan timeout exceeded (5 minutes)"
                }

                # Try to terminate process
                try:
                    proc.terminate()
                    await proc.wait()
                except ProcessLookupError:
                    pass  # Process might have already finished
        except Exception as e:
            # Scan exception
            logging.error(f"Error during scan {task_id}: {str(e)}")

            # Update task status to failed in memory
            if task_id in self.active_scans:
                self.active_scans[task_id]["status"] = "failed"
                self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                self.active_scans[task_id]["error"] = str(e)

            # Update task status to failed in database
            self.update_scan_task_in_db(task_id, "failed", f"Scan error: {str(e)}")

            # Save exception results
            self.scan_results[task_id] = {
                "task_id": task_id,
                "status": "failed",
                "hosts": [],
                "error": str(e)
            }


# Global scanner service instance
scanner_service = ScannerService()
