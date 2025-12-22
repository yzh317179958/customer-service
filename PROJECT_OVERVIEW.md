# Fiido 智能服务平台 - 项目架构概览

> **最后更新**：2025-12-22
> **文档版本**：v7.2
> **代码版本**：v7.5.11

---

## 一、项目简介

Fiido 智能服务平台是面向跨境电商的一站式 AI 解决方案，采用三层架构设计，支持多产品独立开发与部署。

**支持两种部署模式**：
- **全家桶模式**：单进程启动所有产品（适合单机部署）
- **独立模式**：每个产品独立进程（适合商业化按需订阅）

---

## 二、技术架构

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Products 产品层                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │ AI 智能客服  │  │ 坐席工作台   │  │ 物流通知     │  │ 客户控制台   │
│  │ ai_chatbot   │  │agent_workbench│  │ notification │  │customer_portal│
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
│         │                 │                 │                 │
├─────────┴─────────────────┴─────────────────┴─────────────────┴─────────┤
│                        Services 服务层                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │
│  │Shopify │ │ Email  │ │ Coze   │ │ Ticket │ │Session │ │Billing │     │
│  └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘     │
│       │          │          │          │          │          │         │
├───────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────────┤
│                     Infrastructure 基础设施层                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │Database│ │Scheduler│ │Logging │ │Monitor │ │Security│        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 依赖规则

| 依赖方向 | 是否允许 |
|----------|----------|
| products → services | 允许 |
| products → infrastructure | 允许 |
| services → infrastructure | 允许 |
| services → products | **禁止** |
| infrastructure → 上层 | **禁止** |
| products 之间 | **禁止** |

---

## 三、目录结构

```
/home/yzh/AI客服/鉴权/
│
├── 【核心文件】
├── backend.py                   # 主服务入口（全家桶模式）
├── CLAUDE.md                    # 最高开发规范
├── PROJECT_OVERVIEW.md          # 本文档
├── requirements.txt             # Python 依赖
├── .env                         # 环境配置
├── README.md                    # 项目说明
│
├── 【三层架构】
├── products/                    # 产品层
│   ├── README.md               # 产品层规范
│   ├── ai_chatbot/             # AI 智能客服（含 frontend/ 前端、prompts/ 提示词）
│   ├── agent_workbench/        # 坐席工作台
│   ├── customer_portal/        # 客户控制台
│   └── notification/           # 物流通知
│
├── services/                    # 服务层
│   ├── README.md               # 服务层规范
│   ├── bootstrap/              # 依赖注入注册（将服务实现注册到基础设施层）
│   ├── shopify/                # Shopify 订单服务
│   ├── email/                  # 邮件服务
│   ├── coze/                   # Coze AI 服务
│   ├── ticket/                 # 工单服务
│   ├── session/                # 会话服务
│   ├── asset/                  # 素材服务（含 data/ 素材数据、tools/ 工具脚本）
│   └── billing/                # 计费服务
│
├── infrastructure/              # 基础设施层
│   ├── README.md               # 基础设施规范
│   ├── bootstrap/              # 启动引导（组件工厂、依赖注入）
│   ├── database/               # 数据库（PostgreSQL + Redis）
│   ├── scheduler/              # 定时任务
│   ├── logging/                # 日志
│   ├── monitoring/             # 监控
│   └── security/               # 安全认证
│
├── 【资源与配置】
├── config/                      # 配置文件（私钥等）
│
├── 【运维与文档】
├── deploy/                      # 部署配置（含 scripts/ 启动脚本）
├── docs/                        # 文档
│   └── prd/                    # PRD 文档
├── tests/                       # 测试
```

---

## 四、产品清单

| 产品 | 目录 | 状态 | 说明 |
|------|------|------|------|
| AI 智能客服 | products/ai_chatbot | 已上线 | 核心产品 |
| 坐席工作台 | products/agent_workbench | 已上线 | 人工客服后端 |
| 客户控制台 | products/customer_portal | 规划中 | 订阅、用量、账单管理 |
| 物流通知 | products/notification | 规划中 | 预售/拆包裹/异常监控 |

---

## 五、服务清单

| 服务 | 目录 | 状态 | 说明 |
|------|------|------|------|
| **依赖注入注册** | **services/bootstrap** | **已完成** | **将服务实现注册到基础设施层工厂** |
| Shopify 订单 | services/shopify | 已完成 | 多站点订单查询、缓存预热 |
| 邮件服务 | services/email | 已完成 | SMTP 邮件发送 |
| Coze AI | services/coze | 已完成 | AI 对话服务、JWT签名 |
| 工单服务 | services/ticket | 已完成 | 工单管理、协助请求、自动化规则 |
| 会话服务 | services/session | 已完成 | 会话状态管理 |
| 素材服务 | services/asset | 已完成 | 产品图片匹配、CDN素材 |
| 计费服务 | services/billing | 规划中 | 套餐、订阅、用量、账单 |

---

## 六、基础设施清单

