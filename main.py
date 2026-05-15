from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any

app = FastAPI(title="网络设备发现平台", version="0.9.5")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("index.html")

@app.get("/index.html", response_class=HTMLResponse)
async def index_html():
    return FileResponse("index.html")

@app.get("/scan.html", response_class=HTMLResponse)
async def scan():
    return FileResponse("scan.html")

@app.get("/assets.html", response_class=HTMLResponse)
async def assets():
    return FileResponse("assets.html")

@app.get("/tasks.html", response_class=HTMLResponse)
async def tasks():
    return FileResponse("tasks.html")

@app.get("/asset/{ip}", response_class=HTMLResponse)
async def asset_detail(ip: str):
    return FileResponse("asset_detail.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.9.5"}

# 注册 API 路由
from app.routers import scan
app.include_router(scan.router, prefix="/api", tags=["scan"])
from app.routers import assets as assets_router
from app.routers import schedules
app.include_router(assets_router.router, prefix="/api", tags=["assets"])
app.include_router(schedules.router, prefix="/api", tags=["schedules"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
