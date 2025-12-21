# 坐席工作台（Agent Workbench）- 分步实现计划

> **创建日期**：2025-12-19
> **最后澄清**：2025-12-21
> **预计步骤数**：20
> **核心功能步骤（P0）**：Step 1-10
> **重要功能步骤（P1）**：Step 11-16
> **扩展功能步骤（P2）**：Step 17-20

---

## 关键决策（已确认）

| 决策项 | 选择 | 说明 |
|--------|------|------|
| **前端策略** | 改造 fronted_origin | 直接在原型目录上改造，不新建 frontend/ |
| **前端框架** | React + TypeScript | 保持与原型一致 |
| **Tailwind CSS** | 改为 npm 依赖 | 移除 CDN，本地安装 tailwindcss + postcss |
| **SSE 数据源** | 复用现有队列 | 使用 `infrastructure/bootstrap/sse.py` 的全局队列 |
| **开发顺序** | 允许并行/跳步 | 后端(Step 1-2)与前端(Step 4-5)可并行 |

---

## 开发顺序说明

遵循 `CLAUDE.md` 自底向上原则：

```
（如需新增基础能力）infrastructure/ → services/ → products/ → 前端 → 测试 → 更新文档
```

**允许并行的步骤组**：
- 后端组：Step 1-2（SSE + 发消息）
- 前端组：Step 4-5（工程化 + 登录）
- 可在后端完成前先做前端骨架

本计划以"让前端原型可真实接入并可用"为目标：优先补齐 P0 后端缺口，再工程化落地前端。

---

## Step 1: 补齐会话事件 SSE（后端 P0）

**任务描述：**
新增会话级事件流端点，支持坐席端实时刷新选中会话（`manual_message`/`status_change`）。

**技术方案：**
- 复用 `infrastructure/bootstrap/sse.py` 的 `get_or_create_sse_queue(session_name)`
- 参考 `misc.py:524-557` 的 `/api/agent/events` 实现模式
- 事件类型：`manual_message`、`status_change`、`error`

**涉及文件：**
- `products/agent_workbench/handlers/sessions.py`（新增 `GET /sessions/{session_name}/events`）
- 无需修改 `infrastructure/bootstrap/sse.py`（已支持）

**测试方法：**
1. 启动后端：`uvicorn products.agent_workbench.main:app --port 8002`
2. 登录获取 token：`POST /api/agent/login`
3. 打开 SSE（示例）：
   - `curl -N -H "Authorization: Bearer <token>" http://localhost:8002/api/sessions/<session_name>/events`

**预期结果：**
- SSE 长连接建立成功
- 当会话产生 `manual_message/status_change` 时，SSE 推送对应事件 JSON

---

## Step 2: 增加"坐席发送消息"安全端点（后端 P0）

**任务描述：**
在 `agent_workbench` 提供受 `require_agent()` 保护的消息写入端点，避免直接使用 `ai_chatbot` 的未鉴权入口。

**技术方案：**
- 消息写入 `SessionState.history`（role=agent）
- 通过 `enqueue_sse_message(session_name, payload)` 推送 `manual_message` 事件
- 消息需携带 `agent_id` 和 `agent_name` 字段

**涉及文件：**
- `products/agent_workbench/handlers/sessions.py`（新增 `POST /sessions/{session_name}/messages`）
- `services/session/state.py`（仅当需要扩展字段/方法时）

**测试方法：**
1. `curl -X POST http://localhost:8002/api/sessions/<session>/messages -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"content":"hello"}'`
2. `GET /api/sessions/<session>` 校验 `history` 增加 `role=agent` 的消息
3. 若已完成 Step 1：观察 SSE 是否推送 `manual_message`

**预期结果：**
- 接口返回 200 且成功写入会话历史
- 用户端/坐席端可通过刷新或 SSE 看到新消息

---

## Step 3: CORS/代理联调准备（后端/前端 P0）

**任务描述：**
确保坐席前端开发端口可访问后端（推荐 dev proxy；或补充 CORS origin）。

