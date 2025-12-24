# AI 智能客服 - 架构说明

> **版本**: v7.7.0
> **创建日期**: 2025-12-24

---

## 一、目录结构

```
products/ai_chatbot/
├── __init__.py               # 模块入口
├── main.py                   # 独立启动入口
├── config.py                 # 配置管理
├── routes.py                 # API 路由注册
├── models.py                 # 请求/响应模型 + Intent 枚举
├── dependencies.py           # 依赖注入
├── lifespan.py               # 生命周期管理
├── handlers/
│   ├── __init__.py
│   ├── chat.py               # 聊天处理（含 intent 识别）
│   ├── config.py             # 配置端点
│   ├── conversation.py       # 会话管理
│   ├── manual.py             # 人工转接
│   └── tracking.py           # 物流轨迹查询
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.vue      # 主聊天面板（含售后状态机）
│   │   │   ├── WelcomeScreen.vue  # 欢迎界面（快捷回复）
│   │   │   ├── ChatMessage.vue    # 消息气泡
│   │   │   └── StatusBar.vue      # 状态栏
│   │   ├── stores/
│   │   │   └── chatStore.ts       # Pinia 状态（含 intent、afterSaleState）
│   │   └── api/
│   │       └── chat.ts            # API 调用
│   ├── public/
│   │   └── icons/                 # 品牌 icon（v7.7.0 新增）
│   └── dist/                      # 构建产物
├── prompts/                  # 提示词模板
│   ├── 订单查询回复_v2.md        # 中文测试版（支持中英双语）
│   ├── order_query_reply_v2.md  # 英文生产版（v7.7.0 新增）
│   └── ...
└── memory-bank/
    ├── prd.md
    ├── tech-stack.md
    ├── implementation-plan.md
    ├── progress.md
    └── architecture.md
```

---

## 二、依赖关系

```
products/ai_chatbot
│
├── services/session          # 会话状态管理
├── services/coze             # Coze Token 管理、AI 对话
├── services/shopify          # 订单查询、物流信息
├── services/tracking         # 17track 物流追踪
├── services/email            # 邮件发送（可选）
├── services/asset            # 产品图片匹配
│
└── infrastructure/
    ├── bootstrap             # 组件工厂、依赖注入、SSE
    ├── security              # JWT 签名、限流（v7.7.0 新增）
    ├── database              # PostgreSQL + Redis 双写
    └── monitoring            # 指标采集（v7.7.0 新增）
```

---

## 三、数据存储

| 数据类型 | 主存储 | 缓存 | 说明 |
|----------|--------|------|------|
| 活跃会话 | Redis | - | 高频读写，TTL 过期 |
| 工单数据 | PostgreSQL | Redis | 双写模式 |
| 审计日志 | PostgreSQL | Redis | 双写模式 |
| 会话归档 | PostgreSQL | - | 持久化存储 |
| Shopify 缓存 | Redis | - | TTL 过期 |
| 物流轨迹 | Redis | - | 17track 缓存 |

---

## 四、核心组件

### 4.1 routes.py - API 路由

```python
# 路由注册
router = APIRouter(prefix="/api")
router.include_router(chat_router)
router.include_router(conversation_router)
router.include_router(config_router)
router.include_router(manual_router)
router.include_router(tracking_router)
```

### 4.2 handlers/chat.py - 聊天处理

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/chat | POST | 同步聊天 |
| /api/chat/stream | POST | 流式聊天（SSE） |
| /api/bot/info | GET | 机器人信息 |

**v7.7.0 变更**:
- Bot 默认配置改为英文（name: "Fiido Support"）
- 从 `.env` 读取 `COZE_BOT_NAME`, `COZE_BOT_DESCRIPTION`, `COZE_BOT_WELCOME`

**v7.7.0 新增**: Intent 识别逻辑

```python
async def handle_chat(request: ChatRequest):
    # 根据 intent 选择处理流程
    if request.intent == UserIntent.AFTER_SALE:
        # 售后流程：先校验订单
        if not request.order_number:
            return {"action": "request_order"}
        order = await shopify.search_order_by_number(request.order_number)
        if not order:
            return {"action": "order_not_found"}
    # ... 调用 Coze
```

