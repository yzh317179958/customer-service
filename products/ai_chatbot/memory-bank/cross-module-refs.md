# 跨模块功能引用

> **文档类型**：跨模块功能引用记录
> **所属模块**：products/ai_chatbot（AI 智能客服）
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
| 17track 物流集成 | `docs/features/17track-integration/` | ⏳ 开发中 | 商品卡片展示物流轨迹 |
| **聊天记录存储** | `docs/features/chat-history-storage/` | ⏳ 开发中 | 消息实时存储 |

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

---

### 17track 物流追踪集成

**主文档**: `docs/features/17track-integration/`

**状态**: ⏳ Phase 5 开发中

**版本历史**:
- v1.0：✅ 已完成（2025-12-23）- Phase 1-4 基础功能
- v2.0：⏳ 开发中 - Phase 5 集成完善

**本模块职责**:
- 商品卡片展示物流状态
- 点击「查看物流」展开完整轨迹时间线
- 调用 tracking 服务获取物流事件
- **Phase 5 新增**：处理"追踪中"状态，优化错误提示

**涉及文件**:
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `frontend/src/components/ChatMessage.vue` | 修改 | 添加可折叠物流轨迹 |
| `handlers/tracking.py` | 新增 | 物流轨迹查询 API |
| `routes.py` | 修改 | 注册 tracking 路由 |

**Phase 5 涉及文件**:
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `handlers/tracking.py` | 修改 | 调用自动注册方法，传递承运商 |
| `frontend/src/components/ChatMessage.vue` | 修改 | 优化错误状态显示 |

**对接模块**:
- `services/tracking` - 17track API 封装
- `products/notification` - 物流状态通知

---

### 聊天记录存储

**主文档**: `docs/features/chat-history-storage/`

**状态**: ⏳ 开发中
**进度**:
- Step 4 ✅: 已完成 DI + 生命周期注入（MessageStoreService 初始化与启动/关闭）
- Step 5 ✅: 已在 `handlers/chat.py` 写入点调用 enqueue 保存 user/assistant 消息

**本模块职责**:
- 用户消息发送时调用 `message_store.save_message()` 持久化
- AI 回复时保存消息并记录响应时间
- 人工客服消息由坐席工作台模块持久化（本模块不直接产生 agent 消息）
- 存储失败时降级处理，不阻塞聊天流程

**涉及文件**:
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `handlers/chat.py` | 修改 | 添加消息存储调用 |
| `dependencies.py` | 修改 | 注入 MessageStoreService |
| `lifespan.py` | 修改 | 初始化服务 |

**对接模块**:
- `services/session/message_store` - 消息持久化服务
- `products/agent_workbench` - 历史记录查询
- `infrastructure/database` - 数据库表模型
