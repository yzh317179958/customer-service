# Fiido 智能服务平台 - 最高开发规范

> **文档性质**：最高法案，所有开发必须遵守
> **文档版本**：v3.1
> **最后更新**：2025-12-18

---

## 一、项目定位

Fiido 智能服务平台是面向跨境电商的一站式 AI 解决方案，采用三层架构设计，支持多产品独立开发与部署。

---

## 二、架构总览

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          backend.py                                  │
│                        （主服务入口）                                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       products/ 产品层                               │
│                                                                     │
│   面向用户的完整功能，有独立的 API 端点                               │
│                                                                     │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│   │ ai_chatbot  │  │   agent_    │  │notification │  ...          │
│   │ AI智能客服  │  │  workbench  │  │ 物流通知    │               │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │
└──────────┼─────────────────┼────────────────┼───────────────────────┘
           │                 │                │
           ▼                 ▼                ▼
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
│   │database│ │scheduler│ │logging │ │monitor │ │security│  ...     │
│   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
/home/yzh/AI客服/鉴权/
│
├── 【核心文件】
├── backend.py                   # 主服务入口（AI客服后端）
├── CLAUDE.md                    # 【本文件】最高开发规范
├── PROJECT_OVERVIEW.md          # 架构总览与模块清单
├── requirements.txt             # Python 依赖
├── .env                         # 环境配置
├── README.md                    # 项目说明
│
├── 【三层架构】
├── products/                    # 【产品层】
│   ├── README.md               # 产品层规范
│   ├── ai_chatbot/             # AI 智能客服
│   ├── agent_workbench/        # 坐席工作台
│   └── notification/           # 物流通知
│
├── services/                    # 【服务层】
│   ├── README.md               # 服务层规范
│   ├── shopify/                # Shopify 订单服务
│   ├── email/                  # 邮件服务
│   ├── coze/                   # Coze AI 服务
│   ├── ticket/                 # 工单服务
│   └── session/                # 会话服务
│
├── infrastructure/              # 【基础设施层】
│   ├── README.md               # 基础设施规范
│   ├── database/               # 数据库连接
│   ├── scheduler/              # 定时任务
│   ├── logging/                # 日志系统
│   ├── monitoring/             # 监控告警
│   └── security/               # 安全认证（JWT、坐席认证）
│
├── 【前端应用】
├── frontend/                    # 用户端前端（Vue）
│
├── 【资源与配置】
├── prompts/                     # AI 提示词模板
├── assets/                      # 静态资源（图片等）
├── config/                      # 配置文件（私钥等）
├── data/                        # 数据目录
│
├── 【运维与文档】
├── scripts/                     # 脚本工具
├── deploy/                      # 部署配置
├── docs/                        # 文档
│   └── prd/                    # PRD 文档
├── tests/                       # 测试
│
└── 【兼容层】
└── src/                         # 兼容层（重导出新模块，保持旧import可用）
```

### 2.3 各层职责

| 层级 | 职责 | 特点 |
|------|------|------|
| **products/** | 面向用户的完整功能 | 有 API 端点、有业务逻辑、可独立部署 |
| **services/** | 可复用的业务服务 | 被多个产品共享、封装业务能力 |
| **infrastructure/** | 底层技术组件 | 无业务逻辑、纯技术封装 |

---

## 三、依赖规则（铁律）

### 3.1 单向依赖原则

```
products/ ──────► services/ ──────► infrastructure/
   │                 │                    │
   │                 │                    │
   ▼                 ▼                    ▼
 可以依赖          可以依赖             最底层
 services/       infrastructure/        无依赖
```

### 3.2 依赖规则表

| 规则 | 说明 | 示例 |
|------|------|------|
| products → services | 允许 | ai_chatbot 可以 import services.shopify |
| products → infrastructure | 允许 | ai_chatbot 可以 import infrastructure.database |
| services → infrastructure | 允许 | shopify 可以 import infrastructure.database |
| services → products | **禁止** | shopify 不能 import products.ai_chatbot |
| infrastructure → services | **禁止** | database 不能 import services.shopify |
| infrastructure → products | **禁止** | database 不能 import products.ai_chatbot |
| products 之间 | **禁止** | ai_chatbot 不能 import agent_workbench |

### 3.3 产品间通信方式

产品之间不能直接 import，但可以通过以下方式协作：

| 方式 | 说明 | 示例 |
|------|------|------|
| 共享服务 | 通过 services 层间接通信 | ai_chatbot 和 agent_workbench 都用 session 服务 |
| 数据库/缓存 | 通过 Redis/数据库共享数据 | ai_chatbot 写入，agent_workbench 读取 |
| API 调用 | 通过 HTTP API 通信 | 一个产品调用另一个产品的 API |
| 事件机制 | 发布/订阅事件 | ai_chatbot 发布事件，notification 订阅 |

---

## 四、开发原则（铁律）

### 4.1 自底向上开发

开发涉及多层时，必须按以下顺序：

```
1. infrastructure/（如需要）
        ↓
