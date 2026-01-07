"""
坐席工作台 - API 路由

路由前缀: /api
端点分类:
- /agent/* - 坐席认证与状态
- /sessions/* - 会话管理
- /tickets/* - 工单系统
- /quick-replies/* - 快捷回复
- /templates/* - 模板管理
- /agents/* - 坐席管理（Admin）
- /assist-requests/* - 协助请求
- /shopify/* - Shopify 订单查询
- /warmup/* - 缓存预热管理
- /cdn/* - CDN 健康检查
- /customers/* - 客户信息
- /admin/* - 管理员操作
"""

from fastapi import APIRouter

# Create main router
router = APIRouter(tags=["Agent Workbench"])

# Import sub-routers
from products.agent_workbench.handlers.auth import router as auth_router
from products.agent_workbench.handlers.sessions import router as sessions_router
from products.agent_workbench.handlers.tickets import router as tickets_router
from products.agent_workbench.handlers.quick_replies import router as quick_replies_router
from products.agent_workbench.handlers.templates import router as templates_router
from products.agent_workbench.handlers.agents import router as agents_router
from products.agent_workbench.handlers.assist_requests import router as assist_requests_router
from products.agent_workbench.handlers.misc import router as misc_router
from products.agent_workbench.handlers.shopify import router as shopify_router
from products.agent_workbench.handlers.warmup import router as warmup_router
from products.agent_workbench.handlers.cdn import router as cdn_router
from products.agent_workbench.handlers.history import router as history_router

# Register sub-routers
router.include_router(auth_router)
router.include_router(sessions_router)
router.include_router(tickets_router)
router.include_router(quick_replies_router)
router.include_router(templates_router)
router.include_router(agents_router)
router.include_router(assist_requests_router)
router.include_router(misc_router)
router.include_router(shopify_router)
router.include_router(warmup_router)
router.include_router(cdn_router)
router.include_router(history_router)
