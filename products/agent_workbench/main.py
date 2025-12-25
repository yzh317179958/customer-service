#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐席工作台 - 独立启动入口

使用方法:
    # 直接运行
    python -m products.agent_workbench.main

    # 使用 uvicorn
    uvicorn products.agent_workbench.main:app --host 0.0.0.0 --port 8002

    # 使用环境变量配置
    AGENT_WORKBENCH_PORT=8002 python -m products.agent_workbench.main

环境变量:
    AGENT_WORKBENCH_HOST     - 监听地址，默认 0.0.0.0
    AGENT_WORKBENCH_PORT     - 监听端口，默认 8002
    DEBUG                    - 调试模式，默认 false
    ENABLE_SLA_ALERTS        - 启用 SLA 预警，默认 true
    ENABLE_HEARTBEAT_MONITOR - 启用心跳监控，默认 true
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from products.agent_workbench.config import get_config
from products.agent_workbench.lifespan import lifespan
from products.agent_workbench.routes import router

# 安全组件
from infrastructure.security import get_rate_limit_handler, get_metrics_response
from products.agent_workbench.security import limiter


def create_app() -> FastAPI:
    """创建坐席工作台 FastAPI 应用"""
    config = get_config()

    app = FastAPI(
        title=config.product_name,
        description="Fiido 坐席工作台 - 独立模式",
        version="1.0.0",
        lifespan=lifespan,
    )

    # 保存配置到 app.state
    app.state.config = config

    # ========================================
    # 安全组件初始化
    # ========================================

    # 限流器（在 products.agent_workbench.security 中创建，确保 handlers 复用同一个实例）
    app.state.limiter = limiter

    # 限流异常处理
    app.add_exception_handler(RateLimitExceeded, get_rate_limit_handler())

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router, prefix=config.api_prefix)

    # 根路径健康检查
    @app.get("/")
    async def root():
        return {
            "product": config.product_name,
            "code": config.product_code,
            "status": "running",
            "mode": "standalone",
        }

    # Prometheus 监控指标端点
    @app.get("/metrics")
    async def metrics():
        return get_metrics_response()

    return app


# 创建应用实例（供 uvicorn 使用）
app = create_app()


if __name__ == "__main__":
    import uvicorn

    config = get_config()
    uvicorn.run(
        "products.agent_workbench.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )
