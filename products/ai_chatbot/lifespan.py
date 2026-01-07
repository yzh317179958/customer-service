# -*- coding: utf-8 -*-
"""
AI 智能客服 - 生命周期管理

提供 AI 客服模块独立启动时的生命周期管理，包括：
- 启动时初始化所需组件
- 关闭时清理资源

微服务架构：本模块独立运行，包含完整的初始化逻辑。
"""

import os
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
    get_agent_manager,
    get_ticket_store,
    get_sse_queues,
    start_background_tasks,
    start_warmup_scheduler,
)
import services.bootstrap  # noqa: F401  # 注册服务层组件
from products.ai_chatbot.config import AIChatbotConfig
from services.session.message_store import MessageStoreService

# 清理代理环境变量（避免干扰 HTTP 请求）
_PROXY_ENV_VARS = [
    "http_proxy", "https_proxy", "all_proxy",
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
]
for _var in _PROXY_ENV_VARS:
    _value = os.environ.pop(_var, None)
    if _value:
        print(f"⚠️  检测到代理变量 {_var}，已忽略")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    AI 客服产品生命周期管理

    启动时初始化:
    - Redis/会话存储
    - Coze AI 客户端
    - Regulator 监管引擎（可选）
    - 坐席认证（用于人工转接）
    - 工单系统（用于工单创建）
    - SSE 队列
    - 智能分配引擎
    - 客户回复自动恢复规则
    - 后台任务（SLA 预警、心跳监控）
    - 缓存预热调度器（可选）

    关闭时清理:
    - 后台任务
    """
    config: AIChatbotConfig = app.state.config

    print(f"\n{'='*60}")
    print(f"🚀 {config.product_name} 微服务启动中...")
    print(f"{'='*60}\n")

    # ============================================================
    # 1. 使用工厂模式初始化组件
    # ============================================================
    factory = BootstrapFactory()

    # 确定需要初始化的组件
    components = [
        Component.REDIS,
        Component.COZE,
        Component.AGENT_AUTH,  # 用于人工转接时的坐席分配
        Component.TICKET,      # 用于工单创建
        Component.SSE,
    ]

    if config.enable_regulator:
        components.append(Component.REGULATOR)

    # 初始化组件
    instances = factory.init_components(components)

    # ============================================================
    # 2. 初始化业务组件
    # ============================================================
    session_store = get_session_store()
    agent_manager = get_agent_manager()
    ticket_store = get_ticket_store()
    sse_queues = get_sse_queues()

    # 智能分配引擎
    smart_assignment_engine = None
    try:
        if agent_manager and session_store:
            from services.ticket.assignment import SmartAssignmentEngine
            smart_assignment_engine = SmartAssignmentEngine(
                agent_manager=agent_manager,
                session_store=session_store
            )
            print("[Bootstrap] ✅ 智能分配引擎初始化成功")
    except Exception as e:
        print(f"[Bootstrap] ⚠️ 智能分配引擎初始化失败: {e}")

    # 客户回复自动恢复规则
    customer_reply_auto_reopen = None
    try:
        if ticket_store:
            from services.ticket.automation import CustomerReplyAutoReopen
            customer_reply_auto_reopen = CustomerReplyAutoReopen(
                ticket_store,
                agent_manager=agent_manager
            )
            print("[Bootstrap] ✅ 客户回复自动恢复规则初始化成功")
    except Exception as e:
        print(f"[Bootstrap] ⚠️ 客户回复自动恢复规则初始化失败: {e}")

    # ============================================================
    # 3. 注入依赖到产品模块
    # ============================================================
    from products.ai_chatbot import dependencies as deps

    deps.set_coze_client(get_coze_client())
    deps.set_token_manager(get_token_manager())
    deps.set_session_store(session_store)
    deps.set_jwt_oauth_app(get_jwt_oauth_app())
    deps.set_config(get_workflow_id(), get_app_id())
    deps.set_sse_queues(sse_queues)
    deps.set_smart_assignment_engine(smart_assignment_engine)
    deps.set_customer_reply_auto_reopen(customer_reply_auto_reopen)

    # Chat history message store (Step 4)
    message_store = MessageStoreService()
    await message_store.start()
    deps.set_message_store(message_store)

    # 设置 Regulator
    if config.enable_regulator and Component.REGULATOR in instances:
        deps.set_regulator(instances[Component.REGULATOR])

    print("[Bootstrap] ✅ AI 客服模块依赖初始化成功")

    # ============================================================
    # 4. 启动后台任务
    # ============================================================
    start_background_tasks(ticket_store, agent_manager, sse_queues)

    # 启动预热调度器
    if config.enable_warmup:
        start_warmup_scheduler()

    print(f"\n{'='*60}")
    print(f"✅ {config.product_name} 启动完成")
    print(f"   端口: {config.port}")
    print(f"   API: {config.api_prefix}")
    print(f"{'='*60}\n")

    yield

    # ============================================================
    # 5. 清理资源
    # ============================================================
    print(f"\n👋 {config.product_name} 正在关闭...")

    from infrastructure.bootstrap import shutdown_background_tasks
    await shutdown_background_tasks()

    try:
        await message_store.shutdown()
    except Exception:
        pass

    print(f"✅ {config.product_name} 已关闭\n")
