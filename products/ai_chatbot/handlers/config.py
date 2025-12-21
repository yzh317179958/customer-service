"""
AI 智能客服 - 配置与健康检查处理器

端点:
- GET /config - 配置信息
- GET /health - 健康检查
- GET /shift/config - 班次配置
- GET /shift/status - 班次状态
- GET /token/info - Token 信息
- POST /token/refresh - 刷新 Token
"""

import os
from fastapi import APIRouter, HTTPException
import httpx

from cozepy import Coze, TokenAuth

# 导入依赖
from products.ai_chatbot.dependencies import (
    get_coze_client,
    get_token_manager,
    get_workflow_id,
    get_app_id,
    set_coze_client,
)

# 导入班次配置
from services.session.shift_config import get_shift_config, is_in_shift

router = APIRouter()

# HTTP 超时配置
HTTP_TIMEOUT = httpx.Timeout(
    connect=float(os.getenv("HTTP_TIMEOUT_CONNECT", 10.0)),
    read=float(os.getenv("HTTP_TIMEOUT_READ", 30.0)),
    write=float(os.getenv("HTTP_TIMEOUT_WRITE", 30.0)),
    pool=float(os.getenv("HTTP_TIMEOUT_POOL", 10.0))
)


@router.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        coze_client = get_coze_client()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Coze 客户端未初始化")

    workflow_id = get_workflow_id()
    app_id = get_app_id()

    health_info = {
        "status": "healthy",
        "coze_connected": True,
        "workflow_id": workflow_id,
        "app_id": app_id,
        "auth_mode": "OAUTH_JWT",
        "session_isolation": True  # 会话隔离已启用
    }

    # OAuth+JWT 模式下添加 token 信息
    try:
        token_manager = get_token_manager()
        health_info["token_info"] = token_manager.get_token_info()
    except RuntimeError:
        pass

    return health_info


@router.get("/config")
async def get_config():
    """获取前端所需的配置信息（不包含敏感信息）"""
    workflow_id = get_workflow_id()
    app_id = get_app_id()

    return {
        "appId": app_id,
        "workflowId": workflow_id,
        "authMode": "OAUTH_JWT",
        "sessionIsolation": True  # 会话隔离已启用
    }


@router.get("/shift/config")
async def get_shift_config_api():
    """获取工作时间配置"""
    try:
        config = get_shift_config()
        return {
            "success": True,
            "data": config.get_config()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/shift/status")
async def get_shift_status():
    """获取当前是否在工作时间"""
    try:
        in_shift = is_in_shift()
        config = get_shift_config()
        return {
            "success": True,
            "data": {
                "is_in_shift": in_shift,
                "message": "人工客服在线" if in_shift else "当前为非工作时间",
                "shift_hours": f"{config.shift_start.strftime('%H:%M')} - {config.shift_end.strftime('%H:%M')}"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/token/info")
async def get_token_info():
    """获取当前 token 信息"""
    try:
        token_manager = get_token_manager()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Token 管理器未初始化")

    return token_manager.get_token_info()


@router.post("/token/refresh")
async def refresh_token():
    """手动刷新 token"""
    try:
        token_manager = get_token_manager()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Token 管理器未初始化")

    try:
        # 强制刷新 token
        new_token = token_manager.refresh_token()

        # 更新 Coze 客户端（禁用环境代理）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        new_coze_client = Coze(
            auth=TokenAuth(token=new_token),
            base_url=api_base,
            http_client=http_client
        )

        # 更新全局客户端
        set_coze_client(new_coze_client)

        return {
            "success": True,
            "message": "Token 刷新成功",
            "token_info": token_manager.get_token_info()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token 刷新失败: {str(e)}")
