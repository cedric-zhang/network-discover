# Tognix 网络设备发现平台

基于 FastAPI 构建的网络设备发现和资产管理平台。

## 功能特性

- **网络扫描**: 使用 nmap 发现设备并扫描端口
- **资产管理**: 自动记录和管理网络设备信息
- **定时任务**: 支持 APScheduler 定期执行扫描任务
- **Web界面**: 直观的仪表盘，实时数据可视化
- **REST API**: 完整的 API 接口，支持第三方集成

## 技术栈

- **后端**: FastAPI, SQLAlchemy, APScheduler
- **前端**: Vanilla JavaScript, HTML/CSS
- **数据库**: SQLite
- **扫描器**: nmap
- **部署**: systemd + Nginx 反向代理

## 快速开始

### 环境要求

- RockyLinux 9.7（或类似的 RHEL 系统）
- Python 3.9+
- nmap 已安装

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/cedric-zhang/network-discover.git
cd network-discover

# 安装依赖
pip install -r requirements.txt

# 数据库自动创建，无需手动初始化

# 启动服务
systemctl start network-discovery
```

### 手动启动（开发模式）

```bash
cd /root/network-discovery
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
```

## 部署说明

### systemd 服务配置

服务文件路径: `/etc/systemd/system/network-discovery.service`

```ini
[Unit]
Description=Tognix Network Discovery Platform
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/network-discovery
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 服务管理命令

```bash
# 重载配置
systemctl daemon-reload

# 启用开机自启
systemctl enable network-discovery

# 启动服务
systemctl start network-discovery

# 查看状态
systemctl status network-discovery

# 重启服务
systemctl restart network-discovery

# 停止服务
systemctl stop network-discovery

# 查看日志
journalctl -u network-discovery -f
```

### Nginx 配置说明

域名路由配置，监听端口 800:

```nginx
# /etc/nginx/conf.d/default.conf — 默认 server，拒绝未匹配请求
server {
    listen 800 default_server;
    server_name _;
    return 404;
}

# /etc/nginx/conf.d/network-discover.conf — 项目专用配置
server {
    listen 800;
    server_name network-discover.irigud.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /root/network-discovery/static/;
        expires 30d;
    }
}
```

**访问方式**:
- 正确域名: `http://network-discover.irigud.com:800`
- 内网 DNS 已配置解析，无需修改 hosts
- 直接访问 `http://192.168.88.94:800/` 会返回 404（需带 Host header）

## API 接口

- `GET /health` - 健康检查，返回版本信息
- `GET /api/assets/` - 资产列表（支持分页）
- `GET /api/assets/stats` - 资产统计摘要
- `POST /api/scan/submit` - 提交扫描任务
- `GET /api/scan/tasks` - 获取扫描任务列表
- `PUT /api/scan/tasks/{task_id}/schedule` - 更新任务调度周期
- `DELETE /api/scan/tasks/batch` - 批量删除任务

## 版本历史

- **v0.10.1**: 基础设施增强（systemd、Nginx域名路由、文档）
- **v0.10.0**: 里程碑版本 - fix1-fix12闭环，批量删除、分页、周期编辑
- **v0.9.9**: 任务中心完整闭环 - CRUD + 分页 + 批量操作
- **v0.9.5**: 任务中心UI + 自定义确认弹窗
- **v0.9.4**: 扫描反馈优化 + Toast组件
- **v0.9.3**: 稳定性修复
- **v0.9.2**: CSV导出功能
- **v0.9.0**: 定时扫描 + 图表可视化
- **v0.8.0**: 资产详情页
- **v0.7.0**: 数据持久化修复
- **v0.6.0**: 前端数据接入 + 部署脚本
- **v0.5.0**: APScheduler定时扫描
- **v0.4.0**: 扫描引擎优化
- **v0.3.0**: 资产管理功能
- **v0.2.0**: Web界面
- **v0.1.0**: 基础扫描功能

## 代码仓库

https://github.com/cedric-zhang/network-discover

## 许可证

MIT License