2. services/（如需要）
        ↓
3. products/（业务功能）
        ↓
4. backend.py（注册路由，如需要）
        ↓
5. 测试验证
```

### 4.2 增量式开发

| 约束 | 要求 |
|------|------|
| 每步只做一件事 | 不要一次改太多 |
| 立即测试验证 | 改完就测，测完再继续 |
| 频繁提交 | 每个功能点完成即提交 |
| 单次提交文件数 | < 10 个 |
| 单次提交代码行数 | < 500 行 |

### 4.3 扩展式开发

| 原则 | 说明 |
|------|------|
| 优先复用 | 先看 services 是否已有需要的能力 |
| 新增而非修改 | 优先新增函数/类，而非修改现有的 |
| 向后兼容 | 修改接口时保持向后兼容 |
| 不破坏现有功能 | 任何改动不能导致现有功能失效 |

### 4.4 文档驱动开发

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

## 五、开发流程（铁律）

### 5.1 新功能开发流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      新功能开发流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 需求分析                                                     │
│     └── 确定功能属于哪个产品                                      │
│     └── 确定需要哪些 services                                    │
│     └── 确定需要哪些 infrastructure                              │
│                                                                 │
│  2. 编写文档（memory-bank/）                                     │
│     └── prd.md - 需求文档                                       │
│     └── tech-stack.md - 技术方案                                │
│     └── implementation-plan.md - 实现计划                       │
│                                                                 │
│  3. 自底向上开发                                                 │
│     └── infrastructure（如需新增）                               │
│     └── services（如需新增或扩展）                               │
│     └── products（业务逻辑）                                     │
│                                                                 │
│  4. 测试验证                                                     │
│     └── 单元测试                                                 │
│     └── 集成测试                                                 │
│     └── 回归测试                                                 │
│                                                                 │
│  5. 提交部署                                                     │
│     └── 用户确认                                                 │
│     └── Git 提交 + Tag                                          │
│     └── 部署（如需要）                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 开发-提交-部署流程

```
本地开发 → 本地测试 → 告知用户 → 用户确认 → 提交推送 → 打tag → 部署
```

| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 1. 本地开发 | 修改代码、编写测试 | Claude |
| 2. 本地测试 | 运行测试验证功能 | Claude |
| 3. 告知用户 | 说明修改内容和测试结果 | Claude |
| 4. 用户确认 | 用户明确同意后才能继续 | 用户 |
| 5. 提交推送 | git commit + git push | Claude |
| 6. 打标签 | git tag vX.Y.Z | Claude |
| 7. 部署服务器 | 更新生产环境 | Claude |

**关键约束**：
- 禁止未经用户确认就提交代码
- 禁止未经用户确认就部署到服务器

### 5.3 版本号规范

格式：`v主版本.次版本.补丁版本`

| 版本位 | 触发条件 | 示例 |
|--------|----------|------|
| 补丁版本 | Bug 修复、小功能 | v5.3.9 → v5.3.10 |
| 次版本 | 新功能、新模块 | v5.3.10 → v5.4.0 |
| 主版本 | 重大架构变更 | v5.4.0 → v6.0.0 |

---

## 六、模块开发指南（核心）

### 6.1 按需自动创建下层模块（铁律）

**当用户要求开发产品层功能时，Claude 必须自动分析并按需创建/扩展服务层和基础设施层。**

用户只会说"开发一个物流通知产品"，不会说"先创建一个邮件服务"。Claude 必须：

1. **自动分析** 产品需要哪些服务和基础设施
2. **自动创建** 不存在的服务模块和基础设施模块
3. **自动扩展** 已有模块缺失的功能
4. **自底向上** 按正确顺序开发

```
用户说："开发物流异常监控功能"

Claude 自动执行：
1. 分析：需要 scheduler（定时任务）、email（邮件发送）、shopify（订单查询）
2. 检查：scheduler 待完善，email 已有，shopify 已有
3. 先完善 infrastructure/scheduler
4. 再开发 products/notification 的异常监控功能
5. 最后测试验证
```

### 6.2 接收需求时的分析步骤

当用户提出需求时，Claude 必须：

```
1. 分析需求属于哪个产品（products/xxx）
2. 列出需要的 services（已有 or 新建 or 扩展）
3. 列出需要的 infrastructure（已有 or 新建 or 扩展）
4. 制定开发计划（自底向上，包含所有层的改动）
5. 让用户确认后再开始
```

### 6.3 分析模板

```
用户需求：[需求描述]

【分析结果】

1. 产品归属：products/[产品名]

2. 需要的服务层：
   - services/shopify ✓ 已有，无需改动
   - services/email ✓ 已有，需扩展（添加模板功能）
   - services/xxx ✗ 需新建

3. 需要的基础设施：
   - infrastructure/database ✓ 已有，无需改动
   - infrastructure/scheduler ✗ 需完善（添加 Cron 支持）

