# Products 产品层规范

> **层级定位**：面向用户的完整功能模块，独立微服务部署
> **最后更新**：2025-12-23
> **文档版本**：v2.0

---

## 一、层级职责

产品层包含所有面向用户的完整功能，每个产品：

- 有独立的 main.py 启动入口
- 有独立的 API 端点和路由
- 有完整的业务逻辑
- **独立进程、独立端口运行**（微服务架构）
- 包含前端代码（frontend/ 目录）

---

## 二、当前产品清单

| 产品 | 目录 | 端口 | systemd 服务 | 状态 | 说明 |
|------|------|------|--------------|------|------|
| AI 智能客服 | ai_chatbot/ | 8000 | fiido-ai-chatbot | ✅ 已上线 | 核心产品，AI 对话 |
| 坐席工作台 | agent_workbench/ | 8002 | fiido-agent-workbench | ✅ 已上线 | 人工客服后台 |
| 客户控制台 | customer_portal/ | - | - | 📋 规划中 | 商家自助管理 |
| 物流通知 | notification/ | - | - | 📋 规划中 | 预售/拆包裹/异常监控 |

---

## 三、微服务架构

### 3.1 独立部署模式

每个产品作为独立微服务运行：

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
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌───────────────────┐                      ┌───────────────────┐
│   AI 智能客服      │                      │   坐席工作台       │
│   Port: 8000      │                      │   Port: 8002      │
│   独立进程运行     │                      │   独立进程运行     │
└───────────────────┘                      └───────────────────┘
```

### 3.2 启动方式

```bash
# 独立启动单个产品
uvicorn products.ai_chatbot.main:app --host 127.0.0.1 --port 8000
uvicorn products.agent_workbench.main:app --host 127.0.0.1 --port 8002

# 通过 systemd 管理
systemctl start fiido-ai-chatbot
systemctl start fiido-agent-workbench
```

---

## 四、依赖规则

### 4.1 允许的依赖

```python
# ✅ 可以依赖 services 层
from services.shopify import get_shopify_service
from services.email import EmailService
from services.ticket import TicketService

# ✅ 可以依赖 infrastructure 层
from infrastructure.database import get_redis_client, get_async_session
from infrastructure.security import require_agent_auth
```

### 4.2 禁止的依赖

```python
# ❌ 禁止依赖其他产品
from products.agent_workbench import xxx  # 禁止！

# ❌ 禁止被 services 或 infrastructure 依赖
# services 层不能 import products
```

### 4.3 产品间通信

产品之间需要协作时，通过以下方式：

| 方式 | 说明 | 示例 |
|------|------|------|
| 共享服务 | 通过 services 层间接通信 | 都使用 services/session |
| 数据库 | 通过 PostgreSQL/Redis 共享数据 | ai_chatbot 写工单，agent_workbench 读取 |
| API 调用 | 通过 HTTP API 通信 | 跨服务调用 |
| 事件机制 | Redis Pub/Sub | 实时消息推送 |

---

## 五、产品目录结构

每个产品必须遵循以下结构：

```
products/xxx/
├── __init__.py                 # 模块初始化
├── main.py                     # 【必须】微服务启动入口
├── routes.py                   # API 路由定义
├── README.md                   # 【必须】模块规范文档
├── handlers/                   # 业务处理器
│   └── xxx_handler.py
├── frontend/                   # 前端代码
│   ├── src/                   # 源码
│   ├── dist/                  # 构建产物（纳入 git）
│   ├── package.json
│   └── vite.config.ts
├── memory-bank/                # 【必须】Vibe Coding 文档
│   ├── prd.md                 # 产品需求文档
│   ├── tech-stack.md          # 技术栈说明
│   ├── implementation-plan.md # 实现计划
│   ├── progress.md            # 进度追踪
│   ├── architecture.md        # 架构说明
│   └── cross-module-refs.md   # 跨模块引用（如有）
└── tests/                      # 单元测试
    └── test_xxx.py
```

---

## 六、开发规范

### 6.1 新建产品流程

1. 在 products/ 下创建产品目录
2. 创建 main.py 作为微服务启动入口
3. 创建 README.md 定义模块规范
4. 创建 memory-bank/ 并编写文档
5. 实现功能代码
6. 创建 frontend/ 前端项目
7. 配置 systemd 服务文件
8. 配置 nginx 反向代理

### 6.2 main.py 模板

```python
"""
产品名称 - 微服务入口

启动方式：
    uvicorn products.xxx.main:app --host 127.0.0.1 --port 800X
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="产品名称",
    description="产品描述",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)

@app.get("/")
async def root():
    return {"service": "xxx", "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}
```

### 6.3 开发原则

| 原则 | 说明 |
|------|------|
| 文档先行 | 先写 memory-bank 文档，再写代码 |
| 小步快跑 | 每步只做一件事，立即测试 |
| 复用优先 | 优先使用 services 已有能力 |
| 不破坏现有 | 任何改动不能影响其他产品 |
| 独立部署 | 每个产品可独立启停 |

### 6.4 API 路由规范

```python
# routes.py 示例
from fastapi import APIRouter

router = APIRouter(
    prefix="/api",  # 统一前缀
    tags=["产品名称"]
)

@router.post("/action")
async def action():
    pass
```

---

## 七、部署配置

### 7.1 systemd 服务模板

```ini
# /etc/systemd/system/fiido-xxx.service
[Unit]
Description=Fiido XXX Microservice
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fiido-ai-service
Environment="PATH=/opt/fiido-ai-service/venv/bin"
Environment="PYTHONPATH=/opt/fiido-ai-service"
EnvironmentFile=/opt/fiido-ai-service/.env
ExecStart=/opt/fiido-ai-service/venv/bin/uvicorn products.xxx.main:app --host 127.0.0.1 --port 800X
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7.2 nginx 配置模板

```nginx
# 前端静态文件
location /xxx-path/ {
    alias /var/www/fiido-xxx/;
    try_files $uri $uri/ /xxx-path/index.html;
}

# API 反向代理
location /xxx-api/ {
    rewrite ^/xxx-api/(.*) /$1 break;
    proxy_pass http://127.0.0.1:800X;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## 八、测试要求

- 每个产品必须有 tests/ 目录
- 核心功能必须有单元测试
- 新功能必须通过测试才能提交
- 不能破坏现有测试

---

## 九、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-23 | 重构为微服务架构，添加独立部署说明、systemd/nginx 配置模板 |
| v1.0 | 2025-12-18 | 初始版本 |
