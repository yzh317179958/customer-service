# Fiido 智能服务平台 - Systemd 服务配置

本目录包含 Fiido 平台各产品模块的 Systemd 服务配置文件。

## 部署模式

### 1. 全家桶模式（推荐用于单机部署）

启动所有产品在同一进程中：

```bash
# 安装服务
sudo cp fiido-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fiido-backend
sudo systemctl start fiido-backend
```

### 2. 独立模式（推荐用于商业化部署）

每个产品独立运行，可按需启用：

```bash
# 安装 AI 客服服务
sudo cp fiido-ai-chatbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fiido-ai-chatbot
sudo systemctl start fiido-ai-chatbot

# 安装坐席工作台服务
sudo cp fiido-agent-workbench.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fiido-agent-workbench
sudo systemctl start fiido-agent-workbench
```

## 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| fiido-backend（全家桶） | 8000 | 包含所有产品 |
| fiido-ai-chatbot | 8001 | AI 智能客服 |
| fiido-agent-workbench | 8002 | 坐席工作台 |

## 常用命令

```bash
# 查看服务状态
sudo systemctl status fiido-backend

# 查看日志
sudo journalctl -u fiido-backend -f

# 重启服务
sudo systemctl restart fiido-backend

# 停止服务
sudo systemctl stop fiido-backend
```

## Nginx 反向代理配置示例

```nginx
# 全家桶模式
upstream fiido_backend {
    server 127.0.0.1:8000;
}

# 独立模式 - 按路径路由
upstream fiido_ai_chatbot {
    server 127.0.0.1:8001;
}

upstream fiido_agent_workbench {
    server 127.0.0.1:8002;
}

server {
    listen 443 ssl;
    server_name ai.fiido.com;

    # 独立模式路由示例
    location /api/chat {
        proxy_pass http://fiido_ai_chatbot;
    }

    location /api/agent {
        proxy_pass http://fiido_agent_workbench;
    }

    # 或者全家桶模式
    location / {
        proxy_pass http://fiido_backend;
    }
}
```
