"""
pytest 单元测试 - 扫描任务 CRUD 和 API 功能
运行: pytest tests/ -v
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthAPI:
    """健康检查测试"""

    def test_health_check_returns_200(self):
        """测试健康检查返回200"""
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_check_version_format(self):
        """测试版本号格式"""
        res = client.get("/health")
        data = res.json()
        version = data["version"]
        # 版本号应为 0.9.9-fix* 格式
        assert version.startswith("0.9.9")


class TestScanTaskCreate:
    """扫描任务创建测试"""

    def test_create_single_ip_task(self):
        """测试创建单IP扫描任务"""
        res = client.post(
            "/api/scan/submit",
            json={
                "target": "192.168.1.1",
                "name": "pytest测试任务",
                "scan_options": {
                    "port_scan": True,
                    "os_detection": True,
                    "vendor_detection": True
                }
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["target"] == "192.168.1.1"
        assert data["name"] == "pytest测试任务"

    def test_create_cidr_task(self):
        """测试创建CIDR网段扫描任务"""
        res = client.post(
            "/api/scan/submit",
            json={"target": "192.168.1.0/24"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["target"] == "192.168.1.0/24"

    def test_create_task_without_name(self):
        """测试创建无名称任务"""
        res = client.post(
            "/api/scan/submit",
            json={"target": "10.0.0.1"}
        )
        assert res.status_code == 200
        data = res.json()
        # name 可以是空字符串
        assert data["name"] is None or data["name"] == ""

    def test_create_task_with_invalid_ip(self):
        """测试无效IP地址"""
        res = client.post(
            "/api/scan/submit",
            json={"target": "999.999.999.999"}
        )
        # 应返回400或422错误
        assert res.status_code >= 400

    def test_create_task_with_empty_target(self):
        """测试空目标"""
        res = client.post(
            "/api/scan/submit",
            json={"target": ""}
        )
        assert res.status_code >= 400


class TestScanTaskList:
    """扫描任务列表测试"""

    def test_get_task_list(self):
        """测试获取任务列表"""
        res = client.get("/api/scan/tasks")
        assert res.status_code == 200
        data = res.json()
        assert "tasks" in data
        assert "total" in data
        assert isinstance(data["tasks"], list)

    def test_task_list_has_correct_fields(self):
        """测试任务字段完整性"""
        res = client.get("/api/scan/tasks")
        data = res.json()
        if data["tasks"]:
            task = data["tasks"][0]
            required_fields = ["task_id", "status", "target", "created_at"]
            for field in required_fields:
                assert field in task

    def test_task_list_ordered_by_created_at(self):
        """测试任务按创建时间排序"""
        res = client.get("/api/scan/tasks")
        data = res.json()
        if len(data["tasks"]) >= 2:
            # 第一个任务应该是最新的
            first_time = data["tasks"][0]["created_at"]
            second_time = data["tasks"][1]["created_at"]
            assert first_time >= second_time


class TestScanTaskGet:
    """单个任务查询测试"""

    def test_get_existing_task(self):
        """测试获取存在的任务"""
        # 先创建一个任务
        create_res = client.post(
            "/api/scan/submit",
            json={"target": "172.16.0.1"}
        )
        task_id = create_res.json()["task_id"]

        # 查询该任务
        res = client.get(f"/api/scan/tasks/{task_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["task_id"] == task_id

    def test_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        res = client.get("/api/scan/tasks/nonexistent_task_id")
        assert res.status_code == 404


class TestScanTaskDelete:
    """任务删除测试"""

    def test_delete_single_task(self):
        """测试删除单个任务"""
        # 创建任务
        create_res = client.post(
            "/api/scan/submit",
            json={"target": "172.16.0.2"}
        )
        task_id = create_res.json()["task_id"]

        # 删除任务
        res = client.delete(f"/api/scan/tasks/{task_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "Task deleted"

        # 确认任务已删除
        get_res = client.get(f"/api/scan/tasks/{task_id}")
        assert get_res.status_code == 404

    def test_delete_nonexistent_task(self):
        """测试删除不存在的任务"""
        res = client.delete("/api/scan/tasks/nonexistent_task_id")
        assert res.status_code == 404


class TestScanTaskBatchDelete:
    """批量删除测试"""

    def test_batch_delete_tasks(self):
        """测试批量删除多个任务"""
        # 创建多个任务
        task_ids = []
        for i in range(3):
            res = client.post(
                "/api/scan/submit",
                json={"target": f"172.16.{i}.1"}
            )
            task_ids.append(res.json()["task_id"])

        # 执行批量删除
        res = client.post(
            "/api/scan/tasks/batch",
            json={"ids": task_ids}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["deleted"] >= 0

    def test_batch_delete_with_empty_list(self):
        """测试批量删除空列表"""
        res = client.post(
            "/api/scan/tasks/batch",
            json={"ids": []}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["deleted"] == 0


class TestAssetsAPI:
    """资产API测试"""

    def test_get_assets_list(self):
        """测试获取资产列表"""
        res = client.get("/api/assets/?page=1&page_size=10")
        assert res.status_code == 200
        data = res.json()
        assert "assets" in data
        assert "total" in data

    def test_get_assets_pagination(self):
        """测试资产分页"""
        res = client.get("/api/assets/?page=1&page_size=10")
        data = res.json()
        assets = data["assets"]
        # 返回的数量应不超过 page_size
        assert len(assets) <= 10


class TestStatusFlow:
    """状态流转测试"""

    def test_task_initial_status_is_pending(self):
        """测试任务初始状态为pending"""
        res = client.post(
            "/api/scan/submit",
            json={"target": "192.168.100.1"}
        )
        data = res.json()
        assert data["status"] == "pending"

    def test_task_status_values(self):
        """测试任务状态值合法"""
        res = client.get("/api/scan/tasks")
        data = res.json()
        valid_statuses = ["pending", "queued", "running", "scanning", "completed", "failed"]
        for task in data["tasks"]:
            assert task["status"] in valid_statuses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])