# Claude Skills 使用指南

> **写给**：纯小白用户
> **目的**：教你如何使用已创建的 7 个 Skills

---

## 一、什么是 Skills？（30 秒理解）

**没有 Skills**：
```
你：帮我开发一个功能
Claude：好的...(可能不遵守你的规范)
你：不对，要先看 CLAUDE.md 规则
Claude：好的...
你：还要看 memory-bank...
(每次都要提醒，很烦)
```

**有 Skills 后**：
```
你：帮我开发一个功能
Claude：(自动识别需要用架构规范)
       (自动遵守规则)
       好的，根据三层架构，这个功能应该放在 products/...
```

**一句话**：Skills = 教 Claude 自动遵守你的规范

---

## 二、已创建的 7 个 Skills

### 单模块开发

| Skill | 作用 | 触发词 |
|-------|------|--------|
| fiido-architecture | 守护三层架构 | "开发功能"、"修改代码" |
| memory-bank-guide | 生成单模块文档 | "创建新产品"、"补齐文档"、"生成 memory-bank" |
| vibe-coding-workflow | 分步开发流程 | "开始 Step"、"继续开发" |

### 跨模块开发

| Skill | 作用 | 触发词 |
|-------|------|--------|
| cross-module-docs-guide | 生成/更新跨模块文档 | "创建跨模块文档"、"扩展跨模块功能"、"跨模块 Phase 2" |
| cross-module-workflow | 跨模块开发流程 | "开始跨模块 Step"、"跨模块继续开发" |

### 通用工具

| Skill | 作用 | 触发词 |
|-------|------|--------|
| git-commit-helper | 规范 Git 提交 | "帮我提交"、"commit" |
| deploy-guide | 部署到服务器 | "部署"、"上线"、"发布" |

---

## 三、如何让 Skills 生效？

### Step 1：退出当前对话

```bash
# 按 Ctrl+C 或输入
/exit
```

### Step 2：重新启动 Claude Code

```bash
cd /home/yzh/AI客服/鉴权
claude
```

### Step 3：测试是否生效

说这句话测试：
```
你：帮我分析一下开发一个邮件通知功能应该怎么做
```

如果 Claude 回复包含"三层架构"、"products/notification"、"services/email"等关键词，说明 Skill 生效了。

---

## 四、日常使用场景

### 场景 1：开发新功能

```
你：我要开发一个物流异常监控功能

Claude（自动使用 fiido-architecture）：
好的，让我分析这个需求...

【分析结果】
1. 产品归属：products/notification
2. 需要的服务：
   - services/shopify ✓ 已有
   - services/email ✓ 已有
3. 开发计划（自底向上）：
   Step 1: 创建 products/notification 结构
   Step 2: 实现监控逻辑
   Step 3: 集成邮件通知
   Step 4: 测试验证

是否确认执行？
```

### 场景 2：按步骤开发

```
你：开始 Step 1

Claude（自动使用 vibe-coding-workflow）：
好的，让我读取 implementation-plan.md...

Step 1 的任务是：创建 notification 模块基础结构

我现在开始执行：
1. 创建目录 products/notification/
2. 创建 __init__.py、main.py、routes.py
3. 创建 memory-bank/ 文档

完成后请测试：
- 运行 `python -c "from products.notification import *"`
- 应该无报错

测试通过后告诉我，我会更新文档。
```

### 场景 3：创建新模块

```
你：帮我创建 products/customer_portal 的 memory-bank 文档

Claude（自动使用 memory-bank-guide）：
好的，我来生成标准的 memory-bank 文档框架...

已创建 5 个文件：
- prd.md（产品需求）
- tech-stack.md（技术栈）
- implementation-plan.md（实现计划）
- progress.md（进度追踪）
- architecture.md（架构说明）

请检查并补充具体内容。
```

### 场景 4：提交代码

