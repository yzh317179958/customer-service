# Fiido 智能服务平台 - 最高开发规范

> **文档性质**：最高法案，所有开发必须遵守
> **文档版本**：v5.5
> **最后更新**：2025-12-22

---

## 一、项目定位

Fiido 智能服务平台是面向跨境电商的一站式 AI 解决方案，采用三层架构设计，支持多产品独立开发与部署。

**支持两种启动模式**：
- **全家桶模式**：`uvicorn backend:app` 启动所有产品
- **独立模式**：每个产品独立启动，如 `uvicorn products.ai_chatbot.main:app`

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
│   ├── ai_chatbot/             # AI 智能客服（含 frontend/ 前端）
│   ├── agent_workbench/        # 坐席工作台（含 frontend/ 前端）
│   ├── customer_portal/        # 客户控制台（规划中）
│   └── notification/           # 物流通知
│
├── services/                    # 【服务层】
│   ├── README.md               # 服务层规范
│   ├── bootstrap/              # 依赖注入注册（将服务实现注册到基础设施层）
│   ├── shopify/                # Shopify 订单服务
│   ├── email/                  # 邮件服务
│   ├── coze/                   # Coze AI 服务
│   ├── ticket/                 # 工单服务
│   ├── session/                # 会话服务
│   ├── asset/                  # 素材服务（含 data/ 素材数据、tools/ 工具脚本）
│   └── billing/                # 计费服务（规划中）
│
├── infrastructure/              # 【基础设施层】
│   ├── README.md               # 基础设施规范
│   ├── bootstrap/              # 启动引导（组件工厂、依赖注入）
│   ├── database/               # 数据库（PostgreSQL + Redis 双写）
│   │   ├── models/            # ORM 模型（9 个表）
│   │   ├── migrations/        # Alembic 数据库迁移
│   │   ├── converters.py      # Pydantic ↔ ORM 转换器
│   │   └── connection.py      # 连接池管理
│   ├── scheduler/              # 定时任务
│   ├── logging/                # 日志系统
│   ├── monitoring/             # 监控告警
│   └── security/               # 安全认证（JWT、坐席认证）
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
| 数据库 | 通过 PostgreSQL/Redis 共享数据 | ai_chatbot 写入工单，agent_workbench 读取 |
| API 调用 | 通过 HTTP API 通信 | 一个产品调用另一个产品的 API |
| 事件机制 | 发布/订阅事件 | ai_chatbot 发布事件，notification 订阅 |

### 3.4 数据库双写策略

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

**支持双写的服务：**
- `services/ticket/store.py` - 工单存储
- `services/ticket/audit.py` - 审计日志
- `services/session/archive.py` - 会话归档
- `services/email/service.py` - 邮件记录
- `infrastructure/security/agent_auth.py` - 坐席管理

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

### 5.1 宏观开发阶段

新功能开发分为以下阶段：

```
┌─────────────────────────────────────────────────────────────────┐
│                      宏观开发阶段                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  阶段一：需求分析                                                │
│     └── 确定功能属于哪个产品（products/xxx）                     │
│     └── 确定需要哪些 services（已有/新建/扩展）                  │
│     └── 确定需要哪些 infrastructure（已有/新建/扩展）            │
│                                                                 │
│  阶段二：文档驱动（memory-bank/）                                │
│     └── prd.md - 产品需求文档                                   │
│     └── tech-stack.md - 技术栈说明                              │
│     └── implementation-plan.md - 分步实现计划                   │
│     └── progress.md - 进度追踪（初始为空）                       │
│     └── architecture.md - 架构说明（初始为空）                   │
│                                                                 │
│  阶段三：按步骤开发（详见 5.3 Vibe Coding 工作流）               │
│     └── 自底向上：infrastructure → services → products          │
│     └── 每步执行 → 测试 → 文档更新 → Git 提交                   │
│                                                                 │
│  阶段四：完成与部署                                              │
│     └── 所有步骤完成                                            │
│     └── 回归测试通过                                            │
│     └── 用户确认后部署                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**关键约束**：
- 禁止未经用户确认就提交代码
- 禁止未经用户确认就部署到服务器

### 5.2 版本号规范

格式：`v主版本.次版本.补丁版本`

| 版本位 | 触发条件 | 示例 |
|--------|----------|------|
| 补丁版本 | Bug 修复、小功能 | v5.3.9 → v5.3.10 |
| 次版本 | 新功能、新模块 | v5.3.10 → v5.4.0 |
| 主版本 | 重大架构变更 | v5.4.0 → v6.0.0 |

### 5.3 Vibe Coding 开发工作流（铁律）

> **核心理念**："规划就是一切。不要让 AI 自主规划，否则你的代码库会变成一团乱麻。"

基于 Vibe Coding 方法论，Claude 在执行任何子项目/模块开发时，必须严格遵循以下工作流：

#### 5.3.1 开始前：确认计划清晰

**在开始编码前，Claude 必须先阅读并确认理解 memory-bank/ 中的文档：**

```
1. 阅读 memory-bank/ 中的所有文档：
   - prd.md（产品需求）
   - tech-stack.md（技术栈）
   - implementation-plan.md（实现计划）
   - progress.md（进度追踪）
   - architecture.md（架构说明）

