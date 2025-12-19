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
"""

from fastapi import APIRouter

# 创建主路由
router = APIRouter(tags=["AI智能客服"])

# 子路由将在后续步骤中添加
# from products.ai_chatbot.handlers.chat import router as chat_router
# from products.ai_chatbot.handlers.conversation import router as conversation_router

# router.include_router(chat_router)
# router.include_router(conversation_router)
