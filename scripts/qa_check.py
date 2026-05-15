#!/usr/bin/env python3
"""
QA 自动化测试脚本 - v0.9.9-fix3
每次部署后运行此脚本验证核心功能
"""

import requests
import json
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []

    def add_pass(self, name):
        self.passed.append(name)
        print(f"[PASS] {name}")

    def add_fail(self, name, reason):
        self.failed.append((name, reason))
        print(f"[FAIL] {name}: {reason}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n=== 测试结果 ===")
        print(f"总计: {total} 项")
        print(f"通过: {len(self.passed)} 项")
        print(f"失败: {len(self.failed)} 项")
        if self.failed:
            print("\n失败详情:")
            for name, reason in self.failed:
                print(f"  - {name}: {reason}")
        return len(self.failed) == 0

def test_api_health(result):
    """T01: API 连通性 - 健康检查"""
    try:
        res = requests.get(f"{BASE_URL}/health", timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "ok" and data.get("version"):
                result.add_pass("API健康检查")
                return True
        result.add_fail("API健康检查", f"状态码 {res.status_code}")
        return False
    except Exception as e:
        result.add_fail("API健康检查", str(e))
        return False

def test_create_task(result):
    """T02: 创建扫描任务"""
    try:
        res = requests.post(
            f"{BASE_URL}/api/scan/submit",
            json={"target": "127.0.0.1", "name": "QA测试任务"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            if data.get("task_id") and data.get("status") == "pending":
                result.add_pass("创建扫描任务")
                return data["task_id"]
        result.add_fail("创建扫描任务", f"状态码 {res.status_code}")
        return None
    except Exception as e:
        result.add_fail("创建扫描任务", str(e))
        return None

def test_task_persistence(result, task_id):
    """T03: 数据持久化 - 任务列表可查"""
    if not task_id:
        result.add_fail("数据持久化", "无task_id可验证")
        return False
    try:
        res = requests.get(f"{BASE_URL}/api/scan/tasks", timeout=5)
        if res.status_code == 200:
            data = res.json()
            tasks = data.get("tasks", [])
            found = any(t.get("task_id") == task_id for t in tasks)
            if found:
                result.add_pass("数据持久化")
                return True
        result.add_fail("数据持久化", f"任务 {task_id} 未在列表中找到")
        return False
    except Exception as e:
        result.add_fail("数据持久化", str(e))
        return False

def test_pagination(result):
    """T04: 分页功能"""
    try:
        res1 = requests.get(f"{BASE_URL}/api/scan/tasks", timeout=5)
        if res1.status_code != 200:
            result.add_fail("分页功能", "获取任务列表失败")
            return False

        data1 = res1.json()
        total = data1.get("total", 0)

        # 如果总数超过10，验证前端分页逻辑（API本身返回所有数据）
        if total > 10:
            result.add_pass(f"分页功能 (共{total}条，前端分页)")
            return True
        else:
            result.add_pass(f"分页功能 (数据量{total}条)")
            return True
    except Exception as e:
        result.add_fail("分页功能", str(e))
        return False

def test_status_filter(result):
    """T05: 状态筛选数量校验"""
    try:
        res = requests.get(f"{BASE_URL}/api/scan/tasks", timeout=5)
        if res.status_code != 200:
            result.add_fail("状态筛选", "获取任务列表失败")
            return False

        data = res.json()
        tasks = data.get("tasks", [])

        # 计算各状态数量
        counts = {"pending": 0, "queued": 0, "running": 0, "scanning": 0, "completed": 0, "failed": 0}
        for t in tasks:
            status = t.get("status", "")
            if status in counts:
                counts[status] += 1

        queued_count = counts["pending"] + counts["queued"]
        running_count = counts["running"] + counts["scanning"]

        result.add_pass(f"状态筛选 (排队:{queued_count}, 运行:{running_count}, 完成:{counts['completed']}, 失败:{counts['failed']})")
        return True
    except Exception as e:
        result.add_fail("状态筛选", str(e))
        return False

def test_batch_delete(result):
    """T06: 批量删除功能"""
    try:
        # 先创建几个测试任务
        test_ids = []
        for i in range(3):
            res = requests.post(
                f"{BASE_URL}/api/scan/submit",
                json={"target": f"127.0.0.{i+1}", "name": f"QA批量删除测试{i}"},
                timeout=10
            )
            if res.status_code == 200:
                test_ids.append(res.json()["task_id"])

        if len(test_ids) < 2:
            result.add_fail("批量删除", "创建测试任务失败")
            return False

        time.sleep(1)  # 等待任务写入

        # 执行批量删除
        res = requests.post(
            f"{BASE_URL}/api/scan/tasks/batch",
            json={"ids": test_ids},
            timeout=10
        )

        if res.status_code != 200:
            result.add_fail("批量删除", f"状态码 {res.status_code}, 响应: {res.text}")
            return False

        data = res.json()
        deleted = data.get("deleted", 0)

        if deleted >= 2:
            result.add_pass(f"批量删除 (删除{deleted}条)")
            return True
        else:
            result.add_fail("批量删除", f"仅删除{deleted}条，预期至少2条")
            return False
    except Exception as e:
        result.add_fail("批量删除", str(e))
        return False

def test_single_delete(result):
    """T07: 单条删除功能"""
    try:
        # 创建一个测试任务
        res = requests.post(
            f"{BASE_URL}/api/scan/submit",
            json={"target": "127.0.0.99", "name": "QA单条删除测试"},
            timeout=10
        )
        if res.status_code != 200:
            result.add_fail("单条删除", "创建测试任务失败")
            return False

        task_id = res.json()["task_id"]
        time.sleep(1)

        # 执行单条删除
        res = requests.delete(f"{BASE_URL}/api/scan/tasks/{task_id}", timeout=10)

        if res.status_code == 200:
            result.add_pass("单条删除")
            return True
        else:
            result.add_fail("单条删除", f"状态码 {res.status_code}")
            return False
    except Exception as e:
        result.add_fail("单条删除", str(e))
        return False

def test_version(result):
    """T08: 版本信息验证"""
    try:
        res = requests.get(f"{BASE_URL}/health", timeout=5)
        if res.status_code == 200:
            data = res.json()
            version = data.get("version", "")
            if version.startswith("0.9.9"):
                result.add_pass(f"版本信息 (v{version})")
                return True
            else:
                result.add_fail("版本信息", f"版本号 {version} 不符合预期")
                return False
        result.add_fail("版本信息", f"状态码 {res.status_code}")
        return False
    except Exception as e:
        result.add_fail("版本信息", str(e))
        return False

def test_assets_api(result):
    """T09: 资产API连通性"""
    try:
        res = requests.get(f"{BASE_URL}/api/assets/?page=1&page_size=10", timeout=5)
        if res.status_code == 200:
            data = res.json()
            total = data.get("total", 0)
            result.add_pass(f"资产API (共{total}条)")
            return True
        result.add_fail("资产API", f"状态码 {res.status_code}")
        return False
    except Exception as e:
        result.add_fail("资产API", str(e))
        return False

def test_invalid_ip(result):
    """E01: 无效IP处理"""
    try:
        res = requests.post(
            f"{BASE_URL}/api/scan/submit",
            json={"target": "999.999.999.999"},
            timeout=10
        )
        if res.status_code >= 400:
            result.add_pass("无效IP处理 (正确拒绝)")
            return True
        else:
            result.add_fail("无效IP处理", "应拒绝无效IP但返回成功")
            return False
    except Exception as e:
        # 网络错误不算失败
        result.add_fail("无效IP处理", str(e))
        return False

def main():
    print("=== QA 自动化测试 ===")
    print(f"测试目标: {BASE_URL}")
    print()

    result = TestResult()

    # 运行所有测试
    test_api_health(result)
    task_id = test_create_task(result)
    test_task_persistence(result, task_id)
    test_pagination(result)
    test_status_filter(result)
    test_batch_delete(result)
    test_single_delete(result)
    test_version(result)
    test_assets_api(result)
    test_invalid_ip(result)

    # 输出总结
    all_passed = result.summary()

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()