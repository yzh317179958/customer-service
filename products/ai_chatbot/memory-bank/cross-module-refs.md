# 跨模块功能引用

> **文档类型**：跨模块功能引用记录
> **所属模块**：products/ai_chatbot（AI 智能客服）
> **最后更新**：2025-12-22

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
- 检测用户触发转人工意图（关键词、按钮）
- 调用 session 服务将会话状态改为 `pending_manual`
- 发布转人工事件到 Redis，供坐席工作台订阅
- 在等待人工接管期间保持会话活跃

**涉及文件**:
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `routes.py` | 已有 | 处理聊天消息，检测转人工意图 |
| `frontend/src/views/ChatView.vue` | 已有 | 显示转人工按钮和等待状态 |

**对接模块**:
- `products/agent_workbench` - 接收转人工通知，坐席接管会话
- `services/session` - 会话状态管理

---

## 快速导航

| 功能 | 主文档 | 状态 | 本模块职责 |
|------|--------|------|-----------|
| 转人工会话流转 | `docs/features/human-handoff/` | ✅ | 触发转人工、发布事件 |
| 微服务 SSE 通信 | `docs/features/microservice-sse-communication/` | ⏳ 开发中 | 发送 SSE 消息 |

---

### 微服务跨进程 SSE 通信

**主文档**: `docs/features/microservice-sse-communication/`

**状态**: ⏳ 开发中

**本模块职责**:
- 通过 `enqueue_sse_message()` 发送转人工消息
- 发送会话状态变化消息
- 无需代码改动（依赖注入，底层自动切换 Redis/内存）

**涉及文件**:
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `handlers/manual.py` | 检查 | 调用 enqueue_sse_message |

**对接模块**:
- `infrastructure/bootstrap/sse.py` - SSE 消息发布
- `products/agent_workbench` - 接收消息