4. 开发计划（自底向上）：
   Step 1: 完善 infrastructure/scheduler - 添加 Cron 支持
   Step 2: 扩展 services/email - 添加邮件模板功能
   Step 3: 新建 services/xxx - [功能描述]
   Step 4: 开发 products/xxx - 业务逻辑
   Step 5: 测试验证

是否确认执行？
```

### 6.4 新模块创建清单

创建新模块时必须包含：

```
products/xxx/ 或 services/xxx/ 或 infrastructure/xxx/
├── __init__.py                 # 模块初始化
├── README.md                   # 模块规范（必须）
├── memory-bank/                # 文档（products 必须，其他可选）
│   ├── prd.md
│   ├── tech-stack.md
│   ├── implementation-plan.md
│   ├── progress.md
│   └── architecture.md
└── tests/                      # 测试（推荐）
```

### 6.5 新模块开发后同步更新顶层文档（铁律）

**每当创建新模块或对现有模块进行重大改动后，Claude 必须同步更新以下顶层文档：**

| 触发条件 | 需要更新的文档 | 更新内容 |
|----------|----------------|----------|
| 创建新 product | PROJECT_OVERVIEW.md | 产品清单、目录结构 |
| 创建新 service | PROJECT_OVERVIEW.md | 服务清单、目录结构 |
| 创建新 infrastructure | PROJECT_OVERVIEW.md | 基础设施清单、目录结构 |
| 模块状态变更（开发中→已完成） | PROJECT_OVERVIEW.md | 更新状态列 |
| 架构重大调整 | CLAUDE.md + PROJECT_OVERVIEW.md | 架构图、规则等 |

**更新流程**：
```
开发完成 → 更新模块 README.md → 更新 PROJECT_OVERVIEW.md → 提交
```

**示例**：开发完 notification 模块后
1. 更新 products/notification/README.md 的状态：规划中 → 已完成
2. 更新 PROJECT_OVERVIEW.md 的产品清单：状态列改为"已完成"
3. 一并提交

---

## 七、模块启用控制

### 7.1 环境变量控制

```python
# .env
ENABLE_AI_CHATBOT=true        # AI 客服
ENABLE_AGENT_WORKBENCH=true   # 坐席工作台
ENABLE_NOTIFICATION=false     # 物流通知（开发中）
```

### 7.2 backend.py 条件注册

```python
# backend.py
if config.ENABLE_AI_CHATBOT:
    from products.ai_chatbot.routes import router as ai_chatbot_router
    app.include_router(ai_chatbot_router)

if config.ENABLE_NOTIFICATION:
    from products.notification.routes import router as notification_router
    app.include_router(notification_router)
```

---

## 八、生产服务器配置

| 配置项 | 值 |
|--------|-----|
| 服务器地址 | 8.211.27.199 |
| 项目目录 | /opt/fiido-ai-service/ |
| 前端部署 | /var/www/fiido-frontend/ |
| 后端服务 | fiido-ai-backend |
| 用户端地址 | https://ai.fiido.com/chat-test/ |

### 快速部署命令

```bash
# 完整部署（后端+前端）
ssh root@8.211.27.199 'cd /opt/fiido-ai-service && git pull && \
  systemctl restart fiido-ai-backend && \
  cd frontend && npm run build && \
  rm -rf /var/www/fiido-frontend/* && \
  cp -r dist/* /var/www/fiido-frontend/'
```

---

## 九、禁止事项（铁律）

### 9.1 架构禁止

- 禁止下层依赖上层（services 不能 import products）
- 禁止产品层横向依赖（ai_chatbot 不能 import agent_workbench）
- 禁止绕过服务层直接操作底层（products 不能直接操作 Redis，需通过 services）

### 9.2 开发禁止

- 禁止未经用户确认就提交代码
- 禁止未经用户确认就部署到服务器
- 禁止跳过测试就提交代码
- 禁止一次改动太多文件（>10 个）
- 禁止修改破坏现有功能

### 9.3 代码禁止

- 禁止修改 .env 中的核心凭证
- 禁止在代码中硬编码密钥
- 禁止删除现有的测试用例

---

## 十、必读文档

| 类型 | 路径 |
|------|------|
| 架构总览 | PROJECT_OVERVIEW.md |
| 产品层规范 | products/README.md |
| 服务层规范 | services/README.md |
| 基础设施规范 | infrastructure/README.md |
| 开发参考手册 | docs/开发参考手册.md |
| 架构对比分析 | docs/架构对比分析.md |

---

## 十一、文档更新记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v3.1 | 2025-12-18 | 更新目录结构反映实际情况（backend.py、src兼容层等） |
| v3.0 | 2025-12-18 | 重构为三层架构规范，添加依赖规则、开发指南 |
| v2.2 | 2025-12-16 | 原 AI 客服开发指令（已迁移到模块级别） |