2. 如果 implementation-plan.md 不够清晰，必须向用户提问澄清
3. 确认理解后，更新 implementation-plan.md 使其 100% 清晰
```

#### 5.3.2 执行单个步骤

**每次只执行一个步骤，测试通过后再继续：**

```
执行步骤的标准流程：

1. 阅读 memory-bank/ 中的所有文档
2. 查看 progress.md 了解之前完成的工作
3. 执行实现计划的 Step [N]
4. 只做当前步骤要求的内容，不要超前
5. 如果有疑问，先问用户
6. 告知用户如何测试
7. 等待测试结果，测试通过前不开始下一步
```

#### 5.3.3 测试验证

**按照 implementation-plan.md 中的测试方法验证：**

| 测试结果 | Claude 操作 |
|----------|-------------|
| 测试通过 | 更新 progress.md + architecture.md，告知可继续下一步 |
| 测试失败 | 分析错误原因并修复，不继续下一步 |

**测试通过后必须执行：**
1. 更新 `memory-bank/progress.md`，记录 Step [N] 完成内容
2. 更新 `memory-bank/architecture.md`，说明新增/修改的文件用途
3. 告知用户可以继续 Step [N+1]

#### 5.3.4 Git 提交

**每个步骤完成后立即提交：**

```bash
# 1. 查看改动
git status && git diff

# 2. 添加文件
git add .

# 3. 提交（包含步骤信息）
git commit -m "feat: Step N - 步骤描述 vX.X.X"

# 4. 打标签
git tag vX.X.X

# 5. 推送（等用户确认后）
git push origin main --tags
```

#### 5.3.5 完整工作流循环

```
┌─────────────────────────────────────────────────────────┐
│  1. 阅读文档 → 执行 Step N                               │
│         ↓                                               │
│  2. 测试验证                                            │
│         ↓                                               │
│  3. 通过? ─── 否 ──→ 修复 ──→ 返回步骤 2                 │
│         │                                               │
│        是                                               │
│         ↓                                               │
│  4. 更新 progress.md + architecture.md                  │
│         ↓                                               │
│  5. Git commit + tag                                    │
│         ↓                                               │
│  6. /clear 开始新对话（可选，长对话时推荐）              │
│         ↓                                               │
│  7. 还有步骤? ─── 是 ──→ 返回步骤 1                      │
│         │                                               │
│        否                                               │
│         ↓                                               │
│  8. 功能完成！                                          │
└─────────────────────────────────────────────────────────┘
```

#### 5.3.6 问题处理

| 场景 | 处理方式 |
|------|----------|
| Bug 修复 | 分析错误原因 → 修复 → 重新测试 → 不继续下一步 |
| 代码回滚 | 使用 `/rewind` 或 `git reset --hard HEAD~1` |
| 卡住时 | 向用户说明尝试过的方法、当前状态，请求帮助分析 |

#### 5.3.7 文档更新模板

**progress.md 每步完成后追加：**

```markdown
---

## Step [N]: [步骤标题]

**完成时间:** YYYY-MM-DD HH:MM
**版本号:** vX.X.X

**完成内容:**
- [具体做了什么]
- [创建/修改了哪些文件]

