"""
兼容层 - 重导出新架构模块
"""
from services.shopify.sites import (
    SiteCode,
    ShopifySiteConfig,
    get_site_config,
    get_all_configured_sites,
    detect_site_from_order_number,
)

__all__ = [
    "SiteCode",
    "ShopifySiteConfig",
    "get_site_config",
    "get_all_configured_sites",
    "detect_site_from_order_number",
]
