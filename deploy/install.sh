#!/bin/bash
# Fiido AI 客服系统 - 服务器端部署脚本
# 在服务器上运行此脚本

set -e

echo "=========================================="
echo "  Fiido AI 客服系统 - 部署脚本"
echo "=========================================="

INSTALL_DIR="/opt/fiido-ai-service"
SERVICE_NAME="fiido-ai-backend"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 安装系统依赖
log_info "安装系统依赖..."
apt-get update
apt-get install -y python3-pip python3-venv redis-server

# 2. 启动 Redis
log_info "配置 Redis..."
cat > /etc/redis/redis.conf.d/fiido.conf << 'EOF'
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF

systemctl enable redis-server
systemctl restart redis-server

# 3. 创建安装目录
log_info "创建安装目录: $INSTALL_DIR"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# 4. 创建 Python 虚拟环境
log_info "创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 5. 安装 Python 依赖
log_info "安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. 安装 systemd 服务
log_info "配置 systemd 服务..."
cp deploy/systemd/fiido-ai-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# 7. 更新 nginx 配置
log_info "更新 nginx 配置..."

# 备份现有配置
cp /etc/nginx/sites-available/fiido /etc/nginx/sites-available/fiido.bak

# 读取现有配置并添加 AI 服务的 location
cat > /etc/nginx/sites-available/fiido << 'EOF'
server {
    listen 80;
    server_name _;

    # 现有应用 - 代理到 5000 端口
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }

    # AI 客服 API - 代理到 8000 端口
    location /ai/ {
        rewrite ^/ai/(.*) /$1 break;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;

        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;

        # CORS
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header Access-Control-Allow-Headers 'Authorization, Content-Type, X-Requested-With' always;

        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
EOF

# 测试 nginx 配置
nginx -t

# 8. 重启服务
log_info "启动服务..."
systemctl restart nginx
systemctl start $SERVICE_NAME

# 9. 验证
log_info "验证部署..."
sleep 3

if systemctl is-active --quiet $SERVICE_NAME; then
    log_info "✅ $SERVICE_NAME 服务运行正常"
else
    log_error "❌ $SERVICE_NAME 服务启动失败"
    journalctl -u $SERVICE_NAME -n 20
    exit 1
fi

if systemctl is-active --quiet nginx; then
    log_info "✅ nginx 服务运行正常"
else
    log_error "❌ nginx 服务启动失败"
    exit 1
fi

# 测试 API
if curl -s http://127.0.0.1:8000/api/health | grep -q '"coze_connected":true'; then
    log_info "✅ API 健康检查通过"
else
    log_warn "⚠️ API 健康检查未通过，请检查 .env 配置"
fi

echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - API: http://223.4.251.97/ai/api/health"
echo "  - Shopify: http://223.4.251.97/ai/api/shopify/health"
echo ""
echo "管理命令："
echo "  - 查看日志: journalctl -u $SERVICE_NAME -f"
echo "  - 重启服务: systemctl restart $SERVICE_NAME"
echo "  - 停止服务: systemctl stop $SERVICE_NAME"
echo ""
