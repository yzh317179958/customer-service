"""
AI 智能客服 - 会话管理处理器

端点:
- POST /conversation/create - 创建新 Conversation
- POST /conversation/new - 创建新对话
- POST /conversation/clear - 清除历史会话
"""

import os
from fastapi import APIRouter, HTTPException
import httpx

from cozepy import Coze, TokenAuth

# 导入依赖
from products.ai_chatbot.dependencies import (
    get_coze_client,
    get_token_manager,
    get_jwt_oauth_app,
    get_workflow_id,
    get_app_id,
)

# 导入模型
from products.ai_chatbot.models import NewConversationRequest, ConversationResponse

# 导入聊天模块的缓存（共享 conversation_cache）
from products.ai_chatbot.handlers.chat import conversation_cache

router = APIRouter()

# HTTP 超时配置
HTTP_TIMEOUT = httpx.Timeout(
    connect=float(os.getenv("HTTP_TIMEOUT_CONNECT", 10.0)),
    read=float(os.getenv("HTTP_TIMEOUT_READ", 30.0)),
    write=float(os.getenv("HTTP_TIMEOUT_WRITE", 30.0)),
    pool=float(os.getenv("HTTP_TIMEOUT_POOL", 10.0))
)


@router.post("/conversation/create")
async def create_conversation(request: NewConversationRequest):
    """
    创建新的 Conversation (用于多轮对话)
    每次创建新对话时调用此接口,返回 conversation_id
    """
    coze_client = get_coze_client()
    token_manager = get_token_manager()

    try:
        session_id = request.user_id

        # 获取带 session_name 的 token
        access_token = token_manager.get_access_token(session_name=session_id)

        # 刷新 coze_client (确保使用正确的 token，禁用环境代理)
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        temp_coze_client = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )

        # 使用 Coze SDK 创建 conversation
        conversation = temp_coze_client.conversations.create()

        print(f"✅ 创建新 Conversation: {conversation.id} (session: {session_id})")

        return ConversationResponse(
            success=True,
            conversation_id=conversation.id
        )

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 创建 Conversation 失败: {error_msg}")
        return ConversationResponse(
            success=False,
            error=error_msg
        )


@router.post("/conversation/new")
async def create_new_conversation(request: dict):
    """
    创建新对话 (使用 Python SDK)
    保持 session_id 不变,但创建新的 conversation

    【Coze API 约束】
    - 严格遵守 PRD 12.1.1: 不手动生成 conversation_id，由 Coze 自动生成
    - 必须传入 session_name 实现会话隔离
    """
    global conversation_cache

    jwt_oauth_app = get_jwt_oauth_app()
    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    if not jwt_oauth_app:
        raise HTTPException(status_code=503, detail="JWTOAuthApp 未初始化")

    try:
        # 使用 JWTOAuthApp 生成带 session_name 的 token
        token_response = jwt_oauth_app.get_access_token(
            ttl=3600,
            session_name=session_id  # 【Coze 约束】会话隔离关键
        )

        # 提取 access_token
        access_token = token_response.access_token if hasattr(token_response, 'access_token') else token_response

        # 使用 Python SDK 创建 Coze 客户端（配置超时和代理）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        temp_coze = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )

        # 【Coze 约束】创建新 conversation（由 Coze 自动生成 ID）
        conversation = temp_coze.conversations.create()

        # 更新缓存：保存新的 conversation_id
        conversation_cache[session_id] = conversation.id

        print(f"✅ 新对话已创建: {conversation.id} (session: {session_id})")

        return {
            "success": True,
            "conversation_id": conversation.id
        }
    except Exception as e:
        print(f"❌ 创建对话失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/conversation/clear")
async def clear_conversation_history(request: dict):
    """
    清除历史会话
    实现方式：创建新的 conversation_id 并更新缓存

    【Coze API 约束】
    - 严格遵守 PRD 12.1.1: conversation_id 由 Coze 生成，不手动创建
    - 清除历史 = 创建新会话，废弃旧 conversation_id
    - 必须更新 session_name → conversation_id 映射关系
    """
    global conversation_cache

    jwt_oauth_app = get_jwt_oauth_app()
    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    if not jwt_oauth_app:
        raise HTTPException(status_code=503, detail="JWTOAuthApp 未初始化")

    try:
        # 记录旧的 conversation_id（用于日志）
        old_conversation_id = conversation_cache.get(session_id, "无")

        # 使用 JWTOAuthApp 生成带 session_name 的 token
        token_response = jwt_oauth_app.get_access_token(
            ttl=3600,
            session_name=session_id  # 【Coze 约束】会话隔离
        )

        # 提取 access_token
        access_token = token_response.access_token if hasattr(token_response, 'access_token') else token_response

        # 使用 Python SDK 创建 Coze 客户端（配置超时和代理）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        temp_coze = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )

        # 【Coze 约束】创建新的 conversation（自动生成新 ID）
        new_conversation = temp_coze.conversations.create()

        # 更新缓存：用新 conversation_id 替换旧的
        conversation_cache[session_id] = new_conversation.id

        print(f"✅ 历史会话已清除")
        print(f"   Session: {session_id}")
        print(f"   旧 Conversation: {old_conversation_id}")
        print(f"   新 Conversation: {new_conversation.id}")

        return {
            "success": True,
            "conversation_id": new_conversation.id,
            "message": "历史会话已清除，新对话已创建"
        }
    except Exception as e:
        print(f"❌ 清除历史失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
