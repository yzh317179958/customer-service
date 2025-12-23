# Fiido 智能服务平台 - Systemd 服务配置

> **最后更新**：2025-12-23
> **部署模式**：微服务架构（每个产品独立进程）

本目录包含 Fiido 平台各产品模块的 Systemd 服务配置文件。

---

## 部署模式

### 微服务模式（当前使用）

每个产品作为独立微服务运行，通过 nginx 反向代理统一入口：

```
┌─────────────────────────────────────────────────────────────────┐
│                        nginx (443/80)                            │
│                     ai.fiido.com SSL 终结                         │
├─────────────────────────────────────────────────────────────────┤
│  /chat-test  →  /var/www/fiido-frontend (AI客服前端)             │
│  /workbench  →  /var/www/fiido-workbench (坐席工作台前端)         │
│  /api/*      →  127.0.0.1:8000 (AI客服API)                       │
│  /workbench-api/* → 127.0.0.1:8002 (坐席工作台API)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 服务清单

| 服务 | 端口 | 服务文件 | 说明 |
|------|------|----------|------|
| fiido-ai-chatbot | 8000 | fiido-ai-chatbot.service | AI 智能客服 |
| fiido-agent-workbench | 8002 | fiido-agent-workbench.service | 坐席工作台 |

---

## 安装部署

### 1. 安装服务文件

```bash
# 复制服务文件到 systemd 目录
sudo cp deploy/systemd/fiido-ai-chatbot.service /etc/systemd/system/
sudo cp deploy/systemd/fiido-agent-workbench.service /etc/systemd/system/

# 重载 systemd 配置
sudo systemctl daemon-reload

# 设置开机自启
sudo systemctl enable fiido-ai-chatbot
sudo systemctl enable fiido-agent-workbench

# 启动服务
sudo systemctl start fiido-ai-chatbot
sudo systemctl start fiido-agent-workbench
```

### 2. 验证服务状态

```bash
# 查看所有 Fiido 服务状态
systemctl status fiido-ai-chatbot fiido-agent-workbench

# 健康检查
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8002/api/health
```

---

## 常用命令

```bash
# 查看服务状态
sudo systemctl status fiido-ai-chatbot
sudo systemctl status fiido-agent-workbench

# 查看实时日志
sudo journalctl -u fiido-ai-chatbot -f
sudo journalctl -u fiido-agent-workbench -f

# 重启服务
sudo systemctl restart fiido-ai-chatbot
sudo systemctl restart fiido-agent-workbench

# 停止服务
sudo systemctl stop fiido-ai-chatbot
sudo systemctl stop fiido-agent-workbench

# 查看最近 100 行日志
sudo journalctl -u fiido-ai-chatbot -n 100

# 查看今天的日志
sudo journalctl -u fiido-ai-chatbot --since today
```

---

## 服务配置说明

### fiido-ai-chatbot.service

```ini
[Unit]
Description=Fiido AI Chatbot Microservice
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fiido-ai-service
Environment="PATH=/opt/fiido-ai-service/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/fiido-ai-service"
EnvironmentFile=/opt/fiido-ai-service/.env
ExecStart=/opt/fiido-ai-service/venv/bin/uvicorn products.ai_chatbot.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
MemoryMax=8G

[Install]
WantedBy=multi-user.target
```

### fiido-agent-workbench.service

```ini
[Unit]
Description=Fiido Agent Workbench Microservice
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fiido-ai-service
Environment="PATH=/opt/fiido-ai-service/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/fiido-ai-service"
EnvironmentFile=/opt/fiido-ai-service/.env
ExecStart=/opt/fiido-ai-service/venv/bin/uvicorn products.agent_workbench.main:app --host 127.0.0.1 --port 8002
Restart=always
RestartSec=5
MemoryMax=4G

[Install]
WantedBy=multi-user.target
```

---

## Nginx 配置

完整的 nginx 配置位于 `deploy/nginx/fiido-ai-location.conf`。

### 关键配置

```nginx
server {
    listen 443 ssl http2;
    server_name ai.fiido.com;

    ssl_certificate /etc/letsencrypt/live/ai.fiido.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai.fiido.com/privkey.pem;

    # AI 客服前端
    location /chat-test/ {
        alias /var/www/fiido-frontend/;
        try_files $uri $uri/ /chat-test/index.html;
    }

    # 坐席工作台前端
    location /workbench/ {
        alias /var/www/fiido-workbench/;
        try_files $uri $uri/ /workbench/index.html;
    }

    # AI 客服 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    # 坐席工作台 API
    location /workbench-api/ {
        rewrite ^/workbench-api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    # 静态资源
    location /assets/ {
        alias /opt/fiido-ai-service/assets/;
        expires 7d;
    }
}
```

---

## 故障排查

### 服务无法启动

1. 检查 Python 虚拟环境
   ```bash
   /opt/fiido-ai-service/venv/bin/python --version
   ```

2. 检查依赖是否完整
   ```bash
   /opt/fiido-ai-service/venv/bin/pip list
   ```

3. 手动运行测试
   ```bash
   cd /opt/fiido-ai-service
   source venv/bin/activate
   python -c "from products.ai_chatbot.main import app; print('OK')"
   ```

### 端口被占用

```bash
# 查看端口占用
sudo lsof -i :8000
sudo lsof -i :8002

# 杀死占用进程
sudo kill -9 <PID>
```

### 日志分析

```bash
# 查看错误日志
sudo journalctl -u fiido-ai-chatbot -p err

# 查看启动失败原因
sudo systemctl status fiido-ai-chatbot -l
```

---

## 废弃服务

以下服务已废弃，不再使用：

| 服务 | 原用途 | 废弃原因 |
|------|--------|----------|
| fiido-backend.service | 全家桶模式 | 已切换到微服务架构 |
| fiido-ai-backend.service | 旧版后端 | 已重构 |

---

## 更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-23 | 更新为微服务架构，移除全家桶模式 |
| v1.0 | 2025-12-18 | 初始版本 |
