#!/bin/bash

# 网络设备发现平台 - 部署脚本
# 适用于 RockyLinux 9.7

set -e  # 遇到错误立即退出

echo "======= 网络设备发现平台 v0.6.0 部署脚本 ======="

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo "错误: 必须使用root用户运行此脚本"
   exit 1
fi

# 检查必要命令
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "错误: 未找到命令 '$1'"
        return 1
    fi
}

echo "检查系统依赖..."
check_command "python3" || { echo "请先安装 Python 3.9+"; exit 1; }
check_command "pip3" || { echo "请先安装 pip3"; exit 1; }
check_command "nmap" || { echo "警告: 未找到 nmap，将尝试安装"; }
check_command "systemctl" || { echo "错误: 未找到 systemctl，这不是 systemd 系统"; exit 1; }

# 安装缺少的软件包
if ! command -v "nmap" &> /dev/null; then
    echo "正在安装 nmap..."
    dnf install -y nmap
fi

if ! command -v "nginx" &> /dev/null; then
    echo "正在安装 nginx..."
    dnf install -y nginx
fi

# 检查项目目录
PROJECT_DIR="/root/network-discovery"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "错误: 项目目录 $PROJECT_DIR 不存在"
    echo "请先将项目文件放置在 $PROJECT_DIR 目录下"
    exit 1
fi

echo "项目目录存在: $PROJECT_DIR"

# 安装 Python 依赖
echo "安装 Python 依赖..."
cd "$PROJECT_DIR"
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 创建系统服务文件
SERVICE_FILE="/etc/systemd/system/network-discovery.service"
echo "创建系统服务: $SERVICE_FILE"

cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Network Discovery Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/network-discovery
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "服务文件创建完成"

# 设置正确的权限
chmod 644 "$SERVICE_FILE"

# 重载 systemd 配置
echo "重载 systemd 配置..."
systemctl daemon-reload

# 启动并启用服务
echo "启动 network-discovery 服务..."
systemctl enable network-discovery
systemctl start network-discovery

# 检查服务状态
if systemctl is-active --quiet network-discovery; then
    echo "✅ network-discovery 服务启动成功"
else
    echo "❌ network-discovery 服务启动失败"
    systemctl status network-discovery --no-pager -l
    exit 1
fi

# 配置 Nginx 反向代理
NGINX_CONF="/etc/nginx/conf.d/network-discovery.conf"
echo "配置 Nginx 反向代理: $NGINX_CONF"

cat > "$NGINX_CONF" << 'EOF'
server {
    listen 80;
    server_name _;

    # 设置客户端请求体大小限制
    client_max_body_size 64M;

    # 设置代理头部
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 设置代理超时
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存配置
    location /static/ {
        alias /root/network-discovery/static/;
        expires 1h;
        add_header Cache-Control "public";
    }
}
EOF

echo "Nginx 配置完成"

# 检查 Nginx 配置语法
echo "检查 Nginx 配置语法..."
nginx -t

# 启动并启用 Nginx
echo "启动 Nginx 服务..."
systemctl enable nginx
systemctl start nginx

# 检查 Nginx 服务状态
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务启动成功"
else
    echo "❌ Nginx 服务启动失败"
    systemctl status nginx --no-pager -l
    exit 1
fi

# 检查端口监听
echo "检查服务监听状态..."
if ss -tuln | grep -q ':80 '; then
    echo "✅ Nginx 正在 80 端口监听"
else
    echo "❌ 80 端口未被监听"
fi

if ss -tuln | grep -q ':8000 '; then
    echo "✅ 应用程序正在 8000 端口监听"
else
    echo "⚠️  8000 端口未被监听 (这可能是正常的，因为应用可能只监听 127.0.0.1:8000)"
fi

echo ""
echo "======= 部署完成 ======="
echo "网络设备发现平台已成功部署!"
echo ""
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "服务管理命令:"
echo "  查看应用状态: systemctl status network-discovery"
echo "  重启应用: systemctl restart network-discovery"
echo "  查看应用日志: journalctl -u network-discovery -f"
echo ""
echo "Nginx 管理命令:"
echo "  查看 Nginx 状态: systemctl status nginx"
echo "  重启 Nginx: systemctl restart nginx"
echo "  查看 Nginx 日志: journalctl -u nginx -f"
echo ""
echo "项目位置: $PROJECT_DIR"
echo "服务配置: $SERVICE_FILE"
echo "Nginx 配置: $NGINX_CONF"