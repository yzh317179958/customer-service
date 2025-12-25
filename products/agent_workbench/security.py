# -*- coding: utf-8 -*-
"""
坐席工作台 - 安全组件单例

用于在 handlers 中复用同一个 slowapi Limiter 实例（@limiter.limit），
并在 main.py 中挂载到 app.state.limiter。
"""

import os

from infrastructure.security import RateLimiterConfig, create_rate_limiter


RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "5/minute")
RATE_LIMIT_REFRESH = os.getenv("RATE_LIMIT_REFRESH", "10/minute")


limiter = create_rate_limiter(
    RateLimiterConfig(
        default_limit=RATE_LIMIT_DEFAULT,
        storage_uri=os.getenv("REDIS_URL"),
        endpoint_limits={
            "/api/agent/login": RATE_LIMIT_LOGIN,
            "/api/agent/refresh": RATE_LIMIT_REFRESH,
        },
    )
)

