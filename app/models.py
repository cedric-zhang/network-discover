from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
import ipaddress
from enum import Enum


class ScheduleType(str, Enum):
    now = "now"
    daily = "每天"
    weekly = "每周"
    custom = "自定义"


class ScanOptions(BaseModel):
    port_scan: bool = True
    os_detection: bool = True
    vendor_detection: bool = True


class ScanSubmitRequest(BaseModel):
    target: str
    scan_options: ScanOptions = ScanOptions()
    schedule: ScheduleType = ScheduleType.now

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        """验证 IP 或 CIDR 格式"""
        v = v.strip()
        if not v:
            raise ValueError('目标不能为空')
        # 支持逗号分隔多 IP
        targets = [t.strip() for t in v.split(',')]
        for t in targets:
            try:
                if '/' in t:
                    ipaddress.ip_network(t, strict=False)
                else:
                    ipaddress.ip_address(t)
            except ValueError:
                raise ValueError(f'无效的 IP 地址或网段: {t}')
        return v


class ScanTaskResponse(BaseModel):
    task_id: str
    status: str
    target: str
    scan_options: Optional[ScanOptions] = None
    created_at: str
    updated_at: Optional[str] = None
    message: Optional[str] = None


class PortInfo(BaseModel):
    port: int
    protocol: str
    service: str
    product: str = ""


class HostInfo(BaseModel):
    ip: str
    status: str
    os: str = ""
    vendor: str = ""
    hostname: str = ""
    ports: List[PortInfo] = []


class ScanResultResponse(BaseModel):
    task_id: str
    status: str
    hosts: List[HostInfo] = []