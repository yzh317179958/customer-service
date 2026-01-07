# 跨模块功能引用

> **文档类型**：跨模块功能引用记录
> **所属模块**：products/agent_workbench（坐席工作台）
> **最后更新**：2026-01-07

---

## 说明

本文件记录本模块参与的所有跨模块功能，便于追踪和维护。

每个跨模块功能的完整文档位于 `docs/features/[功能名]/`，本文件仅保存引用和本模块的职责说明。

---

## 参与的跨模块功能

### 转人工会话流转

**主文档**: `docs/features/human-handoff/`（待创建）

**状态**: ✅ 已完成（核心功能）

**本模块职责**:

- 订阅 Redis 事件，接收新的待接入会话
- 展示待接入队列，显示客户信息和等待时间
- 坐席点击「接管」后，将会话状态改为 `manual_live`
- 提供实时消息收发界面
- 坐席结束服务后，将会话状态改回 `bot_active`

**涉及文件**:


| 文件                                  | 改动类型 | 说明                               |
| ------------------------------------- | -------- | ---------------------------------- |
| `handlers/sessions.py`                | 已有     | 会话接管、释放、消息发送 API       |
| `frontend/components/Workspace.tsx`   | 已有     | 工作台主界面，待接入队列，消息列表 |
| `frontend/src/stores/sessionStore.ts` | 已有     | 会话状态管理                       |
| `frontend/src/api/sessions.ts`        | 已有     | 会话 API 封装                      |

**对接模块**:

- `products/ai_chatbot` - 触发转人工，发布事件
- `services/session` - 会话状态管理

---

## 快速导航


| 功能           | 主文档                         | 状态 | 本模块职责                   |
| -------------- | ------------------------------ | ---- | ---------------------------- |
| 转人工会话流转 | `docs/features/human-handoff/` | ✅   | 接收通知、坐席接管、消息收发 |
| 微服务 SSE 通信 | `docs/features/microservice-sse-communication/` | ⏳ 开发中 | 订阅 SSE 消息 |
| **聊天记录存储** | `docs/features/chat-history-storage/` | ⏳ 开发中 | 历史记录查询界面 |

---

### 微服务跨进程 SSE 通信

**主文档**: `docs/features/microservice-sse-communication/`

**状态**: ⏳ 开发中

**本模块职责**:
- 通过 `subscribe_sse_events()` 订阅会话消息
- 接收转人工通知、状态变化等实时消息
- 改造 SSE 事件流端点使用新接口

**涉及文件**:
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `handlers/sessions.py` | 修改 | 改造 SSE 订阅方式 |

**对接模块**:
- `infrastructure/bootstrap/sse.py` - SSE 消息订阅
- `products/ai_chatbot` - 发送消息

---

### 聊天记录存储

**主文档**: `docs/features/chat-history-storage/`

**状态**: ⏳ 开发中
**进度**:
- Step 6 ✅: 坐席发送消息持久化（role=agent）
  - DI 注入 MessageStoreService
  - `agent_send_message` enqueue 保存 agent 消息
- Step 7 ✅: 历史记录查询 API（list/detail/search/stats/export）

**本模块职责**:
- 提供历史记录查询 API（会话列表、详情、搜索、统计）
- 提供数据导出功能（CSV）
- 前端历史记录页面展示
- 需要坐席认证才能访问

**涉及文件**:
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `handlers/history.py` | 新增 | 历史记录 API |
| `routes.py` | 修改 | 注册路由 |
| `dependencies.py` | 修改 | 注入 MessageStoreService |
| `frontend/components/History.tsx` | 新增 | 历史记录页面（React） |
| `frontend/App.tsx` | 修改 | 注册路由 |
| `frontend/components/Sidebar.tsx` | 修改 | 添加菜单入口 |
| `frontend/src/api/history.ts` | 新增 | API 调用封装 |
| `handlers/sessions.py` | 修改 | 坐席发送消息时持久化（role=agent） |

**对接模块**:
- `services/session/message_store` - 消息持久化服务
- `products/ai_chatbot` - 消息产生源
- `infrastructure/database` - 数据库表模型
