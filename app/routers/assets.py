from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IPAsset
from pydantic import BaseModel


router = APIRouter()


class AssetResponse(BaseModel):
    ip: str
    status: str
    hostname: str
    os_name: str
    vendor: str
    mac_address: str
    open_ports: List[str]
    last_scan_at: Optional[str] = None
    created_at: Optional[str] = None


class AssetsResponse(BaseModel):
    assets: List[AssetResponse]
    total: int


@router.get("/assets/", response_model=AssetsResponse)
def get_assets(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="过滤状态: online, offline, unknown"),
    search: Optional[str] = Query(None, description="搜索IP或主机名"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取资产列表"""
    query = db.query(IPAsset)
    
    # 状态过滤
    if status:
        query = query.filter(IPAsset.status == status)
    
    # 搜索功能
    if search:
        query = query.filter(
            (IPAsset.ip.contains(search)) | 
            (IPAsset.hostname.contains(search))
        )
    
    # 分页
    offset = (page - 1) * page_size
    assets_db = query.offset(offset).limit(page_size).all()
    total = query.count()
    
    # 转换为响应模型
    assets = []
    for asset_db in assets_db:
        asset = AssetResponse(
            ip=asset_db.ip,
            status=asset_db.status,
            hostname=asset_db.hostname,
            os_name=asset_db.os_name,
            vendor=asset_db.vendor,
            mac_address=asset_db.mac_address,
            open_ports=asset_db.open_ports,
            last_scan_at=asset_db.last_scan_at.isoformat() if asset_db.last_scan_at else None,
            created_at=asset_db.created_at.isoformat() if asset_db.created_at else None
        )
        assets.append(asset)
    
    return AssetsResponse(assets=assets, total=total)


@router.get("/assets/{ip}", response_model=AssetResponse)
def get_asset(ip: str, db: Session = Depends(get_db)):
    """获取特定IP的资产信息"""
    asset = db.query(IPAsset).filter(IPAsset.ip == ip).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse(
        ip=asset.ip,
        status=asset.status,
        hostname=asset.hostname,
        os_name=asset.os_name,
        vendor=asset.vendor,
        mac_address=asset.mac_address,
        open_ports=asset.open_ports,
        last_scan_at=asset.last_scan_at.isoformat() if asset.last_scan_at else None,
        created_at=asset.created_at.isoformat() if asset.created_at else None
    )


@router.get("/assets/stats/summary")
def get_assets_stats(db: Session = Depends(get_db)):
    """获取资产统计摘要"""
    total = db.query(IPAsset).count()
    online = db.query(IPAsset).filter(IPAsset.status == 'online').count()
    offline = db.query(IPAsset).filter(IPAsset.status == 'offline').count()
    unknown = db.query(IPAsset).filter(IPAsset.status == 'unknown').count()
    
    return {
        "total": total,
        "online": online,
        "offline": offline,
        "unknown": unknown,
        "timestamp": datetime.utcnow().isoformat()
    }