**测试结果:**
- ✅ [测试项1] 通过
- ✅ [测试项2] 通过

**备注:**
- [遇到的问题及解决方案]
```

**architecture.md 每新增文件后追加：**

```markdown
---

## [文件路径]

**用途:** [这个文件做什么]

**主要函数/组件:**
- `functionName()` - 功能描述

**依赖关系:**
- 依赖: [依赖哪些文件]
- 被依赖: [被哪些文件使用]
```

#### 5.3.8 检查清单

**每个步骤完成后的检查：**

- [ ] 测试验证通过
- [ ] 更新 `progress.md`
- [ ] 更新 `architecture.md`
- [ ] Git commit
- [ ] Git tag
- [ ] 告知用户可继续下一步

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

### 6.5 跨模块功能开发（铁律）

**当需求涉及多个模块时（如 ai_chatbot 和 agent_workbench），必须使用跨模块开发工作流。**

#### 6.5.1 主从文档模式

跨模块功能采用「主从模式」管理文档：

| 位置 | 内容 | 职责 |
|------|------|------|
| `docs/features/[功能名]/` | 主文档 | 完整的需求、计划、进度、架构 |
| `products/xxx/memory-bank/cross-module-refs.md` | 引用文档 | 记录本模块参与的跨模块功能 |

#### 6.5.2 跨模块开发流程

```
1. 需求分析：确定涉及哪些模块
2. 创建主文档：docs/features/[功能名]/
   - prd.md（完整需求）
   - implementation-plan.md（分步计划）
   - progress.md（进度追踪）
   - architecture.md（架构说明）
3. 更新模块引用：各模块 memory-bank/cross-module-refs.md
4. 按步骤开发：自底向上，每步更新主文档和模块引用
5. 集成测试：验证完整流程
```

#### 6.5.3 相关资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 跨模块文档目录 | `docs/features/` | 存放跨模块功能的主文档 |
| 文档模板 | `docs/features/_templates/` | prd/plan/progress/architecture 模板 |
| 跨模块文档生成 | `.claude/skills/cross-module-docs-guide/SKILL.md` | 生成跨模块功能文档（类似 memory-bank-guide） |
| 跨模块开发工作流 | `.claude/skills/cross-module-workflow/SKILL.md` | 按步骤执行跨模块开发（类似 vibe-coding-workflow） |

**两个技能的分工：**

| 技能 | 职责 | 触发词 |
|------|------|--------|
| cross-module-docs-guide | 生成 docs/features/ 文档，更新模块引用 | "创建跨模块文档"、"生成跨模块需求" |
| cross-module-workflow | 按步骤开发，更新进度和架构 | "开始跨模块 Step"、"跨模块继续开发" |

---

### 6.6 新模块开发后同步更新顶层文档（铁律）

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
  cd products/ai_chatbot/frontend && npm run build && \
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
| Vibe Coding 开发规范 | docs/参考资料/Vibe_Coding开发规范流程说明.md |
| 跨模块功能文档 | docs/features/README.md |
| 跨模块文档生成技能 | .claude/skills/cross-module-docs-guide/SKILL.md |
| 跨模块开发工作流技能 | .claude/skills/cross-module-workflow/SKILL.md |

---

## 十一、文档更新记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v5.5 | 2025-12-22 | 拆分跨模块开发技能：cross-module-docs-guide（文档生成）+ cross-module-workflow（开发执行），更新 6.5.3 相关资源 |
| v5.4 | 2025-12-22 | 新增跨模块开发工作流（6.5 节），创建 docs/features/ 文档结构和 cross-module-workflow 技能 |
| v5.3 | 2025-12-22 | 新增 PostgreSQL 数据库模块，添加双写策略说明，更新目录结构 |
| v5.2 | 2025-12-21 | 同步目录结构：新增 customer_portal、billing、services/bootstrap；移除 prompts/；明确 agent_workbench 含前端 |
| v5.1 | 2025-12-19 | 清理遗留目录：删除 prompts/、assets/、data/、attachments/，素材数据迁移至 services/asset/data/ |
| v5.0 | 2025-12-19 | 前端移至 products/ai_chatbot/frontend/，脚本归入 deploy/scripts/，素材工具归入 services/asset/tools/ |
