"""
AI 智能客服 - handlers 模块

包含:
- chat: 聊天处理（/chat, /chat/stream, /bot/info）
- conversation: 会话管理（/conversation/*）
- config: 配置与健康检查（/config, /health, /shift/*, /token/*）
"""

from products.ai_chatbot.handlers.chat import router as chat_router
from products.ai_chatbot.handlers.conversation import router as conversation_router
from products.ai_chatbot.handlers.config import router as config_router

__all__ = ["chat_router", "conversation_router", "config_router"]
