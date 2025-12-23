"""
AI 智能客服 - API 路由

路由前缀: /api
端点:
- POST /chat - 同步聊天
- POST /chat/stream - 流式聊天
- GET /bot/info - 机器人信息
- POST /conversation/create - 创建会话
- POST /conversation/new - 新建对话
- POST /conversation/clear - 清除历史
- GET /config - 配置信息
- GET /health - 健康检查
- GET /shift/config - 班次配置
- GET /shift/status - 班次状态
- GET /token/info - Token 信息
- POST /token/refresh - 刷新 Token
- POST /manual/escalate - 人工升级
- POST /manual/messages - 人工消息写入
- GET /sessions/{session_name} - 获取会话状态
- GET /sessions/{session_name}/events - 会话 SSE 事件流
- GET /shopify/* - Shopify 订单查询（供 Coze 插件调用）
- GET /tracking/{tracking_number} - 物流轨迹查询
- GET /tracking/{tracking_number}/status - 物流状态查询（轻量）
"""

from fastapi import APIRouter

# 创建主路由
router = APIRouter(tags=["AI智能客服"])

# 导入子路由
from products.ai_chatbot.handlers.chat import router as chat_router
from products.ai_chatbot.handlers.conversation import router as conversation_router
from products.ai_chatbot.handlers.config import router as config_router
from products.ai_chatbot.handlers.manual import router as manual_router
from products.ai_chatbot.handlers.sessions import router as sessions_router
from products.ai_chatbot.handlers.tracking import router as tracking_router

# 导入共享服务路由（供 Coze 插件调用）
from products.agent_workbench.handlers.shopify import router as shopify_router

# 注册所有子路由
router.include_router(chat_router)
router.include_router(conversation_router)
router.include_router(config_router)
router.include_router(manual_router)
router.include_router(sessions_router)
router.include_router(tracking_router)  # 物流轨迹查询
router.include_router(shopify_router)  # Shopify 订单查询
