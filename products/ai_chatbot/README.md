# AI 智能客服模块规范

> **模块定位**：核心产品，面向终端用户的 AI 对话服务
> **模块状态**：已上线
> **最后更新**：2025-12-18

---

## 一、模块职责

AI 智能客服模块提供：

- 基于 Coze 的智能对话能力
- Shopify 订单查询集成
- 人工客服无缝接管
- 多语言支持

---

## 二、API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/chat | POST | 同步 AI 对话 |
| /api/chat/stream | POST | 流式 AI 对话 |
| /api/conversation/new | POST | 创建新会话 |

---

## 三、依赖服务

```python
# 允许的依赖
from services.shopify import ShopifyService
from services.coze import CozeService
from services.session import SessionService
from infrastructure.database import get_redis_client
```

---

## 四、目录结构

```
products/ai_chatbot/
├── __init__.py
├── README.md            # 本文档
├── routes.py            # API 路由
├── handlers/
│   ├── chat_handler.py
│   └── conversation_handler.py
├── memory-bank/         # Vibe Coding 文档
│   ├── prd.md
│   ├── tech-stack.md
│   ├── implementation-plan.md
│   ├── progress.md
│   └── architecture.md
└── tests/
    └── test_chat.py
```

---

## 五、核心约束

### 5.1 Coze API 调用

- 必须使用 SSE 流式响应
- 必须传入 session_name 保证会话隔离
- 首次对话不传 conversation_id

### 5.2 状态机约束

```
bot_active → pending_manual → manual_live → bot_active
```

人工接管期间必须阻止 AI 对话

---

## 六、配置项

| 环境变量 | 说明 |
|----------|------|
| ENABLE_AI_CHATBOT | 模块启用开关 |
| COZE_WORKFLOW_ID | Coze 工作流 ID |
| COZE_APP_ID | Coze 应用 ID |

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
