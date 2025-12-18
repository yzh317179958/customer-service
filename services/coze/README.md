# Coze AI 服务规范

> **服务定位**：Coze API 封装与 Token 管理
> **服务状态**：已完成
> **最后更新**：2025-12-18

---

## 一、服务职责

- Coze API 调用封装
- OAuth Token 自动刷新
- 会话管理
- SSE 流式响应处理

---

## 二、公开接口

```python
class CozeService:
    async def chat(
        self,
        message: str,
        session_id: str,
        conversation_id: str = None
    ) -> AsyncGenerator

    async def chat_sync(
        self,
        message: str,
        session_id: str
    ) -> dict

def get_coze_service() -> CozeService
```

---

## 三、目录结构

```
services/coze/
├── __init__.py
├── README.md           # 本文档
├── client.py           # Coze API 客户端
├── service.py          # 业务服务
├── token_manager.py    # Token 管理
└── tests/
    └── test_coze.py
```

---

## 四、核心约束

- 必须使用 SSE 流式调用
- Token 过期自动刷新
- 禁止手动生成 conversation_id

---

## 五、配置项

| 环境变量 | 说明 |
|----------|------|
| COZE_WORKFLOW_ID | 工作流 ID |
| COZE_APP_ID | 应用 ID |
| COZE_OAUTH_CLIENT_ID | OAuth 客户端 ID |
| COZE_OAUTH_CLIENT_SECRET | OAuth 客户端密钥 |

---

## 六、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
