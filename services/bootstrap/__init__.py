"""
Services 层 Bootstrap 注册模块

负责在应用启动前，将服务层实现注册到基础设施层暴露的
依赖注入接口中，确保基础设施模块无需直接 import services。
"""

from infrastructure.bootstrap import Component
from infrastructure.bootstrap import register_component_initializer
from infrastructure.bootstrap import (
    register_session_store_impls,
    register_ticket_store_impls,
    register_token_manager_factory,
    register_warmup_service_factory,
)

from services.session.redis_store import RedisSessionStore
from services.session.state import InMemorySessionStore
from services.ticket.store import TicketStore
from services.ticket.template import TicketTemplateStore
from services.ticket.audit import AuditLogStore
from services.session.quick_reply_store import QuickReplyStore
from services.coze.token_manager import OAuthTokenManager
from services.session.regulator import Regulator, RegulatorConfig
from services.shopify.warmup import get_warmup_service


def _init_regulator():
    """初始化监管引擎（供 BootstrapFactory 调用）"""
    try:
        config = RegulatorConfig()
        regulator = Regulator(config)
        print("[Bootstrap] ✅ Regulator 监管引擎初始化成功")
        print(f"   关键词: {len(config.keywords)}个")
        print(f"   失败阈值: {config.fail_threshold}")
        return regulator
    except Exception as exc:
        print(f"[Bootstrap] ⚠️ Regulator 初始化失败: {exc}")
        return None


# 注册依赖实现
register_session_store_impls(RedisSessionStore, InMemorySessionStore)
register_ticket_store_impls(TicketStore, TicketTemplateStore, AuditLogStore, QuickReplyStore)
register_token_manager_factory(OAuthTokenManager.from_env)
register_component_initializer(Component.REGULATOR, _init_regulator)
register_warmup_service_factory(get_warmup_service)

# 只要导入该模块，即可完成注册
