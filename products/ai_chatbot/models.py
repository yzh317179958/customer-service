"""
AI 智能客服 - 请求/响应模型
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel


class UserIntent(str, Enum):
    """用户意图枚举 (v7.8.0)

    简化为三个业务分支 + 联系客服：
    - presale: 售前咨询（购车相关）
    - tracking: 物流查询（订单/包裹追踪）
    - after_sale: 售后问题（退换货、维修、投诉）
    - contact_agent: 联系售后团队
    """
    PRESALE = "presale"              # 售前咨询 (Pre-sales inquiry)
    TRACKING = "tracking"            # 物流查询 (Where's my package?)
    AFTER_SALE = "after_sale"        # 售后问题 (After-sales support)
    CONTACT_AGENT = "contact_agent"  # 联系售后团队 (Contact support team)


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    parameters: Optional[dict] = {}
    user_id: Optional[str] = None  # 会话 ID（前端生成的唯一标识）
    conversation_id: Optional[str] = None  # Conversation ID（用于保留历史对话）
    intent: Optional[UserIntent] = None  # 用户意图（v7.7.0 新增）
    order_number: Optional[str] = None  # 订单号（售后流程使用，v7.7.0 新增）


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
