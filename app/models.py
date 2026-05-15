from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
import ipaddress
import re
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from app.database import Base


# Pydantic Models (for API)
class PortInfo(BaseModel):
    """端口信息模型"""
    port: int
    protocol: str
    service: str
    product: str
    version: str = ""


class HostInfo(BaseModel):
    """主机信息模型"""
    ip: str
    status: str
    os: str
    vendor: str
    hostname: str
    ports: List[PortInfo]


class ScanOptions(BaseModel):
    """扫描选项模型"""
    port_scan: bool = True
    os_detection: bool = True
    vendor_detection: bool = True


class ScanSubmitRequest(BaseModel):
    """扫描提交请求模型"""
    target: str
    name: Optional[str] = None  # 用户自定义任务名称
    scan_options: ScanOptions = ScanOptions()

    @field_validator("target")
    @classmethod
    def validate_target(cls, v):
        if not v:
            raise ValueError("Target cannot be empty")

        # 检查是否类似IP地址格式 (数字.数字.数字.数字 或 数字.数字.数字.数字/数字)
        # 如果是IP格式，必须通过ipaddress验证，不能当作域名
        ip_pattern = r'^\d{1,3}(\.\d{1,3}){3}(/\d{1,2})?$'
        if re.match(ip_pattern, v):
            try:
                # 必须是有效的IP地址或CIDR
                if '/' in v:
                    ipaddress.IPv4Network(v, strict=False)
                else:
                    ipaddress.IPv4Address(v)
                return v  # 有效IP/CIDR
            except ValueError as e:
                raise ValueError(f"Invalid IP address format: {v}. {str(e)}")

        # 不是IP格式，检查是否为有效域名
        hostname_pattern = r'^[a-zA-Z][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](\.[a-zA-Z][a-zA-Z0-9-]{0,61}[a-zA-Z0-9])*$'
        if re.match(hostname_pattern, v):
            return v  # 有效域名

        # 既不是有效IP也不是有效域名
        raise ValueError(f"Invalid target: {v}. Must be a valid IP, CIDR range, or hostname")


class ScanTaskResponse(BaseModel):
    """扫描任务响应模型"""
    task_id: str
    status: str
    target: str
    name: Optional[str] = None  # 任务名称
    scan_options: ScanOptions
    created_at: str
    updated_at: str
    message: Optional[str] = None


class ScanResultResponse(BaseModel):
    """扫描结果响应模型"""
    task_id: str
    status: str
    hosts: List[HostInfo]


# SQLAlchemy Models (for Database)
class IPAsset(Base):
    __tablename__ = "ip_assets" 

    ip = Column(String, primary_key=True)
    status = Column(String, default="unknown")  # online / offline / unknown
    hostname = Column(String, default="")
    os_name = Column(String, default="")
    vendor = Column(String, default="")
    mac_address = Column(String, default="")
    open_ports = Column(JSON, default=list)  # 存 JSON 列表
    last_scan_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Schedule(Base):
    __tablename__ = "schedules" 

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    target = Column(String, nullable=False)
    cron_expr = Column(String, nullable=False)  # 5-field cron: minute hour day month day_of_week
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanTask(Base):
    __tablename__ = "scan_tasks" 

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)  # 用户自定义任务名称
    target = Column(String)
    status = Column(String, default="pending")
    result_summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
