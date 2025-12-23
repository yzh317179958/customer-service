# -*- coding: utf-8 -*-
"""
基础设施 - 组件工厂模块

提供按需初始化组件的工厂模式，支持：
- 组件枚举定义
- 依赖关系管理
- 按需初始化
"""

from enum import Enum
from typing import List, Set, Dict, Any, Callable


class Component(str, Enum):
    """可初始化的组件枚举"""
    REDIS = "redis"
    DATABASE = "database"  # PostgreSQL 数据库
    COZE = "coze"
    REGULATOR = "regulator"
    AGENT_AUTH = "agent_auth"
    TICKET = "ticket"
    SSE = "sse"
    SCHEDULER = "scheduler"


# 组件依赖关系
COMPONENT_DEPENDENCIES: Dict[Component, List[Component]] = {
    Component.REDIS: [],
    Component.DATABASE: [],  # 无依赖
    Component.COZE: [],
    Component.REGULATOR: [],
    Component.AGENT_AUTH: [Component.REDIS],
    Component.TICKET: [Component.REDIS],
    Component.SSE: [],
    Component.SCHEDULER: [],
}


class BootstrapFactory:
    """
    启动引导工厂

    根据产品需求按需初始化组件，自动处理依赖关系

    使用示例:
        factory = BootstrapFactory()
        factory.init_components([
            Component.REDIS,
            Component.COZE,
            Component.REGULATOR,
        ])
    """

    def __init__(self):
        self._initialized: Set[Component] = set()
        self._instances: Dict[Component, Any] = {}

    def init_components(self, components: List[Component]) -> Dict[Component, Any]:
        """
        按依赖顺序初始化组件

        Args:
            components: 需要初始化的组件列表

        Returns:
            初始化后的组件实例字典
        """
        # 解析依赖，获取正确的初始化顺序
        ordered = self._resolve_dependencies(components)

        for component in ordered:
            if component not in self._initialized:
                self._init_component(component)
                self._initialized.add(component)

        return self._instances

    def _resolve_dependencies(self, components: List[Component]) -> List[Component]:
        """拓扑排序解析依赖"""
        result = []
        visited = set()

        def dfs(comp: Component):
            if comp in visited:
                return
            visited.add(comp)
            for dep in COMPONENT_DEPENDENCIES.get(comp, []):
                dfs(dep)
            result.append(comp)

        for comp in components:
            dfs(comp)

        return result

    def _init_component(self, component: Component):
        """初始化单个组件"""
        initializer = _component_initializers.get(component)
        if initializer:
            self._instances[component] = initializer()
            return

        if component == Component.REDIS:
            from .redis import init_redis
            self._instances[component] = init_redis()

        elif component == Component.DATABASE:
            from .database import init_database
            self._instances[component] = init_database()

        elif component == Component.COZE:
            from .coze import init_coze_client
            self._instances[component] = init_coze_client()

        elif component == Component.AGENT_AUTH:
            from .auth import init_agent_auth
            from .redis import get_session_store
            manager, token_manager = init_agent_auth(get_session_store())
            self._instances[component] = {
                "agent_manager": manager,
                "agent_token_manager": token_manager
            }

        elif component == Component.TICKET:
            from .ticket import init_ticket_system
            from .redis import get_redis_client
            stores = init_ticket_system(get_redis_client())
            self._instances[component] = stores

        elif component == Component.SSE:
            from .sse import get_sse_queues
            # 初始化 Redis SSE 管理器（跨进程通信）
            import os
            if os.getenv("USE_REDIS_SSE", "true").lower() == "true":
                from .redis_sse import init_redis_sse
                init_redis_sse()
            self._instances[component] = get_sse_queues()

        elif component == Component.SCHEDULER:
            # 调度器需要在其他组件初始化后启动
            self._instances[component] = None

    def get_instance(self, component: Component) -> Any:
        """获取已初始化的组件实例"""
        return self._instances.get(component)

    def start_scheduler(
        self,
        ticket_store: Any = None,
        agent_manager: Any = None,
        sse_queues: dict = None,
        include_warmup: bool = True
    ):
        """
        启动后台调度器

        Args:
            ticket_store: 工单存储
            agent_manager: 坐席管理器
            sse_queues: SSE 队列
            include_warmup: 是否包含预热调度
        """
        from .scheduler import start_background_tasks, start_warmup_scheduler

        start_background_tasks(ticket_store, agent_manager, sse_queues)

        if include_warmup:
            start_warmup_scheduler()

    @property
    def initialized_components(self) -> Set[Component]:
        """获取已初始化的组件集合"""
        return self._initialized.copy()

    def is_initialized(self, component: Component) -> bool:
        """检查组件是否已初始化"""
        return component in self._initialized


# 全局工厂实例（可选）
_global_factory: BootstrapFactory = None


def get_global_factory() -> BootstrapFactory:
    """获取全局工厂实例"""
    global _global_factory
    if _global_factory is None:
        _global_factory = BootstrapFactory()
    return _global_factory


def reset_global_factory():
    """重置全局工厂（仅用于测试）"""
    global _global_factory
    _global_factory = None


ComponentInitializer = Callable[[], Any]
_component_initializers: Dict[Component, ComponentInitializer] = {}


def register_component_initializer(
    component: Component,
    initializer: ComponentInitializer
) -> None:
    """
    注册自定义组件初始化器
    """
    _component_initializers[component] = initializer
