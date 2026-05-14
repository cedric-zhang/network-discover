from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import IPAsset
from pydantic import BaseModel
import csv
import io
from fastapi.responses import StreamingResponse


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter()


class AssetResponse(BaseModel):
    ip: str
    status: str
    hostname: str
    os_name: str
    vendor: str
    mac_address: str
    open_ports: List[Dict]
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
    
    if status:
        query = query.filter(IPAsset.status == status)
    
    if search:
        query = query.filter(
            (IPAsset.ip.contains(search)) | 
            (IPAsset.hostname.contains(search))
        )
    
    offset = (page - 1) * page_size
    assets_db = query.offset(offset).limit(page_size).all()
    total = query.count()
    
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


# 注意：固定路径必须放在动态路径（/assets/{ip}）之前
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


@router.get("/assets/export")
def export_assets_csv(db: Session = Depends(get_db)):
    """导出资产数据为 CSV 文件"""
    assets = db.query(IPAsset).all()
    
    output = io.StringIO()
    # UTF-8 BOM for Excel compatibility
    output.write('\ufeff')
    
    writer = csv.writer(output)
    writer.writerow(['IP地址', '状态', '主机名', '操作系统', '厂商', 'MAC地址', '开放端口', '最后扫描时间', '创建时间'])
    
    for asset in assets:
        ports_str = ''
        if asset.open_ports:
            if isinstance(asset.open_ports, list):
                ports_str = ', '.join([
                    str(p.get('port', '')) + '/' + str(p.get('protocol', 'tcp'))
                    if isinstance(p, dict) else str(p)
                    for p in asset.open_ports
                ])
            else:
                ports_str = str(asset.open_ports)
        
        status_text = '未知'
        if asset.status == 'up' or asset.status == 'online':
            status_text = '在线'
        elif asset.status == 'down' or asset.status == 'offline':
            status_text = '离线'
        
        writer.writerow([
            asset.ip,
            status_text,
            asset.hostname or '',
            asset.os_name or '',
            asset.vendor or '',
            asset.mac_address or '',
            ports_str,
            asset.last_scan_at.isoformat() if asset.last_scan_at else '',
            asset.created_at.isoformat() if asset.created_at else ''
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="network_assets.csv"'}
    )


# 动态路径放在最后
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
