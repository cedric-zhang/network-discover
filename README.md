# Tognix Network Discovery Platform

A comprehensive network device discovery and asset management platform built with FastAPI.

## Features

- **Network Scanning**: Discover devices and scan ports using nmap
- **Asset Management**: Automatically record and manage network device information
- **Scheduled Tasks**: Periodic scanning with APScheduler support
- **Web Interface**: Intuitive dashboard with real-time data visualization
- **REST API**: Complete API endpoints for third-party integration

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, APScheduler
- **Frontend**: Vanilla JavaScript, HTML/CSS
- **Database**: SQLite
- **Scanner**: nmap
- **Deployment**: systemd + Nginx reverse proxy

## Quick Start

### Prerequisites

- RockyLinux 9.7 (or similar RHEL-based system)
- Python 3.9+
- nmap installed

### Installation

```bash
# Clone the repository
git clone https://github.com/cedric-zhang/network-discover.git
cd network-discover

# Install dependencies
pip install -r requirements.txt

# Initialize database (auto-created on first run)
# No manual initialization needed

# Start the service
systemctl start network-discovery
```

### Manual Start (for development)

```bash
cd /root/network-discovery
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
```

## Deployment

### systemd Service

Service file: `/etc/systemd/system/network-discovery.service`

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

### Service Management

```bash
systemctl daemon-reload
systemctl enable network-discovery
systemctl start network-discovery
systemctl status network-discovery
systemctl restart network-discovery
systemctl stop network-discovery

# View logs
journalctl -u network-discovery -f
```

### Nginx Configuration

Domain-based routing on port 800:

```nginx
# /etc/nginx/conf.d/default.conf
server {
    listen 800 default_server;
    server_name _;
    return 404;
}

# /etc/nginx/conf.d/network-discover.conf
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

## API Endpoints

- `GET /health` - Health check with version info
- `GET /api/assets/` - Asset list with pagination
- `GET /api/assets/stats` - Asset statistics summary
- `POST /api/scan/submit` - Submit scan task
- `GET /api/scan/tasks` - Get scan task list
- `PUT /api/scan/tasks/{task_id}/schedule` - Update task schedule
- `DELETE /api/scan/tasks/batch` - Batch delete tasks

## Version History

- **v0.10.1**: Infrastructure enhancement (systemd, Nginx domain routing, docs)
- **v0.10.0**: Milestone - fix1-fix12 complete, batch delete, pagination, schedule editing
- **v0.9.9**: Task center complete - CRUD + pagination + batch operations
- **v0.9.5**: Task center UI + custom confirm dialog
- **v0.9.4**: Scan feedback optimization + Toast component
- **v0.9.3**: Stability fixes
- **v0.9.2**: CSV export
- **v0.9.0**: Scheduled scanning + charts visualization
- **v0.8.0**: Asset detail page
- **v0.7.0**: Data persistence fix
- **v0.6.0**: Frontend integration + deployment script
- **v0.5.0**: APScheduler scheduled scanning
- **v0.4.0**: Scanner optimization
- **v0.3.0**: Asset management
- **v0.2.0**: Web interface
- **v0.1.0**: Basic scanning

## Repository

https://github.com/cedric-zhang/network-discover

## License

MIT License
