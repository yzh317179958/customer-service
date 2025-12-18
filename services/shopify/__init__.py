"""
Shopify service module

Provides multi-site order query, tracking, and caching
"""

from services.shopify.client import (
    ShopifyClient,
    ShopifyOrderSummary,
    ShopifyOrderDetail,
    ShopifyAPIError,
    get_shopify_client,
    ERROR_CODES,
)
from services.shopify.service import (
    ShopifyService,
    get_shopify_service,
    search_order_across_sites,
    search_orders_by_email_across_sites,
    get_all_sites_health,
    get_configured_sites_list,
)
from services.shopify.cache import ShopifyCache, get_shopify_cache
from services.shopify.sites import (
    ShopifySiteConfig,
    get_site_config,
    get_all_configured_sites,
    detect_site_from_order_number,
    SiteCode,
)
from services.shopify.tracking import enrich_tracking_data

__all__ = [
    "ShopifyClient",
    "ShopifyOrderSummary",
    "ShopifyOrderDetail",
    "ShopifyAPIError",
    "get_shopify_client",
    "ERROR_CODES",
    "ShopifyService",
    "get_shopify_service",
    "search_order_across_sites",
    "search_orders_by_email_across_sites",
    "get_all_sites_health",
    "get_configured_sites_list",
    "ShopifyCache",
    "get_shopify_cache",
    "ShopifySiteConfig",
    "get_site_config",
    "get_all_configured_sites",
    "detect_site_from_order_number",
    "SiteCode",
    "enrich_tracking_data",
]
