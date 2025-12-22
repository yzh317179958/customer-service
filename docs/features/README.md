# 跨模块功能文档目录

> **目录性质**：跨模块功能的主文档存放处
> **维护规范**：遵循主从模式，主文档在此，各模块保留引用

---

## 目录结构

```
docs/features/
├── README.md                    # 本文件
├── _templates/                  # 模板文件
│   ├── prd.md                  # 产品需求文档模板
│   ├── implementation-plan.md  # 实现计划模板
│   ├── progress.md             # 进度追踪模板
│   └── architecture.md         # 架构说明模板
│
└── [功能名称]/                  # 具体功能文档
    ├── prd.md                  # 产品需求
    ├── implementation-plan.md  # 分步实现计划
    ├── progress.md             # 进度追踪
    └── architecture.md         # 架构说明
```

---

## 主从模式说明

跨模块功能采用 **主从模式** 管理文档：

| 位置 | 内容 | 职责 |
|------|------|------|
| `docs/features/[功能名]/` | 主文档 | 完整的需求、计划、进度、架构 |
| `products/xxx/memory-bank/cross-module-refs.md` | 引用文档 | 记录本模块参与的跨模块功能引用 |

### 主文档（Main）

存放在 `docs/features/[功能名]/`，包含：
- 完整的产品需求（涵盖所有模块）
- 完整的实现计划（按模块拆分步骤）
- 统一的进度追踪
- 整体架构说明

### 从文档（Reference）

存放在各模块的 `memory-bank/cross-module-refs.md`，记录：
- 本模块参与了哪些跨模块功能
- 每个功能中本模块的职责
- 指向主文档的链接

---

## 使用流程

### 1. 新建跨模块功能

```bash
# 创建功能目录
mkdir -p docs/features/[功能名]

# 复制模板
cp docs/features/_templates/*.md docs/features/[功能名]/
```

### 2. 编写主文档

按顺序完成：
1. `prd.md` - 产品需求（包含所有涉及模块的需求）
2. `implementation-plan.md` - 实现计划（按模块拆分步骤）
3. `progress.md` - 初始化进度追踪
4. `architecture.md` - 初始化架构说明

### 3. 更新模块引用

在每个涉及模块的 `memory-bank/cross-module-refs.md` 添加引用：

```markdown
## [功能名称]

**主文档**: `docs/features/[功能名]/`
**本模块职责**: [描述本模块在该功能中的职责]
**涉及文件**:
- file1.py
- file2.tsx
```

### 4. 按步骤开发

严格遵循 Vibe Coding 工作流：
1. 阅读主文档 → 执行 Step N
2. 测试验证
3. 更新 `progress.md` + `architecture.md`
4. Git commit + tag
5. 继续下一步

---

## 功能清单

| 功能名称 | 路径 | 状态 | 涉及模块 | 说明 |
|---------|------|------|----------|------|
| 微服务 SSE 通信 | `microservice-sse-communication/` | ⏳ 开发中 | ai_chatbot, agent_workbench, infrastructure | Redis Pub/Sub 跨进程实时通信 |

---

## 模板使用指南

| 模板 | 用途 | 何时创建 |
|------|------|----------|
| `prd.md` | 产品需求文档 | 开始前 |
| `implementation-plan.md` | 分步实现计划 | 需求确认后 |
| `progress.md` | 进度追踪 | 开始开发时 |
| `architecture.md` | 架构说明 | 随开发逐步完善 |

---

## 相关文档

- [Vibe Coding 开发规范](../参考资料/Vibe_Coding开发规范流程说明.md)
- [CLAUDE.md 开发规范](../../CLAUDE.md)
- [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md)
