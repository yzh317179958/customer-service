"""
AI 智能客服 - 请求/响应模型
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    parameters: Optional[dict] = {}
    user_id: Optional[str] = None  # 会话 ID（前端生成的唯一标识）
    conversation_id: Optional[str] = None  # Conversation ID（用于保留历史对话）


class ChatResponse(BaseModel):
    """聊天响应模型"""
    success: bool
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class NewConversationRequest(BaseModel):
    """创建新对话请求"""
    user_id: Optional[str] = None


class ConversationResponse(BaseModel):
    """对话响应模型"""
    success: bool
    conversation_id: Optional[str] = None
    message: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    force: bool = False
