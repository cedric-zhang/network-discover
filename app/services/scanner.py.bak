import subprocess
import asyncio
from typing import Dict
import logging
from datetime import datetime
from app.models import ScanSubmitRequest, ScanOptions
import xml.etree.ElementTree as ET
from app.utils.nmap_parser import parse_nmap_xml
import os


class ScannerService:
    def __init__(self):
        self.active_scans: Dict[str, dict] = {}
        self.scan_results: Dict[str, dict] = {}

    def build_nmap_command(self, target: str, scan_options: ScanOptions = None) -> list:
        """
        构建nmap扫描命令
        """
        if scan_options is None:
            scan_options = ScanOptions()

        cmd = ["nmap", "-sS"]  # SYN扫描

        # 根据扫描选项添加参数
        if scan_options.port_scan:
            cmd.extend(["-sV"])  # 版本探测
        if scan_options.os_detection:
            cmd.extend(["-O"])   # 操作系统检测
        if scan_options.vendor_detection:
            cmd.extend(["-A"])   # 启用脚本扫描、OS检测和版本检测（包含了-O和-sV）

        # 添加快速扫描参数和XML输出
        cmd.extend(["-T4", "-oX", "-", target])

        return cmd

    async def run_scan(self, task_id: str, scan_request: ScanSubmitRequest):
        """
        在后台运行nmap扫描
        """
        try:
            # 更新任务状态为scanning
            if task_id in self.active_scans:
                self.active_scans[task_id]["status"] = "scanning"
                self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()

            # 构建命令
            cmd = self.build_nmap_command(scan_request.target, scan_request.scan_options)

            logging.info(f"Executing nmap command: {' '.join(cmd)}")

            # 异步执行命令，设置超时时间
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )

            try:
                # 等待命令执行，设置5分钟超时
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300.0)

                # 检查退出码
                if proc.returncode == 0:
                    # 解析XML输出
                    xml_output = stdout.decode('utf-8')

                    # 更新任务状态为completed
                    if task_id in self.active_scans:
                        self.active_scans[task_id]["status"] = "completed"
                        self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()

                    # 解析扫描结果
                    hosts = parse_nmap_xml(xml_output)

                    # 保存扫描结果
                    self.scan_results[task_id] = {
                        "task_id": task_id,
                        "status": "completed",
                        "hosts": [host.model_dump() for host in hosts],
                        "raw_output": xml_output
                    }

                else:
                    # 扫描失败
                    error_msg = stderr.decode('utf-8') if stderr else "Unknown error"

                    if task_id in self.active_scans:
                        self.active_scans[task_id]["status"] = "failed"
                        self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                        self.active_scans[task_id]["error"] = error_msg

                    # 保存失败结果
                    self.scan_results[task_id] = {
                        "task_id": task_id,
                        "status": "failed",
                        "hosts": [],
                        "error": error_msg
                    }

            except asyncio.TimeoutError:
                # 扫描超时
                if task_id in self.active_scans:
                    self.active_scans[task_id]["status"] = "failed"
                    self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                    self.active_scans[task_id]["error"] = "Scan timeout exceeded (5 minutes)"

                # 保存超时结果
                self.scan_results[task_id] = {
                    "task_id": task_id,
                    "status": "failed",
                    "hosts": [],
                    "error": "Scan timeout exceeded (5 minutes)"
                }

                # 尝试终止进程
                try:
                    proc.terminate()
                    await proc.wait()
                except ProcessLookupError:
                    pass  # 进程可能已经结束了
        except Exception as e:
            # 扫描异常
            logging.error(f"Error during scan {task_id}: {str(e)}")

            if task_id in self.active_scans:
                self.active_scans[task_id]["status"] = "failed"
                self.active_scans[task_id]["updated_at"] = datetime.now().isoformat()
                self.active_scans[task_id]["error"] = str(e)

            # 保存异常结果
            self.scan_results[task_id] = {
                "task_id": task_id,
                "status": "failed",
                "hosts": [],
                "error": str(e)
            }


# 全局扫描器实例
scanner_service = ScannerService()