| 组件 | 目录 | 状态 | 说明 |
|------|------|------|------|
| **启动引导** | **infrastructure/bootstrap** | **已完成** | **组件工厂、依赖注入、后台任务调度** |
| 安全认证 | infrastructure/security | 已完成 | JWT签名、坐席认证 |
| 监控 | infrastructure/monitoring | 已完成 | CDN 健康检查 |
| 数据库 | infrastructure/database | 已完成 | PostgreSQL + Redis，双写模式 |
| 定时任务 | infrastructure/scheduler | 待迁移 | APScheduler |
| 日志 | infrastructure/logging | 待创建 | 日志配置 |

### Bootstrap 模块详情

Bootstrap 模块负责所有组件的统一初始化，包含以下文件：

| 文件 | 功能 |
|------|------|
| `__init__.py` | 模块导出 |
| `factory.py` | 组件工厂（依赖注入） |
| `redis.py` | Redis/Session 初始化 |
| `coze.py` | Coze Client 初始化 |
| `auth.py` | 坐席认证系统初始化 |
| `ticket.py` | 工单系统初始化 |
| `sse.py` | SSE 队列管理 |
| `scheduler.py` | 后台任务调度器 |

### Database 模块详情

数据库模块支持 PostgreSQL + Redis 双写模式，包含以下组件：

| 文件/目录 | 功能 |
|------|------|
| `base.py` | SQLAlchemy Base 类 |
| `connection.py` | PostgreSQL 连接池管理 |
| `converters.py` | Pydantic ↔ ORM 转换器 |
| `models/` | ORM 模型（9 个表） |
| `migrations/` | Alembic 数据库迁移 |

**数据表：**
- tickets, ticket_comments, ticket_attachments, ticket_status_history, ticket_assignments
- agents, audit_logs, session_archives, email_records

**双写策略：**
```
写入: PostgreSQL（主存储） → Redis（缓存）
读取: PostgreSQL 优先 → Redis 降级
```

**支持双写的服务：**
| 服务 | 文件 | 说明 |
|------|------|------|
| 工单存储 | services/ticket/store.py | 工单 CRUD |
| 审计日志 | services/ticket/audit.py | 操作日志 |
| 会话归档 | services/session/archive.py | 历史会话 |
| 邮件记录 | services/email/service.py | 发送记录 |
| 坐席管理 | infrastructure/security/agent_auth.py | 账号管理 |

---

## 七、部署模式

### 7.1 全家桶模式（推荐单机部署）

```bash
# 启动命令
uvicorn backend:app --host 0.0.0.0 --port 8000

# 或使用脚本
./deploy/scripts/start.sh all
```

所有产品在同一进程中运行，共享初始化逻辑。

### 7.2 独立模式（推荐商业化部署）

```bash
# 仅启动 AI 客服
uvicorn products.ai_chatbot.main:app --host 0.0.0.0 --port 8001

# 仅启动坐席工作台
uvicorn products.agent_workbench.main:app --host 0.0.0.0 --port 8002

# 或使用脚本
./deploy/scripts/start.sh ai-chatbot
./deploy/scripts/start.sh agent-workbench
```

每个产品独立进程，按需启动。

### 7.3 端口分配

| 服务 | 端口 | 模式 |
|------|------|------|
| backend（全家桶） | 8000 | 全家桶 |
| ai_chatbot | 8001 | 独立 |
| agent_workbench | 8002 | 独立 |

### 7.4 Systemd 服务

服务配置文件位于 `deploy/systemd/`：

| 文件 | 说明 |
|------|------|
| fiido-backend.service | 全家桶模式 |
| fiido-ai-chatbot.service | AI 客服独立模式 |
| fiido-agent-workbench.service | 坐席工作台独立模式 |

---

## 八、开发规范

### 8.1 规范层级

```
CLAUDE.md（全局最高法）
    ↓
各层 README.md（层级规范）
    ↓
各模块 README.md（模块规范）
```

### 8.2 Vibe Coding 文档

每个产品模块必须包含 `memory-bank/` 文件夹：

| 文件 | 用途 |
|------|------|
| prd.md | 产品需求文档 |
| tech-stack.md | 技术栈说明 |
| implementation-plan.md | 实施计划 |
| progress.md | 进度追踪 |
| architecture.md | 架构设计 |

---

## 九、快速导航

### 产品模块
- [AI 智能客服](products/ai_chatbot/README.md)
- [坐席工作台](products/agent_workbench/README.md)
- [客户控制台](products/customer_portal/README.md)
- [物流通知](products/notification/README.md)

### 服务模块
- [Shopify 订单](services/shopify/README.md)
- [邮件服务](services/email/README.md)
- [Coze AI](services/coze/README.md)
- [工单服务](services/ticket/README.md)
- [会话服务](services/session/README.md)
- [计费服务](services/billing/README.md)

### 基础设施
- [数据库](infrastructure/database/README.md)
- [定时任务](infrastructure/scheduler/README.md)
- [日志](infrastructure/logging/README.md)
- [监控](infrastructure/monitoring/README.md)
- [安全](infrastructure/security/README.md)

---

## 十、相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 最高开发规范 | CLAUDE.md | 必读 |
| 开发参考手册 | docs/开发参考手册.md | 服务器、部署 |
| 安全防护方案 | docs/安全防护方案.md | 安全措施 |
| 物流通知设计 | docs/物流通知与异常监控设计方案.md | 物流模块 |

---

*文档版本 v7.2 - 2025-12-22 (新增 PostgreSQL 数据库模块，双写模式)*
