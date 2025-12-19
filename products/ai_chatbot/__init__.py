# -*- coding: utf-8 -*-
"""
AI 智能客服产品模块

提供 AI 客服相关功能:
- 多轮对话
- 会话管理
- Coze AI 集成
"""


def get_router():
    """延迟导入路由，避免循环导入"""
    from products.ai_chatbot.routes import router
    return router


__all__ = ["get_router"]
