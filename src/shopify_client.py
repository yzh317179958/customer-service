"""
兼容层 - 重导出新架构模块
"""
from services.shopify.client import (
    ShopifyClient,
    ShopifyOrderSummary,
    ShopifyOrderDetail,
    ShopifyAPIError,
    get_shopify_client,
    ERROR_CODES,
    ShopifyAddress,
    ShopifyLineItem,
    ShopifyFulfillment,
)

__all__ = [
    "ShopifyClient",
    "ShopifyOrderSummary",
    "ShopifyOrderDetail",
    "ShopifyAPIError",
    "get_shopify_client",
    "ERROR_CODES",
    "ShopifyAddress",
    "ShopifyLineItem",
    "ShopifyFulfillment",
]