### 4.3 handlers/conversation.py - 会话管理

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/conversation/create | POST | 创建会话 |
| /api/conversation/new | POST | 新建对话 |
| /api/conversation/clear | POST | 清除历史 |

### 4.4 handlers/tracking.py - 物流追踪

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/tracking/{tracking_number} | GET | 查询物流轨迹 |
| /api/tracking/{tracking_number}/status | GET | 查询物流状态 |

**v7.7.0 变更**:
- 添加 `_status_text_en()` 函数，状态文本默认英文
- `message` 字段默认英文，`message_zh` 保留中文
- `current_status_zh` 改为使用英文映射

### 4.5 dependencies.py - 依赖注入

```python
# 核心依赖
def get_coze_client() -> CozeClient
def get_session_store() -> SessionStore
def get_shopify_service(site: str) -> ShopifyService
def get_tracking_service() -> TrackingService
```

---

## 五、v7.7.0 新增架构

### 5.1 Intent 意图预识别流程

```
┌─────────────────────────────────────────────────────────────┐
│                      用户点击快捷回复                         │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
  │ Where's my    │   │ Product Help  │   │ Running into  │
  │ package?      │   │ (售前咨询)     │   │ a little issue│
  └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
          │                   │                   │
          ▼                   ▼                   ▼
  intent=order_status  intent=presale     intent=after_sale
          │                   │                   │
          │                   │                   ▼
          │                   │           ┌───────────────┐
          │                   │           │  订单校验流程  │
          │                   │           │  (状态机)     │
          │                   │           └───────┬───────┘
          │                   │                   │
          └───────────────────┴───────────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │   Coze API    │
                      └───────────────┘
```

### 5.2 售后流程状态机

```
┌─────────┐  点击售后按钮  ┌─────────────────┐
│  idle   │ ────────────► │ awaiting_order  │
└─────────┘               └────────┬────────┘
                                   │ 用户输入订单号
                                   ▼
                          ┌─────────────────┐
                          │   validating    │
                          └────────┬────────┘
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌─────────────┐ ┌─────────────┐
            │ order_found │ │ 订单不存在   │
            └──────┬──────┘ │ 重新输入     │
                   │        └─────────────┘
                   ▼
          ┌─────────────────┐
          │ awaiting_issue  │
          └────────┬────────┘
                   │ 用户输入问题
                   ▼
          ┌─────────────────┐
          │ 调用 Coze API   │
          └─────────────────┘
```

### 5.3 请求限流架构

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI App                           │
├─────────────────────────────────────────────────────────────┤
│                    RateLimitMiddleware                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  session_id: 10 req/min                                 ││
│  │  IP: 100 req/min                                        ││
│  │  Global: 1000 req/min                                   ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                       API Handlers                           │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 监控指标架构

```
┌─────────────────────────────────────────────────────────────┐
│                      API Handlers                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  @metrics.track_request_duration                        ││
│  │  @metrics.count_api_calls                               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Prometheus Metrics Export   │
              │   GET /metrics                │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      Alerting System          │
              │   - Coze API 错误率 > 5%      │
              │   - 响应时间 P95 > 3s         │
              └───────────────────────────────┘
```

---

## 六、前端状态管理

### 6.1 chatStore.ts 状态结构

```typescript
interface ChatState {
  // 基础状态
  sessionId: string
  conversationId: string | null
  messages: Message[]
  isLoading: boolean

  // v7.7.0 新增
  currentIntent: UserIntent | null
  afterSaleState: AfterSaleState
  validatedOrderNumber: string | null
}

type UserIntent =
  | 'presale'
  | 'order_status'
  | 'after_sale'
  | 'contact_agent'
  | 'general'

type AfterSaleState =
  | 'idle'
  | 'awaiting_order'
  | 'validating'
  | 'order_found'
  | 'awaiting_issue'
```

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v7.7.0-r2 | 2025-12-24 | Step 1.7 完成：售后状态机实现（chatStore.ts、ChatPanel.vue、WelcomeScreen.vue） |
| v7.7.0 | 2025-12-24 | 全新创建，新增 Intent 流程、售后状态机、限流、监控架构 |
