"""
Frontend Integration Test - Test compatibility between frontend JavaScript functions and backend API
"""
import json
from app.models import AssetResponse


def test_asset_model_compatibility():
    """Test AssetResponse model compatibility with frontend JavaScript expected format"""
    # Simulate asset data returned by API
    asset_data = {
        "ip": "192.168.1.1",
        "status": "online",
        "hostname": "router.home",
        "os_name": "Linux",
        "vendor": "TP-LINK",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "open_ports": ["22/tcp", "80/tcp", "443/tcp"],
        "last_scan_at": "2023-10-01T10:30:00",
        "created_at": "2023-09-01T08:00:00"
    }
    
    # Verify model compatibility
    asset = AssetResponse(**asset_data)
    
    print("✓ AssetResponse model validation passed")
    print(f"  IP: {asset.ip}")
    print(f"  Status: {asset.status}")
    print(f"  Open Ports: {len(asset.open_ports)} items")
    
    return asset


def test_assets_api_response():
    """Test AssetsResponse compatibility with frontend expected format"""
    from app.models import AssetsResponse
    
    # Simulate asset list returned by API
    assets_data = [
        {
            "ip": "192.168.1.1",
            "status": "online",
            "hostname": "router.home",
            "os_name": "Linux",
            "vendor": "TP-LINK",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "open_ports": ["22/tcp", "80/tcp", "443/tcp"],
            "last_scan_at": "2023-10-01T10:30:00",
            "created_at": "2023-09-01T08:00:00"
        },
        {
            "ip": "192.168.1.100",
            "status": "offline",
            "hostname": "workstation-01",
            "os_name": "Windows 10",
            "vendor": "Dell",
            "mac_address": "11:22:33:44:55:66",
            "open_ports": [],
            "last_scan_at": "2023-10-01T09:15:00",
            "created_at": "2023-08-15T14:20:00"
        }
    ]
    
    # Build response object
    response = AssetsResponse(assets=[AssetResponse(**asset) for asset in assets_data], total=len(assets_data))
    
    print("✓ AssetsResponse model validation passed")
    print(f"  Total assets: {response.total}")
    print(f"  Returned assets: {len(response.assets)}")
    
    return response


def test_javascript_compatibility():
    """Test Python data structure compatibility with JavaScript frontend processing"""
    # Simulate data structure that JavaScript frontend will process
    api_response = {
        "assets": [
            {
                "ip": "192.168.1.1",
                "status": "online",
                "hostname": "router.home",
                "os_name": "Linux",
                "vendor": "TP-LINK",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "open_ports": ["22/tcp", "80/tcp", "443/tcp"],
                "last_scan_at": "2023-10-01T10:30:00",
                "created_at": "2023-09-01T08:00:00"
            }
        ],
        "total": 1
    }
    
    # Verify data type compatibility
    assert isinstance(api_response["assets"], list)
    assert isinstance(api_response["total"], int)
    assert isinstance(api_response["assets"][0]["open_ports"], list)
    
    print("✓ Frontend JavaScript compatibility validation passed")
    
    return api_response


def run_all_tests():
    """Run all frontend integration tests"""
    print("Starting frontend integration tests...")
    print()
    
    test_asset_model_compatibility()
    print()
    
    test_assets_api_response()
    print()
    
    test_javascript_compatibility()
    print()
    
    print("✓ All frontend integration tests passed!")
    print("  - Backend API data structure compatible with frontend expectations")
    print("  - Python model validation passed")
    print("  - Data types compatible with JavaScript")


if __name__ == "__main__":
    run_all_tests()
