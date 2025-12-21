# AI 智能客服 - 架构说明

> **最后更新**：2025-12-21

## 目录结构

```
products/ai_chatbot/
├── __init__.py           # 模块入口
├── main.py               # 独立启动入口
├── config.py             # 配置管理
├── routes.py             # API 路由注册
├── models.py             # 请求/响应模型
├── dependencies.py       # 依赖注入
├── lifespan.py           # 生命周期管理
├── handlers/
│   ├── __init__.py
│   ├── chat.py           # 聊天处理
│   ├── config.py         # 配置端点
│   ├── conversation.py   # 会话管理
│   └── manual.py         # 人工转接
├── frontend/             # Vue 3 前端
│   ├── src/
│   └── dist/
└── memory-bank/
    ├── prd.md
    ├── tech-stack.md
    ├── implementation-plan.md
    ├── progress.md
    └── architecture.md
```

**注**：提示词（prompts）已迁移到 Coze 平台管理。

## 依赖关系

```
products/ai_chatbot
├── services/session (会话状态管理)
├── services/coze (Coze Token 管理)
├── services/email (邮件发送)
└── infrastructure/security (认证)
```

## 核心组件

### routes.py
- 定义所有 API 端点
- 注册子路由

### handlers/chat.py
- /api/chat - 同步聊天
- /api/chat/stream - 流式聊天
- /api/bot/info - 机器人信息

### handlers/conversation.py
- /api/conversation/create - 创建会话
- /api/conversation/new - 新建对话
- /api/conversation/clear - 清除历史

### dependencies.py
- coze_client 依赖注入
- session_store 依赖注入
