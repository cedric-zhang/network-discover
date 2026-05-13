import pytest
from fastapi.testclient import TestClient
from main import app
from app.models import ScanSubmitRequest, ScanOptions
import uuid
from datetime import datetime

client = TestClient(app)

def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.2.0"

def test_submit_valid_cidr():
    """测试提交合法CIDR网段"""
    payload = {
        "target": "192.168.1.0/24",
        "scan_options": {
            "port_scan": True,
            "os_detection": True,
            "vendor_detection": True
        },
        "schedule": "now"
    }
    response = client.post("/api/scan/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"
    assert data["target"] == "192.168.1.0/24"
    assert "message" in data

def test_submit_valid_single_ip():
    """测试提交合法单IP"""
    payload = {
        "target": "192.168.1.1",
        "scan_options": {
            "port_scan": True,
            "os_detection": True,
            "vendor_detection": True
        },
        "schedule": "now"
    }
    response = client.post("/api/scan/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"
    assert data["target"] == "192.168.1.1"
    assert "message" in data

def test_submit_invalid_ip():
    """测试提交非法IP"""
    payload = {
        "target": "999.999.999.999",
        "scan_options": {
            "port_scan": True,
            "os_detection": True,
            "vendor_detection": True
        },
        "schedule": "now"
    }
    response = client.post("/api/scan/submit", json=payload)
    assert response.status_code == 422

def test_submit_empty_target():
    """测试提交空字符串"""
    payload = {
        "target": "",
        "scan_options": {
            "port_scan": True,
            "os_detection": True,
            "vendor_detection": True
        },
        "schedule": "now"
    }
    response = client.post("/api/scan/submit", json=payload)
    assert response.status_code == 422

def test_submit_multiple_ips():
    """测试提交逗号分隔多IP"""
    payload = {
        "target": "192.168.1.1,192.168.1.2,192.168.1.3",
        "scan_options": {
            "port_scan": True,
            "os_detection": True,
            "vendor_detection": True
        },
        "schedule": "now"
    }
    response = client.post("/api/scan/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"
    assert data["target"] == "192.168.1.1,192.168.1.2,192.168.1.3"
    assert "message" in data

def test_get_scan_tasks():
    """测试获取扫描任务列表"""
    response = client.get("/api/scan/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
    assert "total" in data

def test_get_scan_task_by_id():
    """测试获取单个扫描任务详情"""
    # 先创建一个任务
    payload = {
        "target": "192.168.1.0/24",
        "scan_options": {
            "port_scan": True,
            "os_detection": True,
            "vendor_detection": True
        },
        "schedule": "now"
    }
    submit_response = client.post("/api/scan/submit", json=payload)
    assert submit_response.status_code == 200
    task_data = submit_response.json()
    task_id = task_data["task_id"]

    # 获取任务详情
    response = client.get(f"/api/scan/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["target"] == "192.168.1.0/24"

def test_get_scan_task_by_id_not_found():
    """测试获取不存在的任务"""
    fake_task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    response = client.get(f"/api/scan/tasks/{fake_task_id}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Task not found"