```
你：帮我提交这次改动

Claude（自动使用 git-commit-helper）：
好的，让我检查改动...

【提交前检查】
✅ 修改文件数：6 个（< 10）
✅ 新增代码行：180 行（< 500）
⚠️ 请确认测试已通过

建议版本号：v7.6.0（新功能）

建议 commit 消息：
---
feat: Step 3 - 物流异常监控 v7.6.0

实现物流状态检测和邮件告警功能

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
---

确认提交？
```

### 场景 5：部署上线

```
你：部署到生产服务器

Claude（自动使用 deploy-guide）：
好的，开始部署检查...

【部署前检查清单】
✅ 本地测试通过
✅ 代码已推送到 Git
✅ 版本号：v7.6.0
⚠️ 请确认已通知相关人员

部署方式选择：
1. 仅后端
2. 仅前端
3. 完整部署（后端+前端）

你选哪个？

---

你：完整部署

Claude：执行完整部署命令...

ssh root@8.211.27.199 'cd /opt/fiido-ai-service && git pull && \
  systemctl restart fiido-ai-backend && \
  cd products/ai_chatbot/frontend && npm run build && \
  rm -rf /var/www/fiido-frontend/* && \
  cp -r dist/* /var/www/fiido-frontend/'

部署完成后请验证：
1. 检查 https://ai.fiido.com/api/health
2. 访问 https://ai.fiido.com/chat-test/

验证通过？
```

---

## 五、如果 Skill 没有自动触发

### 方法 1：手动提醒

```
你：请使用 fiido-architecture skill 来分析这个需求
```

### 方法 2：使用明确的触发词

| Skill | 有效触发词 |
|-------|-----------|
| fiido-architecture | "分析架构"、"检查依赖"、"开发功能" |
| memory-bank-guide | "创建文档"、"生成 memory-bank"、"补齐文档"、"新增需求"、"扩展功能" |
| vibe-coding-workflow | "开始 Step"、"执行步骤"、"继续开发" |
| cross-module-docs-guide | "创建跨模块文档"、"扩展跨模块功能"、"新增跨模块需求"、"跨模块 Phase 2" |
| cross-module-workflow | "开始跨模块 Step"、"跨模块继续开发"、"执行跨模块下一步" |
| git-commit-helper | "帮我提交"、"commit"、"生成提交消息" |
| deploy-guide | "部署"、"上线"、"发布到服务器" |

### 方法 3：检查 Skill 是否被识别

```
你：你能看到哪些 Skills？
```

---

## 六、常见问题

### Q1：Skills 修改后需要重启吗？

**需要**。修改 SKILL.md 后，要退出并重新启动 Claude Code。

### Q2：Skills 会自动更新吗？

**不会**。你需要手动修改 `.claude/skills/xxx/SKILL.md` 文件。

### Q3：团队成员怎么使用？

提交到 Git 后，团队成员 `git pull` 就能获得相同的 Skills。

### Q4：可以创建更多 Skills 吗？

可以。只需要：
1. 创建目录 `.claude/skills/你的skill名/`
2. 创建 `SKILL.md` 文件
3. 重启 Claude Code

---

## 七、Skills 文件位置

```
/home/yzh/AI客服/鉴权/.claude/skills/
├── fiido-architecture/SKILL.md      # 三层架构守护
├── memory-bank-guide/SKILL.md       # 单模块文档生成
├── vibe-coding-workflow/SKILL.md    # 单模块开发工作流
├── cross-module-docs-guide/SKILL.md # 跨模块文档生成
├── cross-module-workflow/SKILL.md   # 跨模块开发工作流
├── git-commit-helper/SKILL.md       # Git 提交规范
└── deploy-guide/SKILL.md            # 部署指南
```

---

## 八、下一步

1. **退出当前对话**：`/exit` 或 `Ctrl+C`
2. **重新启动**：`claude`
3. **测试单模块**：说"帮我分析开发一个新功能"
4. **测试跨模块**：说"创建跨模块文档"
5. **确认生效后提交**：`git add .claude/skills/ && git commit -m "feat: 添加 7 个 Claude Skills"`
