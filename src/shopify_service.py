"""
兼容层 - 重导出新架构模块
"""
from services.shopify.service import (
    ShopifyService,
    get_shopify_service,
    search_order_across_sites,
    search_orders_by_email_across_sites,
    get_all_sites_health,
    get_configured_sites_list,
)

__all__ = [
    "ShopifyService",
    "get_shopify_service",
    "search_order_across_sites",
    "search_orders_by_email_across_sites",
    "get_all_sites_health",
    "get_configured_sites_list",
]
