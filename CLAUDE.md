# Fiido 智能服务平台 - 最高开发规范

> **文档性质**：最高法案，所有开发必须遵守
> **文档版本**：v6.0
> **最后更新**：2025-12-23

---

## 一、项目定位

Fiido 智能服务平台是面向跨境电商的一站式 AI 解决方案，采用**微服务架构**设计，每个产品独立部署运行。

**当前部署模式**：
- **微服务模式**：每个产品独立进程，独立端口
  - AI 智能客服：`uvicorn products.ai_chatbot.main:app` → 端口 8000
  - 坐席工作台：`uvicorn products.agent_workbench.main:app` → 端口 8002

---

## 二、架构总览

### 2.1 微服务架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                           nginx (443/80)                             │
│                        反向代理 + SSL 终结                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  AI 智能客服   │      │  坐席工作台    │      │   静态资源     │
│   Port 8000   │      │   Port 8002   │      │   /assets/    │
│  /api/*       │      │ /workbench-api│      │               │
└───────┬───────┘      └───────┬───────┘      └───────────────┘
        │                      │
        └──────────┬───────────┘
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       services/ 服务层                               │
│                                                                     │
│   可复用的业务服务，被多个产品共享                                    │
│                                                                     │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│   │shopify │ │ email  │ │  coze  │ │ ticket │ │session │  ...     │
│   └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘          │
└────────┼──────────┼──────────┼──────────┼──────────┼────────────────┘
         │          │          │          │          │
         ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   infrastructure/ 基础设施层                         │
│                                                                     │
│   底层技术组件，无业务逻辑                                            │
│                                                                     │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│   │database│ │scheduler│ │logging │ │monitor │ │security│          │
│   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Redis + PgSQL  │
         └─────────────────┘
```

### 2.2 目录结构

```
/home/yzh/AI客服/鉴权/                    # 本地开发目录
/opt/fiido-ai-service/                   # 服务器部署目录
│
├── 【核心文件】
├── CLAUDE.md                    # 【本文件】最高开发规范
├── PROJECT_OVERVIEW.md          # 架构总览与模块清单
├── requirements.txt             # Python 依赖
├── .env                         # 环境配置
├── README.md                    # 项目说明
│
├── 【三层架构】
├── products/                    # 【产品层】- 独立微服务
│   ├── README.md               # 产品层规范
│   ├── ai_chatbot/             # AI 智能客服（含 frontend/ 前端）
│   │   ├── main.py            # 独立启动入口
│   │   ├── routes.py          # API 路由
│   │   ├── handlers/          # 请求处理
│   │   └── frontend/dist/     # 前端构建产物
│   ├── agent_workbench/        # 坐席工作台（含 frontend/ 前端）
│   │   ├── main.py            # 独立启动入口
│   │   ├── routes.py          # API 路由
│   │   ├── handlers/          # 请求处理
│   │   └── frontend/dist/     # 前端构建产物
│   ├── customer_portal/        # 客户控制台（规划中）
│   └── notification/           # 物流通知（规划中）
│
├── services/                    # 【服务层】
│   ├── README.md               # 服务层规范
│   ├── bootstrap/              # 依赖注入注册
│   ├── shopify/                # Shopify 订单服务
│   ├── email/                  # 邮件服务
│   ├── coze/                   # Coze AI 服务
│   ├── ticket/                 # 工单服务
│   ├── session/                # 会话服务
│   ├── asset/                  # 素材服务
│   ├── tracking/               # 物流追踪服务
│   └── billing/                # 计费服务（规划中）
│
├── infrastructure/              # 【基础设施层】
│   ├── README.md               # 基础设施规范
│   ├── bootstrap/              # 启动引导（组件工厂、依赖注入）
│   ├── database/               # 数据库（PostgreSQL + Redis 双写）
│   ├── scheduler/              # 定时任务
│   ├── logging/                # 日志系统
│   ├── monitoring/             # 监控告警
│   └── security/               # 安全认证（JWT、坐席认证）
│
├── 【资源与配置】
├── assets/                      # 静态资源（产品图片等）
├── config/                      # 配置文件（私钥等）
│
├── 【运维与文档】
├── deploy/                      # 部署配置
├── docs/                        # 文档
```

### 2.3 各层职责

| 层级 | 职责 | 特点 |
|------|------|------|
| **products/** | 面向用户的完整功能 | 独立微服务、独立端口、可独立部署 |
| **services/** | 可复用的业务服务 | 被多个产品共享、封装业务能力 |
| **infrastructure/** | 底层技术组件 | 无业务逻辑、纯技术封装 |

---

## 三、生产服务器配置（当前部署）

### 3.1 服务器信息

| 配置项 | 值 |
|--------|-----|
| 服务器地址 | 8.211.27.199 |
| 项目目录 | /opt/fiido-ai-service/ |
| 虚拟环境 | /opt/fiido-ai-service/venv/ |
| 前端目录 | /var/www/fiido-frontend/ (AI客服) |
|          | /var/www/fiido-workbench/ (坐席工作台) |

### 3.2 微服务端口分配

| 服务 | 端口 | systemd 服务名 | 外部访问路径 |
|------|------|----------------|--------------|
| AI 智能客服 | 8000 | fiido-ai-chatbot | /api/* |
| 坐席工作台 | 8002 | fiido-agent-workbench | /workbench-api/* |

### 3.3 访问地址

| 功能 | URL |
|------|-----|
| AI 客服前端 | https://ai.fiido.com/chat-test/ |
| 坐席工作台前端 | https://ai.fiido.com/workbench/ |
| AI 客服 API | https://ai.fiido.com/api/ |
| 坐席工作台 API | https://ai.fiido.com/workbench-api/ |
| 静态资源 | https://ai.fiido.com/assets/ |

### 3.4 systemd 服务配置

**AI 智能客服服务** (`/etc/systemd/system/fiido-ai-chatbot.service`):
```ini
[Unit]
Description=Fiido AI Chatbot Microservice
After=network.target redis-server.service
Wants=redis-server.service

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

**坐席工作台服务** (`/etc/systemd/system/fiido-agent-workbench.service`):
```ini
[Unit]
Description=Fiido Agent Workbench Microservice
After=network.target redis-server.service
Wants=redis-server.service

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

### 3.5 nginx 配置

```nginx
server {
    server_name ai.fiido.com;

    # AI客服前端
    location /chat-test {
        alias /var/www/fiido-frontend;
        index index.html;
        try_files $uri $uri/ /chat-test/index.html;
    }

    # 坐席工作台前端
    location /workbench {
        alias /var/www/fiido-workbench;
        index index.html;
        try_files $uri $uri/ /workbench/index.html;
    }

    # 静态资源
    location /assets/ {
        alias /opt/fiido-ai-service/assets/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 坐席工作台 API
    location /workbench-api {
        rewrite ^/workbench-api(.*)$ /api$1 break;
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_buffering off;
    }

    # AI客服 API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_read_timeout 120s;
    }

    # 根路径
    location / {
        proxy_pass http://127.0.0.1:8000;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/ai.fiido.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai.fiido.com/privkey.pem;
}
```

### 3.6 常用运维命令

```bash
# 查看服务状态
systemctl status fiido-ai-chatbot fiido-agent-workbench

# 重启服务
systemctl restart fiido-ai-chatbot fiido-agent-workbench

# 查看日志
journalctl -u fiido-ai-chatbot -f
journalctl -u fiido-agent-workbench -f

# ⚠️ 部署更新（从本地同步）- 必须分开同步每个目录！
# 【重要】不要把 services/ 和 infrastructure/ 直接同步到根目录！
# 否则 email/, logging/ 等目录会覆盖 Python 标准库导致服务启动失败！
cd /home/yzh/AI客服/鉴权
rsync -avz --exclude '__pycache__' --exclude 'node_modules' --exclude '.git' \
  products/ root@8.211.27.199:/opt/fiido-ai-service/products/
rsync -avz --exclude '__pycache__' --exclude 'node_modules' --exclude '.git' \
  services/ root@8.211.27.199:/opt/fiido-ai-service/services/
rsync -avz --exclude '__pycache__' --exclude 'node_modules' --exclude '.git' \
  infrastructure/ root@8.211.27.199:/opt/fiido-ai-service/infrastructure/
rsync -avz assets/ root@8.211.27.199:/opt/fiido-ai-service/assets/
rsync -avz config/ root@8.211.27.199:/opt/fiido-ai-service/config/
rsync -avz requirements.txt .env root@8.211.27.199:/opt/fiido-ai-service/

# 部署前端（在服务器上执行）
ssh root@8.211.27.199 "cp -r /opt/fiido-ai-service/products/ai_chatbot/frontend/dist/* /var/www/fiido-frontend/"
ssh root@8.211.27.199 "cp -r /opt/fiido-ai-service/products/agent_workbench/frontend/dist/* /var/www/fiido-workbench/"

# 完整重启
ssh root@8.211.27.199 "systemctl restart fiido-ai-chatbot fiido-agent-workbench"
```

### 3.7 部署注意事项（铁律）

**⚠️ 绝对禁止以下操作：**

```bash
# ❌ 错误！会导致 email/, logging/ 等目录覆盖 Python 标准库！
rsync services/ infrastructure/ root@8.211.27.199:/opt/fiido-ai-service/

# ❌ 错误！同上
rsync -avz products/ services/ infrastructure/ root@8.211.27.199:/opt/fiido-ai-service/
```

**服务器目录结构必须是：**
```
/opt/fiido-ai-service/
├── products/           # 产品层
│   ├── ai_chatbot/
│   └── agent_workbench/
├── services/           # 服务层（在 services/ 子目录下）
│   ├── email/          # 不是 /opt/fiido-ai-service/email/
│   ├── shopify/
│   └── ...
├── infrastructure/     # 基础设施层（在 infrastructure/ 子目录下）
│   ├── logging/        # 不是 /opt/fiido-ai-service/logging/
│   └── ...
└── ...
```

**如果服务启动失败报 `AttributeError: module 'logging' has no attribute 'getLogger'`：**
```bash
# 检查并删除错误同步的目录
ssh root@8.211.27.199 "ls /opt/fiido-ai-service/ | grep -E '^(email|logging|monitoring|scheduler|security|session|shopify|ticket|tracking|bootstrap|coze|billing|asset|notification|database)$'"

# 如果有输出，删除这些目录
ssh root@8.211.27.199 "cd /opt/fiido-ai-service && rm -rf email logging monitoring scheduler security session shopify ticket tracking bootstrap coze billing asset notification database"

# 重新同步
rsync -avz services/ root@8.211.27.199:/opt/fiido-ai-service/services/
rsync -avz infrastructure/ root@8.211.27.199:/opt/fiido-ai-service/infrastructure/

# 重启服务
ssh root@8.211.27.199 "systemctl restart fiido-ai-chatbot fiido-agent-workbench"
```

---

## 四、依赖规则（铁律）

### 4.1 单向依赖原则

```
products/ ──────► services/ ──────► infrastructure/
   │                 │                    │
   │                 │                    │
   ▼                 ▼                    ▼
 可以依赖          可以依赖             最底层
 services/       infrastructure/        无依赖
```

### 4.2 依赖规则表

| 规则 | 说明 | 示例 |
|------|------|------|
| products → services | 允许 | ai_chatbot 可以 import services.shopify |
| products → infrastructure | 允许 | ai_chatbot 可以 import infrastructure.database |
| services → infrastructure | 允许 | shopify 可以 import infrastructure.database |
| services → products | **禁止** | shopify 不能 import products.ai_chatbot |
| infrastructure → services | **禁止** | database 不能 import services.shopify |
| infrastructure → products | **禁止** | database 不能 import products.ai_chatbot |
| products 之间 | **禁止** | ai_chatbot 不能 import agent_workbench |

### 4.3 产品间通信方式

产品之间不能直接 import，但可以通过以下方式协作：

| 方式 | 说明 | 示例 |
|------|------|------|
| 共享服务 | 通过 services 层间接通信 | ai_chatbot 和 agent_workbench 都用 session 服务 |
| 数据库 | 通过 PostgreSQL/Redis 共享数据 | ai_chatbot 写入工单，agent_workbench 读取 |
| API 调用 | 通过 HTTP API 通信 | 一个产品调用另一个产品的 API |
| 事件机制 | 发布/订阅事件 | ai_chatbot 发布事件，notification 订阅 |

### 4.4 数据库双写策略

系统采用 **PostgreSQL 主存储 + Redis 缓存** 的双写模式：

```
写入流程：
1. 先写入 PostgreSQL（主存储，数据源）
2. 再写入 Redis（缓存，高频访问）
3. Redis 失败重试一次，仍失败则记录日志但不阻塞业务

读取流程：
1. 优先从 PostgreSQL 查询（保证数据一致性）
2. PostgreSQL 失败时降级到 Redis/内存
```

---

## 五、开发原则（铁律）

### 5.1 自底向上开发

开发涉及多层时，必须按以下顺序：

```
1. infrastructure/（如需要）
        ↓
2. services/（如需要）
        ↓
3. products/（业务功能）
        ↓
4. 测试验证
        ↓
5. 部署上线
```

### 5.2 增量式开发

| 约束 | 要求 |
|------|------|
| 每步只做一件事 | 不要一次改太多 |
| 立即测试验证 | 改完就测，测完再继续 |
| 频繁提交 | 每个功能点完成即提交 |
| 单次提交文件数 | < 10 个 |
| 单次提交代码行数 | < 500 行 |

### 5.3 文档驱动开发

基于 Vibe Coding 方法论，每个模块必须包含 memory-bank 文件夹：

```
products/xxx/
├── memory-bank/
│   ├── prd.md                  # 产品需求文档
│   ├── tech-stack.md           # 技术栈说明
│   ├── implementation-plan.md  # 实现计划
│   ├── progress.md             # 进度追踪
│   └── architecture.md         # 架构说明
├── README.md                   # 模块规范
└── ...
```

---

## 六、版本号规范

格式：`v主版本.次版本.补丁版本`

| 版本位 | 触发条件 | 示例 |
|--------|----------|------|
| 补丁版本 | Bug 修复、小功能 | v7.6.18 → v7.6.19 |
| 次版本 | 新功能、新模块 | v7.6.19 → v7.7.0 |
| 主版本 | 重大架构变更 | v7.7.0 → v8.0.0 |

**当前版本**: v7.6.18

---

## 七、禁止事项（铁律）

### 7.1 架构禁止

- 禁止下层依赖上层（services 不能 import products）
- 禁止产品层横向依赖（ai_chatbot 不能 import agent_workbench）
- 禁止绕过服务层直接操作底层（products 不能直接操作 Redis，需通过 services）

### 7.2 开发禁止

- 禁止未经用户确认就提交代码
- 禁止未经用户确认就部署到服务器
- 禁止跳过测试就提交代码
- 禁止一次改动太多文件（>10 个）
- 禁止修改破坏现有功能

### 7.3 代码禁止

- 禁止修改 .env 中的核心凭证
- 禁止在代码中硬编码密钥
- 禁止删除现有的测试用例

---

## 八、必读文档

| 类型 | 路径 |
|------|------|
| 架构总览 | PROJECT_OVERVIEW.md |
| 产品层规范 | products/README.md |
| 服务层规范 | services/README.md |
| 基础设施规范 | infrastructure/README.md |
| 跨模块功能文档 | docs/features/README.md |

---

## 九、文档更新记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v6.0 | 2025-12-23 | **重大更新**：移除全家桶模式，改为纯微服务架构；更新服务器部署配置（端口8000/8002）；更新nginx配置；添加systemd服务详情 |
| v5.5 | 2025-12-22 | 拆分跨模块开发技能 |
| v5.4 | 2025-12-22 | 新增跨模块开发工作流 |
| v5.3 | 2025-12-22 | 新增 PostgreSQL 数据库模块，添加双写策略说明 |
