# Fiido 智能服务平台 - 项目架构概览

> **最后更新**：2025-12-18
> **文档版本**：v2.0

---

## 一、项目简介

Fiido 智能服务平台是面向跨境电商的一站式 AI 解决方案，采用三层架构设计，支持多产品独立开发与部署。

---

## 二、技术架构

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Products 产品层                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ AI 智能客服  │  │ 坐席工作台   │  │ 物流通知     │          │
│  │ ai_chatbot   │  │agent_workbench│  │ notification │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
├─────────┴─────────────────┴─────────────────┴───────────────────┤
│                        Services 服务层                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │Shopify │ │ Email  │ │ Coze   │ │ Ticket │ │Session │        │
│  └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘        │
│       │          │          │          │          │             │
├───────┴──────────┴──────────┴──────────┴──────────┴─────────────┤
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
├── CLAUDE.md                    # 最高开发规范
├── PROJECT_OVERVIEW.md          # 本文档
│
├── products/                    # 产品层
│   ├── README.md               # 产品层规范
│   ├── ai_chatbot/             # AI 智能客服
│   ├── agent_workbench/        # 坐席工作台
│   └── notification/           # 物流通知
│
├── services/                    # 服务层
│   ├── README.md               # 服务层规范
│   ├── shopify/                # Shopify 订单服务
│   ├── email/                  # 邮件服务
│   ├── coze/                   # Coze AI 服务
│   ├── ticket/                 # 工单服务
│   └── session/                # 会话服务
│
├── infrastructure/              # 基础设施层
│   ├── README.md               # 基础设施规范
│   ├── database/               # 数据库（Redis）
│   ├── scheduler/              # 定时任务
│   ├── logging/                # 日志
│   ├── monitoring/             # 监控
│   └── security/               # 安全
│
├── frontend/                    # 用户端前端
├── agent-workbench/             # 坐席工作台前端
├── docs/                        # 文档
├── tests/                       # 测试
└── prompts/                     # AI 提示词
```

---

## 四、产品清单

| 产品 | 目录 | 状态 | 说明 |
|------|------|------|------|
| AI 智能客服 | products/ai_chatbot | 已上线 | 核心产品 |
| 坐席工作台 | products/agent_workbench | 已上线 | 人工客服后端 |
| 物流通知 | products/notification | 规划中 | 预售/拆包裹/异常监控 |

---

## 五、服务清单

| 服务 | 目录 | 状态 | 说明 |
|------|------|------|------|
| Shopify 订单 | services/shopify | 已完成 | 多站点订单查询 |
| 邮件服务 | services/email | 已完成 | SMTP 邮件发送 |
| Coze AI | services/coze | 已完成 | AI 对话服务 |
| 工单服务 | services/ticket | 已完成 | 工单管理 |
| 会话服务 | services/session | 已完成 | 会话状态管理 |

---

## 六、基础设施清单

| 组件 | 目录 | 状态 | 说明 |
|------|------|------|------|
| 数据库 | infrastructure/database | 待迁移 | Redis 连接 |
| 定时任务 | infrastructure/scheduler | 待迁移 | APScheduler |
| 日志 | infrastructure/logging | 待创建 | 日志配置 |
| 监控 | infrastructure/monitoring | 待迁移 | 健康检查 |
| 安全 | infrastructure/security | 待创建 | 限流、校验 |

---

## 七、开发规范

### 7.1 规范层级

```
CLAUDE.md（全局最高法）
    ↓
各层 README.md（层级规范）
    ↓
各模块 README.md（模块规范）
```

### 7.2 Vibe Coding 文档

每个产品模块必须包含 `memory-bank/` 文件夹：

| 文件 | 用途 |
|------|------|
| prd.md | 产品需求文档 |
| tech-stack.md | 技术栈说明 |
| implementation-plan.md | 实施计划 |
| progress.md | 进度追踪 |
| architecture.md | 架构设计 |

---

## 八、快速导航

### 产品模块
- [AI 智能客服](products/ai_chatbot/README.md)
- [坐席工作台](products/agent_workbench/README.md)
- [物流通知](products/notification/README.md)

### 服务模块
- [Shopify 订单](services/shopify/README.md)
- [邮件服务](services/email/README.md)
- [Coze AI](services/coze/README.md)
- [工单服务](services/ticket/README.md)
- [会话服务](services/session/README.md)

### 基础设施
- [数据库](infrastructure/database/README.md)
- [定时任务](infrastructure/scheduler/README.md)
- [日志](infrastructure/logging/README.md)
- [监控](infrastructure/monitoring/README.md)
- [安全](infrastructure/security/README.md)

---

## 九、相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 最高开发规范 | CLAUDE.md | 必读 |
| 开发参考手册 | docs/开发参考手册.md | 服务器、部署 |
| 安全防护方案 | docs/安全防护方案.md | 安全措施 |
| 物流通知设计 | docs/物流通知与异常监控设计方案.md | 物流模块 |

---

*文档版本 v2.0 - 2025-12-18*
