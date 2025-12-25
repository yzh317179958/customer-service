# -*- coding: utf-8 -*-
"""
AI 智能客服 - 安全组件单例

用于在 handlers 中复用同一个 slowapi Limiter 实例（@limiter.limit），
并在 main.py 中挂载到 app.state.limiter。
"""

import os

from infrastructure.security import RateLimiterConfig, create_rate_limiter


RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "10/minute")


limiter = create_rate_limiter(
    RateLimiterConfig(
        default_limit=RATE_LIMIT_DEFAULT,
        storage_uri=os.getenv("REDIS_URL"),
        endpoint_limits={
            "/api/chat": RATE_LIMIT_CHAT,
            "/api/chat/stream": RATE_LIMIT_CHAT,
        },
    )
)

