# -*- coding: utf-8 -*-
"""
AI 智能客服 - 生命周期管理

提供 AI 客服模块独立启动时的生命周期管理，包括：
- 启动时初始化所需组件
- 关闭时清理资源

注意：此模块使用 infrastructure/bootstrap 的组件工厂进行初始化，
确保与全家桶模式（backend.py）使用相同的初始化逻辑。
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from infrastructure.bootstrap import (
    BootstrapFactory,
    Component,
    get_coze_client,
    get_token_manager,
    get_jwt_oauth_app,
    get_workflow_id,
    get_app_id,
    get_session_store,
    get_sse_queues,
    start_warmup_scheduler,
)
import services.bootstrap  # noqa: F401  # 注册服务层组件
from products.ai_chatbot.config import AIChatbotConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    AI 客服产品生命周期管理

    启动时初始化:
    - Redis/会话存储
    - Coze AI 客户端
    - Regulator 监管引擎（可选）
    - SSE 队列
    - 缓存预热调度器（可选）

    关闭时清理:
    - 后台任务
    """
    config: AIChatbotConfig = app.state.config

    print(f"\n{'='*60}")
    print(f"🚀 {config.product_name} 独立启动中...")
    print(f"{'='*60}\n")

    # 使用工厂模式初始化组件
    factory = BootstrapFactory()

    # 确定需要初始化的组件
    components = [
        Component.REDIS,
        Component.COZE,
        Component.SSE,
    ]

    if config.enable_regulator:
        components.append(Component.REGULATOR)

    # 初始化组件
    instances = factory.init_components(components)

    # 注入依赖到产品模块
    from products.ai_chatbot import dependencies as deps

    deps.set_coze_client(get_coze_client())
    deps.set_token_manager(get_token_manager())
    deps.set_session_store(get_session_store())
    deps.set_jwt_oauth_app(get_jwt_oauth_app())
    deps.set_config(get_workflow_id(), get_app_id())
    deps.set_sse_queues(get_sse_queues())

    # 设置 Regulator
    if config.enable_regulator and Component.REGULATOR in instances:
        deps.set_regulator(instances[Component.REGULATOR])

    # 启动预热调度器
    if config.enable_warmup:
        start_warmup_scheduler()

    print(f"\n{'='*60}")
    print(f"✅ {config.product_name} 启动完成")
    print(f"   端口: {config.port}")
    print(f"   API: {config.api_prefix}")
    print(f"{'='*60}\n")

    yield

    # 关闭时清理
    print(f"\n👋 {config.product_name} 正在关闭...")

    from infrastructure.bootstrap import shutdown_background_tasks
    await shutdown_background_tasks()

    print(f"✅ {config.product_name} 已关闭\n")
