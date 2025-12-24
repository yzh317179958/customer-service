# AI 智能客服 - 进度追踪

> **版本**: v7.7.0
> **创建日期**: 2025-12-24
> **当前状态**: v7.7.0 开发中

---

## 一、版本历史

### v7.6.x - 核心功能完成

**完成时间**: 2025-12-23
**状态**: ✅ 已上线

**已完成功能**:

| 功能 | 说明 | 状态 |
|------|------|------|
| Coze 工作流集成 | 会话隔离、流式响应、多轮对话 | ✅ |
| 订单查询 | Shopify 多站点、缓存机制 | ✅ |
| 物流追踪 | 17track API、自动注册、时间线 | ✅ |
| 人工转接 | 状态机、班次控制、SSE 推送 | ✅ |
| 前端交互 | Vue 3 + Pinia、快捷回复、消息气泡 | ✅ |

**API 端点统计**:

| Handler | 端点数 | 说明 |
|---------|--------|------|
| chat.py | 3 | 同步聊天、流式聊天、机器人信息 |
| conversation.py | 3 | 创建会话、新建对话、清除历史 |
| config.py | 6 | 配置信息、健康检查、班次、Token |
| manual.py | 2 | 人工升级、人工消息写入 |
| tracking.py | 2 | 物流轨迹、物流状态 |

**总计**: 16 个 API 端点

---

## 二、v7.7.0 开发进度

### Phase 1 - P0 核心功能

| Step | 任务 | 状态 | 完成时间 |
|------|------|------|----------|
| 1.1 | TrackingStatus 枚举英文化 | ✅ 已完成 | 2025-12-24 |
| 1.2 | API 响应默认返回英文 | ✅ 已完成 | 2025-12-24 |
| 1.3 | 前端 UI 文案英文化 | ✅ 已完成 | 2025-12-24 |
| 1.4 | 提示词英文化 | ✅ 已完成 | 2025-12-24 |
| 1.5 | UserIntent 枚举定义 | ✅ 已完成 | 2025-12-24 |
| 1.6 | chat.py 处理 intent 参数 | ✅ 已完成 | 2025-12-24 |
| 1.7 | 售后流程状态机 | ✅ 已完成 | 2025-12-24 |
| 1.8 | UI 素材替换 | ⬜ 待开发 | - |

**Phase 1 进度**: 7/8 (87.5%)

---

### Phase 2 - P1 重要功能

| Step | 任务 | 状态 | 完成时间 |
|------|------|------|----------|
| 2.1 | 添加 slowapi 依赖 | ⬜ 待开发 | - |
| 2.2 | main.py 集成限流中间件 | ⬜ 待开发 | - |
| 2.3 | chat 端点添加限流装饰器 | ⬜ 待开发 | - |
| 2.4 | 监控指标端点 | ⬜ 待开发 | - |

**Phase 2 进度**: 0/4 (0%)

---

### Phase 3 - P2 扩展功能

| Step | 任务 | 状态 | 完成时间 |
|------|------|------|----------|
| 3.1 | 多语言动态切换 | ⬜ 规划中 | - |
| 3.2 | 会话历史持久化 | ⬜ 规划中 | - |
| 3.3 | 富媒体消息支持 | ⬜ 规划中 | - |

**Phase 3 进度**: 0/3 (0%)

---

## 三、总体进度

```
v7.7.0 总进度: [█████████░] 47%

Phase 1 (P0): [█████████░] 87.5% (7/8)
Phase 2 (P1): [░░░░░░░░░░] 0% (0/4)
Phase 3 (P2): [░░░░░░░░░░] 0% (0/3)
```

---

## 四、已完成 Step 详情

### Step 1.1: TrackingStatus 枚举英文化
- **状态**: ✅ 已完成（枚举值本身已是英文）
- **验证**: `TrackingStatus.DELIVERED.value == "Delivered"`

### Step 1.2: API 响应默认返回英文
- **改动文件**:
  - `services/tracking/service.py`: 硬编码中文改为英文
  - `products/ai_chatbot/handlers/tracking.py`: 添加 `_status_text_en()` 函数，message 字段改为英文
- **验证**: `/api/tracking/{tracking_number}` 返回 `current_status_zh: "Tracking"`

### Step 1.3: 前端 UI 文案英文化
- **改动文件**:
  - `frontend/src/components/ChatMessage.vue`: 错误提示、按钮文案改为英文
  - `products/ai_chatbot/handlers/chat.py`: bot 默认配置改为英文
  - `.env` / `.env.example`: Bot 配置改为英文
- **验证**: `/api/bot/info` 返回 `name: "Fiido Support"`

### Step 1.4: 提示词英文化
- **改动文件**:
  - `prompts/订单查询回复_v2.md`: 特殊场景添加英文模板，预计送达时间添加英文列
  - `prompts/order_query_reply_v2.md`: 新增全英文版本（用于生产迁移）
- **验证**: AI 回复符合英文模板格式，PRODUCT 标签正确解析

### Step 1.5: UserIntent 枚举定义
- **改动文件**:
  - `products/ai_chatbot/models.py`: 新增 UserIntent 枚举（5 个值）
  - `ChatRequest` 新增 `intent` 和 `order_number` 字段
- **枚举值**: PRESALE, ORDER_STATUS, AFTER_SALE, CONTACT_AGENT, GENERAL
- **验证**: Python 导入测试通过

### Step 1.6: chat.py 处理 intent 参数
- **改动文件**:
  - `products/ai_chatbot/handlers/chat.py`: 同步/流式接口添加 INTENT 和 ORDER_NUMBER 参数传递
- **Coze 参数**:
  - `parameters.INTENT`: 用户意图（如 "order_status"）
  - `parameters.ORDER_NUMBER`: 订单号（售后流程使用）
- **验证**: curl 测试，日志显示 "🎯 Intent: order_status"

### Step 1.7: 售后流程状态机
- **改动文件**:
  - `frontend/src/stores/chatStore.ts`: 添加 UserIntent、AfterSaleState 类型和状态管理方法
  - `frontend/src/components/WelcomeScreen.vue`: 快捷回复按钮添加 intent 属性
  - `frontend/src/components/ChatPanel.vue`: 实现售后状态机逻辑，订单号验证流程
- **状态流程**:
  - idle → awaiting_order（点击售后按钮）
  - awaiting_order → validating（用户输入订单号）
  - validating → order_found/awaiting_order（验证成功/失败）
  - order_found → awaiting_issue（等待用户描述问题）
- **验证**: 前端构建成功

---

## 五、下一步工作

**当前任务**: Step 1.8 - UI 素材替换

**待改动文件**:
- `frontend/public/icons/` 品牌 icon 文件

**验证方法**:
- 前端显示正确的品牌图标

---

## 六、阻塞问题

暂无阻塞问题。

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v7.7.0-r5 | 2025-12-24 | 记录 Step 1.7 完成，进度 87.5% |
| v7.7.0-r4 | 2025-12-24 | 记录 Step 1.5-1.6 完成，进度 75% |
| v7.7.0-r3 | 2025-12-24 | 记录 Step 1.4 完成，更新进度至 50% |
| v7.7.0-r2 | 2025-12-24 | 记录 Step 1.1-1.3 完成，更新进度 |
| v7.7.0 | 2025-12-24 | 全新创建，记录 v7.6.x 已完成功能，规划 v7.7.0 任务 |