**技术方案（二选一）：**
- 方案 A（推荐）：前端 `vite.config.ts` 配置 proxy，转发 `/api` 到后端
- 方案 B：后端 `config.py` 添加 `http://localhost:5173` 到 CORS origins

**涉及文件：**
- `products/agent_workbench/config.py`（如选择补 CORS）
- `products/agent_workbench/fronted_origin/vite.config.ts`（如选择 proxy）

**测试方法：**
- 前端发起 `GET /api/agent/profile` 不报跨域错误

**预期结果：**
- 开发环境前后端可正常联调

---

## Step 4: 工程化落地前端骨架（前端 P0）

**任务描述：**
改造 `products/agent_workbench/fronted_origin`，使其成为可维护的生产前端工程。

**技术方案：**
1. 移除 `index.html` 中的 CDN Tailwind（`<script src="https://cdn.tailwindcss.com">`）
2. 安装本地依赖：`npm install -D tailwindcss postcss autoprefixer`
3. 创建 `tailwind.config.js` 和 `postcss.config.js`
4. 创建 `src/index.css` 引入 Tailwind 指令
5. 统一使用 `VITE_API_BASE` 环境变量配置 API base
6. 创建 `.env.development` 和 `.env.production`

**涉及文件：**
- `products/agent_workbench/fronted_origin/index.html`（移除 CDN）
- `products/agent_workbench/fronted_origin/package.json`（添加依赖）
- `products/agent_workbench/fronted_origin/tailwind.config.js`（新增）
- `products/agent_workbench/fronted_origin/postcss.config.js`（新增）
- `products/agent_workbench/fronted_origin/src/index.css`（新增）
- `products/agent_workbench/fronted_origin/.env.development`（新增）

**测试方法：**
- `npm install && npm run dev` 可启动，页面可打开
- Tailwind 样式正常生效

**预期结果：**
- 侧边栏/顶部栏/路由或 tab 切换可用（先静态）

---

## Step 5: 登录页与鉴权守卫（前端 P0）

**任务描述：**
实现坐席登录、token 存储、退出登录、401 自动跳转登录。

**技术方案：**
- 创建 `src/api/` 目录，封装 axios/fetch 请求
- 创建 `src/stores/auth.ts`（使用 React Context 或 zustand）
- token 存储在 localStorage，请求拦截器自动注入 Authorization header
- 401 响应拦截器自动跳转登录页

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/pages/Login.tsx`（新增）
- `products/agent_workbench/fronted_origin/src/api/client.ts`（新增，请求封装）
- `products/agent_workbench/fronted_origin/src/api/agent.ts`（新增，登录 API）
- `products/agent_workbench/fronted_origin/src/stores/auth.ts`（新增）
- `products/agent_workbench/fronted_origin/src/App.tsx`（添加路由守卫）

**测试方法：**
1. 打开前端，未登录访问工作台 → 自动跳转登录
2. 登录成功后进入工作台
3. 手动清空 token → 再次请求应回到登录

**预期结果：**
- 登录可用，token 自动注入请求头

---

## Step 6: 会话列表（队列/筛选/轮询）（前端 P0）

**任务描述：**
对接 `/api/sessions`、`/api/sessions/queue`、`/api/sessions/stats`，实现队列列表与基础筛选/搜索（参考 `docs/prd/04_任务拆解/L1-1-Part1_会话管理与筛选.md`）。

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/Workspace.tsx`（改造）
- `products/agent_workbench/fronted_origin/src/api/sessions.ts`（新增）

**测试方法：**
- 列表每 30s 轮询刷新；状态/关键字筛选生效

**预期结果：**
- pending_manual 会话可被快速定位，UI 信息与后端一致

---

## Step 7: 会话详情（含客户档案与内部备注）（前端 P0）

