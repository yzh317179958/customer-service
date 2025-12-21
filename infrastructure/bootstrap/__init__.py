# -*- coding: utf-8 -*-
"""
基础设施 - 启动引导模块

提供产品模块独立启动所需的共享初始化逻辑。

支持两种启动模式：
1. 全家桶模式：通过 backend.py 启动所有产品
2. 独立模式：每个产品通过自己的 main.py 独立启动

使用示例:
    # 方式1: 使用工厂模式按需初始化
    from infrastructure.bootstrap import BootstrapFactory, Component

    factory = BootstrapFactory()
    factory.init_components([
        Component.REDIS,
        Component.COZE,
    ])

    # 方式2: 直接调用初始化函数
    from infrastructure.bootstrap import init_redis, init_coze_client

    init_redis()
    init_coze_client()
"""

# Redis
from .redis import (
    init_redis,
    get_redis_client,
    get_session_store,
    is_redis_enabled,
    RedisConfig,
    register_session_store_impls,
)

# Coze
from .coze import (
    init_coze_client,
    get_coze_client,
    get_token_manager,
    get_jwt_oauth_app,
    get_workflow_id,
    get_app_id,
    refresh_token_if_needed,
    CozeConfig,
    register_token_manager_factory,
)

# Agent Auth
from .auth import (
    init_agent_auth,
    get_agent_manager,
    get_agent_token_manager,
    AgentAuthConfig,
)

# Ticket System
from .ticket import (
    init_ticket_system,
    get_ticket_store,
    get_ticket_template_store,
    get_audit_log_store,
    get_quick_reply_store,
    register_ticket_store_impls,
)

# SSE
from .sse import (
    get_sse_queues,
    get_or_create_sse_queue,
    enqueue_sse_message,
    remove_sse_queue,
)

# Scheduler
from .scheduler import (
    start_background_tasks,
    start_warmup_scheduler,
    shutdown_background_tasks,
    register_warmup_service_factory,
)

# Factory
from .factory import (
    BootstrapFactory,
    Component,
    COMPONENT_DEPENDENCIES,
    get_global_factory,
    register_component_initializer,
)

__all__ = [
    # Redis
    "init_redis",
    "get_redis_client",
    "get_session_store",
    "is_redis_enabled",
    "RedisConfig",
    "register_session_store_impls",
    # Coze
    "init_coze_client",
    "get_coze_client",
    "get_token_manager",
    "get_jwt_oauth_app",
    "get_workflow_id",
    "get_app_id",
    "refresh_token_if_needed",
    "CozeConfig",
    "register_token_manager_factory",
    # Agent Auth
    "init_agent_auth",
    "get_agent_manager",
    "get_agent_token_manager",
    "AgentAuthConfig",
    # Ticket System
    "init_ticket_system",
    "get_ticket_store",
    "get_ticket_template_store",
    "get_audit_log_store",
    "get_quick_reply_store",
    "register_ticket_store_impls",
    # SSE
    "get_sse_queues",
    "get_or_create_sse_queue",
    "enqueue_sse_message",
    "remove_sse_queue",
    # Scheduler
    "start_background_tasks",
    "start_warmup_scheduler",
    "shutdown_background_tasks",
    "register_warmup_service_factory",
    # Factory
    "BootstrapFactory",
    "Component",
    "COMPONENT_DEPENDENCIES",
    "get_global_factory",
    "register_component_initializer",
]
