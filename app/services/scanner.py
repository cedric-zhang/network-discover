import threading
import subprocess
import asyncio
import time
import ipaddress
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
from app.config import scan_config


class ScannerService:
    # Global scan lock to prevent concurrent scans
    _scan_lock = threading.Lock()
    
    def __init__(self):
        self.active_scans: Dict[str, dict] = {}
        self.scan_results: Dict[str, dict] = {}

    def _count_target_ips(self, target: str) -> int:
        try:
            if "/" in target:
                net = ipaddress.IPv4Network(target, strict=False)
                return net.num_addresses
            else:
                ipaddress.IPv4Address(target)
                return 1
        except ValueError:
            return 1

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

        # Timing template from config
        timing = scan_config.timing_template
        cmd.extend([f"-{timing}"])
        # Stats reporting for progress tracking
        cmd.extend(["--stats-every", f"{scan_config.stats_every_seconds}s"])
        # XML output
        cmd.extend(["-oX", "-", target])

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

    def update_scan_progress_in_db(self, task_id: str, progress: int,
                                    current_ip: str = None,
                                    total_ips: int = None, elapsed: float = None):
        """Update scan progress fields in database."""
        db: Session = SessionLocal()
        try:
            scan_task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
            if scan_task:
                scan_task.progress = progress
                if current_ip:
                    scan_task.current_ip = current_ip
                if total_ips is not None:
                    scan_task.total_ips = total_ips
                if elapsed is not None:
                    scan_task.elapsed_seconds = elapsed
                scan_task.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logging.error(f"Error updating scan progress in DB: {str(e)}")
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

    async def _read_stdout_progress(self, proc, task_id: str,
                                     total_ips: int, start_time: float):
        """Read stdout line-by-line to track scan progress."""
        scanned_count = 0
        current_ip = None
        xml_output_parts = []
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace")
                xml_output_parts.append(decoded)
                if decoded.startswith("Nmap scan report for"):
                    scanned_count += 1
                    parts = decoded.split()
                    if len(parts) >= 5:
                        current_ip = parts[4]
                if "About" in decoded and "% done" in decoded:
                    try:
                        pct_str = decoded.split("About")[1].split("%")[0].strip()
                        pct = int(float(pct_str))
                        elapsed = time.time() - start_time
                        progress = max(pct, int(scanned_count / total_ips * 100) if total_ips > 0 else 0)
                        if task_id in self.active_scans:
                            self.active_scans[task_id]["progress"] = progress
                            self.active_scans[task_id]["current_ip"] = current_ip
                            self.active_scans[task_id]["total_ips"] = total_ips
                            self.active_scans[task_id]["elapsed_seconds"] = elapsed
                        self.update_scan_progress_in_db(task_id, progress, current_ip, total_ips, elapsed)
                    except (ValueError, IndexError):
                        pass
            return "".join(xml_output_parts), scanned_count
        except Exception as e:
            logging.error(f"Error reading stdout progress: {str(e)}")
            return "".join(xml_output_parts), scanned_count

    async def run_scan(self, task_id: str, scan_request: ScanSubmitRequest):
        """Run nmap scan in background with progress tracking."""
        start_time = time.time()
        total_ips = self._count_target_ips(scan_request.target)
        timeout = scan_config.timeout

        try:
            if task_id in self.active_scans:
                self.active_scans[task_id]["status"] = "scanning"
                self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                self.active_scans[task_id]["progress"] = 0
                self.active_scans[task_id]["total_ips"] = total_ips
                self.active_scans[task_id]["current_ip"] = None
                self.active_scans[task_id]["elapsed_seconds"] = 0.0

            self.update_scan_task_in_db(task_id, "scanning")
            self.update_scan_progress_in_db(task_id, 0, None, total_ips, 0.0)

            cmd = self.build_nmap_command(scan_request.target, scan_request.scan_options)
            logging.info(f"Executing nmap: {' '.join(cmd)} (timeout={timeout}s)")

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )

            xml_output, scanned_count = await asyncio.wait_for(
                self._read_stdout_progress(proc, task_id, total_ips, start_time),
                timeout=timeout
            )

            await proc.wait()
            elapsed = time.time() - start_time

            if proc.returncode == 0:
                if task_id in self.active_scans:
                    self.active_scans[task_id]["status"] = "completed"
                    self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                    self.active_scans[task_id]["progress"] = 100
                    self.active_scans[task_id]["elapsed_seconds"] = elapsed

                hosts = parse_nmap_xml(xml_output)
                self.update_scan_task_in_db(task_id, "completed",
                    f"Scan completed with {len(hosts)} hosts")
                self.update_scan_progress_in_db(task_id, 100, None, total_ips, elapsed)
                self.save_assets_to_db(hosts)
                self.scan_results[task_id] = {
                    "task_id": task_id, "status": "completed",
                    "hosts": [host.model_dump() for host in hosts],
                    "raw_output": xml_output
                }
            else:
                if task_id in self.active_scans:
                    self.active_scans[task_id]["status"] = "failed"
                    self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                    self.active_scans[task_id]["error"] = f"nmap exited with code {proc.returncode}"

                self.update_scan_task_in_db(task_id, "failed",
                    f"nmap exited with code {proc.returncode}")
                self.scan_results[task_id] = {
                    "task_id": task_id, "status": "failed",
                    "hosts": [], "error": f"nmap exited with code {proc.returncode}"
                }

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            if task_id in self.active_scans:
                self.active_scans[task_id]["status"] = "failed"
                self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                self.active_scans[task_id]["error"] = f"Scan timeout exceeded ({timeout // 60} minutes)"
                self.active_scans[task_id]["elapsed_seconds"] = elapsed

            self.update_scan_task_in_db(task_id, "failed",
                f"Scan timeout exceeded ({timeout // 60} minutes)")
            self.scan_results[task_id] = {
                "task_id": task_id, "status": "failed",
                "hosts": [], "error": f"Scan timeout exceeded ({timeout // 60} minutes)"
            }
            try:
                proc.terminate()
                await proc.wait()
            except (ProcessLookupError, NameError):
                pass

        except Exception as e:
            logging.error(f"Error during scan {task_id}: {str(e)}")
            if task_id in self.active_scans:
                self.active_scans[task_id]["status"] = "failed"
                self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                self.active_scans[task_id]["error"] = str(e)

            self.update_scan_task_in_db(task_id, "failed", f"Scan error: {str(e)}")
            self.scan_results[task_id] = {
                "task_id": task_id, "status": "failed",
                "hosts": [], "error": str(e)
            }



# Global scanner service instance
scanner_service = ScannerService()