**任务描述：**
选中会话后加载：
- `GET /api/sessions/{session_name}`
- `GET /api/customers/{customer_id}/profile`
- 内部备注：`/api/sessions/{session_name}/notes`（CRUD）
- 转接历史：`/api/sessions/{session_name}/transfer-history`

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/Workspace.tsx`（改造）
- `products/agent_workbench/fronted_origin/src/api/misc.ts`（新增）

**测试方法：**
- 选择会话后详情区展示正确；新增/编辑/删除内部备注成功

**预期结果：**
- 会话详情可用且信息完整

---

## Step 8: 接管/释放/转接会话（前端 P0）

**任务描述：**
对接：
- `POST /api/sessions/{session}/takeover`
- `POST /api/sessions/{session}/release`
- `POST /api/sessions/{session}/transfer` + 转接请求处理

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/api/sessions.ts`（扩展）
- `products/agent_workbench/fronted_origin/src/components/Workspace.tsx`（改造）

**测试方法：**
- 执行操作后会话状态变化正确，冲突提示可读（如已被他人接管）

**预期结果：**
- 关键业务动作稳定可用

---

## Step 9: 会话聊天发送与实时刷新（前端 P0）

**任务描述：**
对接 Step 2 的消息接口与 Step 1 的会话 SSE，实现：
- 坐席发送消息
- 选中会话时建立 SSE，收到事件自动刷新详情

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/api/messages.ts`（新增）
- `products/agent_workbench/fronted_origin/src/api/sse.ts`（新增）
- `products/agent_workbench/fronted_origin/src/components/Workspace.tsx`（改造）

**测试方法：**
- 发送消息后立即出现在消息列表
- 另一端触发事件后，坐席端无需手动刷新即可更新

**预期结果：**
- 基本"实时会话"体验成立（轮询 + SSE）

---

## Step 10: 工单中心 MVP（列表/详情/创建/状态流转）（前端 P0）

**任务描述：**
对接 `/api/tickets/*` 实现：
- 列表/搜索/筛选
- 创建工单（含从会话创建：`POST /api/sessions/{session}/ticket`）
- 状态更新与指派（基础）

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/TicketsView.tsx`（改造）
- `products/agent_workbench/fronted_origin/src/api/tickets.ts`（新增）

**测试方法：**
- 创建/更新后刷新列表与详情一致

**预期结果：**
- 工单闭环可跑通

---

## Step 11: 工单评论/附件/审计日志 UI（前端 P1）

**任务描述：**
对接：
- 评论：`GET/POST/DELETE /api/tickets/{id}/comments`
- 附件：`GET/POST /api/tickets/{id}/attachments`
- 审计：`GET /api/tickets/{id}/audit-logs`

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/TicketsView.tsx`（添加评论/附件/审计 Tab）
- `products/agent_workbench/fronted_origin/src/api/tickets.ts`（扩展）

**测试方法：**
- 上传文件后可下载；审计日志可展示关键操作

**预期结果：**
- 工单协作能力补齐

---

## Step 12: 快捷回复（前端 P1）

**任务描述：**
实现快捷回复面板与管理页（参考 `L1-1-Part2_快捷回复与标签系统.md`），对接 `/api/quick-replies/*`。

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/Workspace.tsx`（添加快捷回复面板）
- `products/agent_workbench/fronted_origin/src/components/QuickReplyPanel.tsx`（新增）
- `products/agent_workbench/fronted_origin/src/api/quick-replies.ts`（新增）

**测试方法：**
- 插入模板后变量可替换/保留占位，使用统计递增

**预期结果：**
- 坐席回复效率显著提升

---

## Step 13: 工单模板管理与渲染（前端 P1）

**任务描述：**
对接 `/api/templates/*`，在创建工单时支持选择模板并渲染字段。

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/TicketsView.tsx`（创建工单对话框）
- `products/agent_workbench/fronted_origin/src/api/templates.ts`（新增）

**测试方法：**
- 选择模板后自动填充标题/描述等字段

**预期结果：**
- 工单录入更标准化

---

## Step 14: 监控页（缓存预热 / CDN / SLA 告警）（前端 P1）

**任务描述：**
对接：
- `/api/warmup/*`
- `/api/cdn/*`
- `/api/tickets/sla-alerts`、`/api/tickets/sla-summary`

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/Monitoring.tsx`（改造）
- `products/agent_workbench/fronted_origin/src/api/warmup.ts`（新增）
- `products/agent_workbench/fronted_origin/src/api/cdn.ts`（新增）

**测试方法：**
- 手动触发 warmup、查看 history；CDN 健康检查可返回日志

**预期结果：**
- 运营可观测性建立

---

## Step 15: 坐席管理后台（Admin）（前端 P1）

**任务描述：**
对接 `/api/agents/*` 实现坐席列表、创建/禁用、技能、重置密码等。

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/Settings.tsx`（添加坐席管理 Tab，或新增 AgentManagement.tsx）
- `products/agent_workbench/fronted_origin/src/api/agents.ts`（新增）

**测试方法：**
- admin 登录可见；普通坐席不可见（403 或隐藏）

**预期结果：**
- 基础后台管理可用

---

## Step 16: 协助请求与@提醒（前端 P1）

**任务描述：**
对接 `/api/assist-requests/*` 与 `/api/agent/events`（SSE），实现协助流转与提醒弹窗/通知中心。

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/Workspace.tsx`（添加协助请求入口）
- `products/agent_workbench/fronted_origin/src/components/NotificationCenter.tsx`（新增）
- `products/agent_workbench/fronted_origin/src/api/assist-requests.ts`（新增）
- `products/agent_workbench/fronted_origin/src/stores/notifications.ts`（新增）

**测试方法：**
- 创建协助请求后，被@坐席能实时收到事件并处理

**预期结果：**
- 多坐席协作成立

---

## Step 17: Shopify 订单信息面板（前端 P2）

**任务描述：**
在会话侧边信息中集成订单查询（按订单号/邮箱），对接 `/api/shopify/*`。

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/Workspace.tsx`（添加订单面板）
- `products/agent_workbench/fronted_origin/src/components/OrderPanel.tsx`（新增）
- `products/agent_workbench/fronted_origin/src/api/shopify.ts`（新增）

**测试方法：**
- 输入订单号/邮箱可返回订单与物流信息

**预期结果：**
- 售后关键数据在工作台内闭环

---

## Step 18: Dashboard 报表（前端 P2）

**任务描述：**
前端聚合展示核心指标（会话/工单/SLA），必要时补充后端聚合接口（P1 可选）。

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/Dashboard.tsx`（改造）
- `products/agent_workbench/fronted_origin/src/api/metrics.ts`（新增，可选）

**测试方法：**
- 指标与 `/api/sessions/stats`、`/api/tickets/sla-summary` 等数据一致

**预期结果：**
- 基础运营看板可用

---

## Step 19: Billing iframe 接入（前端 P2）

**任务描述：**
按原型 `BillingView` 设计接入 `products/customer_portal`（或独立部署域名）。

**涉及文件：**
- `products/agent_workbench/fronted_origin/src/components/BillingView.tsx`（改造）
- `products/agent_workbench/fronted_origin/.env.production`（添加 VITE_BILLING_URL）

**测试方法：**
- iframe 可加载，且 token 传递方案明确（query/postMessage 二选一）

**预期结果：**
- 计费门户可从工作台访问

---

## Step 20: 收尾（文档/验收/回归）

**任务描述：**
补齐运行说明、验收清单、回归测试建议，并更新：
- `memory-bank/progress.md`
- `memory-bank/architecture.md`（新增文件/模块用途）
- `products/agent_workbench/README.md`

**涉及文件：**
- `products/agent_workbench/README.md`
- `products/agent_workbench/memory-bank/progress.md`
- `products/agent_workbench/memory-bank/architecture.md`

**测试方法：**
- 按 PRD 的成功标准走一遍闭环

**预期结果：**
- 可交付给下一个 AI/开发者按步骤稳定推进

