# -*- coding: utf-8 -*-
"""
坐席工作台 - 生命周期管理

提供坐席工作台模块独立启动时的生命周期管理，包括：
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
    get_session_store,
    get_redis_client,
    get_agent_manager,
    get_agent_token_manager,
    get_ticket_store,
    get_ticket_template_store,
    get_audit_log_store,
    get_quick_reply_store,
    get_sse_queues,
    start_background_tasks,
)
import services.bootstrap  # noqa: F401  # 注册服务层组件
from products.agent_workbench.config import AgentWorkbenchConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    坐席工作台产品生命周期管理

    启动时初始化:
    - Redis/会话存储
    - 坐席认证系统
    - 工单系统
    - SSE 队列
    - 后台调度器（SLA 预警、心跳监控）

    关闭时清理:
    - 后台任务
    """
    config: AgentWorkbenchConfig = app.state.config

    print(f"\n{'='*60}")
    print(f"🚀 {config.product_name} 独立启动中...")
    print(f"{'='*60}\n")

    # 使用工厂模式初始化组件
    factory = BootstrapFactory()

    # 确定需要初始化的组件
    components = [
        Component.REDIS,
        Component.AGENT_AUTH,
        Component.TICKET,
        Component.SSE,
    ]

    # 初始化组件
    instances = factory.init_components(components)

    # 注入依赖到产品模块
    from products.agent_workbench import dependencies as deps

    deps.set_agent_manager(get_agent_manager())
    deps.set_agent_token_manager(get_agent_token_manager())
    deps.set_session_store(get_session_store())
    deps.set_ticket_store(get_ticket_store())
    deps.set_audit_log_store(get_audit_log_store())
    deps.set_quick_reply_store(get_quick_reply_store())
    deps.set_sse_queues(get_sse_queues())

    # 启动后台任务
    if config.enable_sla_alerts or config.enable_heartbeat_monitor:
        start_background_tasks(
            ticket_store=get_ticket_store() if config.enable_sla_alerts else None,
            agent_manager=get_agent_manager() if config.enable_heartbeat_monitor else None,
            sse_queues=get_sse_queues() if config.enable_sla_alerts else None,
        )

    print(f"\n{'='*60}")
    print(f"✅ {config.product_name} 启动完成")
    print(f"   端口: {config.port}")
    print(f"   API: {config.api_prefix}")
    print(f"   SLA预警: {'启用' if config.enable_sla_alerts else '禁用'}")
    print(f"   心跳监控: {'启用' if config.enable_heartbeat_monitor else '禁用'}")
    print(f"{'='*60}\n")

    yield

    # 关闭时清理
    print(f"\n👋 {config.product_name} 正在关闭...")

    from infrastructure.bootstrap import shutdown_background_tasks
    await shutdown_background_tasks()

    print(f"✅ {config.product_name} 已关闭\n")
