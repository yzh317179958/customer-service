# Skills 使用指南

> 本项目在 `.claude/skills/` 下定义了 5 个开发指导技能，Claude 会根据关键词自动激活。
>
> **最后更新**：2025-12-21

---

## 快速参考

| Skill                  | 触发场景             | 示例指令                                          |
| ---------------------- | -------------------- | ------------------------------------------------- |
| `memory-bank-guide`    | 创建新模块、生成文档 | "创建新产品"、"生成 memory-bank 文档"、"补齐文档" |
| `vibe-coding-workflow` | 分步开发、执行计划   | "开始 Step 1"、"继续开发"、"执行下一步"           |
| `fiido-architecture`   | 开发新功能、检查依赖 | "开发新功能"、"检查架构依赖"、"创建新模块"        |
| `git-commit-helper`    | 提交代码             | "提交代码"、"git commit"                          |
| `deploy-guide`         | 部署上线             | "部署到服务器"、"上线"                            |

---

## 使用方式

### 方式一：使用触发关键词（自动激活）

直接在对话中使用上表的示例指令，Claude 会自动读取对应 skill。

### 方式二：明确指定 skill 名称

```
按照 memory-bank-guide 生成文档
使用 vibe-coding-workflow 开发 Step 3
检查是否符合 fiido-architecture 规范
```

### 方式三：强制读取

```
先读取 skills 再执行
按照 skills 规范来
```

---

## 各 Skill 详细说明

### 1. memory-bank-guide

**用途**：生成模块的 5 个标准文档（prd/tech-stack/implementation-plan/progress/architecture）

**触发词**：创建新产品、生成 memory-bank、补齐文档、初始化新模块

**核心流程**：
1. **询问用户产品需求**（必做）- 获取产品/功能描述
2. 生成 `prd.md` - 产品需求文档
3. 生成 `tech-stack.md` - 技术栈说明（符合生产环境和企业级要求）
4. 生成 `implementation-plan.md` - 分步实现计划
5. 创建 `progress.md` + `architecture.md` - 空白追踪文件

**关键约束**：
- 遵循 `CLAUDE.md` 三层架构规则
- 技术栈推荐需考虑：高并发、容错、可维护性、安全性

### 2. vibe-coding-workflow

**用途**：按实现计划分步开发，每步测试→更新文档→提交

**触发词**：开始 Step X、继续开发、执行下一步、按照实现计划开发

**开始前必读文档**：
- `CLAUDE.md` - 最高开发规范
- `PROJECT_OVERVIEW.md` - 项目架构概览
- `memory-bank/*.md` - 模块文档

**核心流程**：
```
阅读文档 → 执行 Step N → 测试验证 → 更新 progress.md + architecture.md → Git commit
```

**文档更新时机**：
| 文档 | 更新时机 |
|------|----------|
| progress.md | 每个 Step 完成后 |
| architecture.md | 新增/修改文件后 |
| PROJECT_OVERVIEW.md | 新增/完成模块时 |
| CLAUDE.md | 架构规则变更时 |

### 3. fiido-architecture

**用途**：检查三层架构依赖规则，分析新功能归属

**触发词**：开发新功能、修改代码、创建新模块

**依赖规则**：
```
products/ → services/ → infrastructure/（单向依赖）
products 之间禁止互相依赖
```

**生产环境架构考量**：
- 服务边界清晰
- 水平扩展能力
- 故障隔离
- 可观测性
- 配置外置

### 4. git-commit-helper

**用途**：规范化 git 提交流程

**触发词**：提交代码、git commit

**版本号规则**：
| 版本位 | 触发条件 |
|--------|----------|
| 补丁版本 | Bug 修复、小功能 |
| 次版本 | 新功能、新模块 |
| 主版本 | 重大架构变更 |

**commit 格式**：
```
类型: Step N - 描述 vX.X.X

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 5. deploy-guide

**用途**：部署到生产服务器

**触发词**：部署、上线、发布

**服务器配置**：
| 配置项 | 值 |
|--------|-----|
| 服务器地址 | 8.211.27.199 |
| 项目目录 | /opt/fiido-ai-service/ |
| 前端部署 | /var/www/fiido-frontend/ |

**部署前检查清单**：
- 本地测试通过
- 代码已提交并推送
- 版本号已更新
- 文档已更新

---

## 相关文档

| 文档 | 说明 |
|------|------|
| CLAUDE.md | 最高开发规范 |
| PROJECT_OVERVIEW.md | 项目架构概览 |
| Vibe_Coding开发规范流程说明.md | Vibe Coding 方法论 |
