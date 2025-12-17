# Fiido 智能客服系统 - Claude 开发指令

## 项目概述

基于 Coze API 的智能客服系统，包含用户端、坐席工作台和后端服务。

---

## 铁律 0: 开发-提交-部署流程（最高优先级）

**强制要求**：所有代码修改必须严格遵守以下流程，禁止跳过任何步骤。

### 完整工作流程

```
本地开发 → 本地测试 → 告知用户 → 用户确认 → 提交推送 → 打tag → 部署服务器
```

| 阶段 | 操作 | 执行者 |
|-----|------|-------|
| 1. 本地开发 | 修改代码、编写测试 | Claude |
| 2. 本地测试 | 运行测试验证功能 | Claude |
| 3. 告知用户 | 说明修改内容和测试结果 | Claude |
| 4. 用户确认 | 用户明确同意后才能继续 | 用户 |
| 5. 提交推送 | `git commit` + `git push` | Claude |
| 6. 打标签 | `git tag vX.Y.Z` + 推送tag | Claude |
| 7. 部署服务器 | 更新生产环境 | Claude |

**关键约束**：
- ❌ **禁止** 未经用户确认就提交代码
- ❌ **禁止** 未经用户确认就部署到服务器
- ✅ 开发完成后，必须先告知用户修改内容和测试结果
- ✅ 等待用户明确说"提交"、"推送"、"部署"等确认词后才能执行

### 版本号规范

**格式**: `v主版本.次版本.补丁版本`（如 v5.3.9）

| 版本位 | 触发条件 | 示例 |
|-------|---------|------|
| 补丁版本（第三位） | 日常功能开发、Bug修复 | v5.3.9 → v5.3.10 |
| 次版本（第二位） | 用户明确要求"大版本更新" | v5.3.10 → v5.4.0 |
| 主版本（第一位） | 重大架构变更（极少使用） | v5.4.0 → v6.0.0 |

---

## 生产服务器配置

> 📚 详细配置参见 [`docs/开发参考手册.md`](docs/开发参考手册.md) 第一、二章

| 配置项 | 值 |
|-------|-----|
| 服务器地址 | `8.211.27.199` |
| 登录密码 | `Tr&gbt85A>9a@HhuO|g,tov%fN6#Z` |
| 项目目录 | `/opt/fiido-ai-service/` |
| 前端部署 | `/var/www/fiido-frontend/` |
| 后端服务 | `fiido-ai-backend` |
| 用户端地址 | https://ai.fiido.com/chat-test/ |

### 快速部署命令

```bash
# 完整部署（后端+前端）
sshpass -p 'Tr&gbt85A>9a@HhuO|g,tov%fN6#Z' ssh root@8.211.27.199 \
  'cd /opt/fiido-ai-service && git pull && systemctl restart fiido-ai-backend && \
   cd frontend && npm run build && rm -rf /var/www/fiido-frontend/* && cp -r dist/* /var/www/fiido-frontend/'
```

---

## 核心铁律

> 📚 详细规范参见 [`docs/开发参考手册.md`](docs/开发参考手册.md) 第三章 Coze API 调用规范

### 铁律 1: 不可修改的核心接口

```
🔴 严禁修改核心逻辑:
- POST /api/chat              (同步AI对话)
- POST /api/chat/stream       (流式AI对话)
- POST /api/conversation/new  (创建会话)
```

**允许**: 前置检查、后置处理 | **禁止**: 修改 Coze API 调用方式、返回结构

### 铁律 2: Coze API 调用规范

```python
# ✅ 必须使用 SSE 流式响应
with http_client.stream('POST', url, json=payload, headers=headers) as response:
    for line in response.iter_lines():
        # 解析SSE流

# ✅ 必需的请求参数
payload = {
    "workflow_id": WORKFLOW_ID,
    "app_id": APP_ID,
    "session_name": session_id,  # 必需 - 会话隔离
    "additional_messages": [...],
}
```

### 铁律 3: 会话隔离机制

- ✅ 首次对话不传 `conversation_id`，由 Coze 自动生成
- ✅ 后续对话传入相同的 `conversation_id` 维持上下文
- ❌ 禁止手动生成 `conversation_id`

### 铁律 4: 状态机约束

```
bot_active → pending_manual → manual_live → bot_active
```

人工接管期间**必须阻止 AI 对话**（返回 409）

---

## 开发流程规范

> 📚 详细规范参见 [`docs/开发参考手册.md`](docs/开发参考手册.md) 第四章 开发流程详细规范

### 增量开发原则

| 约束 | 要求 |
|-----|------|
| 单次提交文件数 | < 5 个 |
| 单次提交代码行数 | < 500 行 |
| 提交频率 | 每功能完成即提交 |

### 开发检查清单

- [ ] 本地测试通过
- [ ] 回归测试通过 (`./tests/regression_test.sh`)
- [ ] 告知用户修改内容
- [ ] 用户确认后提交推送
- [ ] 打版本 tag
- [ ] 部署到服务器

---

## 本地开发环境

### 启动服务

```bash
# 后端 (http://localhost:8000)
python3 backend.py

# 用户端 (http://localhost:5173)
cd frontend && npm run dev

# 坐席工作台 (http://localhost:5174)
cd agent-workbench && npm run dev
```

### 端口规范

| 服务 | 端口 |
|------|------|
| 后端 API | 8000 |
| 用户端 | 5173 |
| 坐席工作台 | 5174 |

---

## 项目结构

```
/home/yzh/AI客服/鉴权/
├── backend.py              # 后端主服务
├── src/                    # 后端模块
├── frontend/               # 用户端 Vue 项目
├── agent-workbench/        # 坐席工作台 Vue 项目
├── prd/                    # PRD 文档
├── tests/                  # 测试脚本
└── prompts/                # AI 提示词模板
```

---

## 禁止事项

1. **不要** 未经用户确认就提交/推送/部署代码
2. **不要** 修改 `.env` 中的 Coze 凭证
3. **不要** 修改 Coze API 的调用方式和返回解析
4. **不要** 绕过 token_manager 直接生成 Token
5. **不要** 使用 WebSocket 替换 SSE 流式响应
6. **不要** 跳过回归测试就提交代码
7. **不要** 在人工接管期间允许 AI 对话
8. **不要** 手动生成 conversation_id

---

## 必读文档

| 类型 | 文档路径 |
|-----|---------|
| **开发参考手册** | [`docs/开发参考手册.md`](docs/开发参考手册.md) - 服务器配置、部署、Coze API、性能要求 |
| 商品状态逻辑 | [`docs/商品状态判断逻辑.md`](docs/商品状态判断逻辑.md) |
| 核心约束 | `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md` |
| 技术方案 | `prd/03_技术方案/TECHNICAL_SOLUTION_v1.0.md` |
| API 契约 | `prd/03_技术方案/api_contract.md` |
| Coze 规范 | `prd/02_约束与原则/coze.md` |

---

## 环境变量 (.env)

关键配置：`COZE_WORKFLOW_ID`, `COZE_APP_ID`, `COZE_OAUTH_CLIENT_ID`, `JWT_SECRET_KEY`

---

**文档版本**: v2.2
**最后更新**: 2025-12-16
