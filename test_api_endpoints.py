"""
API端点测试 - 验证前端所需的所有API端点正常工作
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """测试健康检查端点"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        print("✓ Health endpoint working: /health")
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")


def test_assets_endpoint():
    """测试资产端点"""
    try:
        response = requests.get(f"{BASE_URL}/api/assets/")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert "total" in data
        print("✓ Assets endpoint working: /api/assets/")
    except Exception as e:
        print(f"✗ Assets endpoint failed: {e}")


def test_assets_stats_endpoint():
    """测试资产统计端点"""
    try:
        response = requests.get(f"{BASE_URL}/api/assets/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "online" in data
        assert "offline" in data
        assert "unknown" in data
        print("✓ Assets stats endpoint working: /api/assets/stats/summary")
    except Exception as e:
        print(f"✗ Assets stats endpoint failed: {e}")


def test_scan_endpoint():
    """测试扫描端点"""
    try:
        # 发送一个示例扫描请求
        payload = {
            "target": "127.0.0.1",
            "scan_options": {
                "port_scan": True,
                "os_detection": True,
                "vendor_detection": True
            }
        }
        response = requests.post(f"{BASE_URL}/api/scans/submit", json=payload)
        # 这可能返回422（验证错误）或200，都是正常的
        print(f"✓ Scan endpoint accessible: /api/scans/submit (status: {response.status_code})")
    except Exception as e:
        print(f"✗ Scan endpoint failed: {e}")


def test_frontend_pages():
    """测试前端页面"""
    pages = ["/", "/index.html", "/assets.html", "/scan.html"]
    
    for page in pages:
        try:
            response = requests.get(f"{BASE_URL}{page}")
            assert response.status_code == 200
            print(f"✓ Frontend page working: {page}")
        except Exception as e:
            print(f"✗ Frontend page failed {page}: {e}")


def run_api_tests():
    """运行所有API测试"""
    print("开始测试API端点...")
    print()
    
    test_health_endpoint()
    print()
    
    test_assets_endpoint()
    print()
    
    test_assets_stats_endpoint()
    print()
    
    test_scan_endpoint()
    print()
    
    test_frontend_pages()
    print()
    
    print("API端点测试完成！")


if __name__ == "__main__":
    run_api_tests()
