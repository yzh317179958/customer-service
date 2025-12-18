"""
Shopify 多站点配置

定义所有支持的 Shopify 店铺站点配置。
每个站点有独立的域名、Access Token 和缓存前缀。

遵循 CLAUDE.md 规范：
- 所有敏感配置从环境变量读取
- 使用统一的配置结构
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class SiteCode(str, Enum):
    """站点代码枚举"""
    US = "us"
    UK = "uk"
    EU = "eu"
    DE = "de"
    FR = "fr"
    IT = "it"
    ES = "es"
    NL = "nl"
    PL = "pl"


@dataclass
class ShopifySiteConfig:
    """站点配置数据类"""
    code: str                    # 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)
    name: str                    # 站点名称
    shop_domain: str             # 店铺域名
    access_token: str            # Admin API Access Token
    api_version: str             # API 版本
    currency: str                # 默认货币
    cache_prefix: str            # 缓存键前缀

    @property
    def base_url(self) -> str:
        """获取 API 基础 URL"""
        return f"https://{self.shop_domain}/admin/api/{self.api_version}"


# 站点默认配置（域名）
SITE_DEFAULTS = {
    SiteCode.US: {
        "name": "Fiido US",
        "shop_domain": "fiidofiido.myshopify.com",
        "currency": "USD",
    },
    SiteCode.UK: {
        "name": "Fiido UK",
        "shop_domain": "fiidouk.myshopify.com",
        "currency": "GBP",
    },
    SiteCode.EU: {
        "name": "Fiido EU",
        "shop_domain": "fiido-eu.myshopify.com",
        "currency": "EUR",
    },
    SiteCode.DE: {
        "name": "Fiido DE",
        "shop_domain": "de-fiido.myshopify.com",
        "currency": "EUR",
    },
    SiteCode.FR: {
        "name": "Fiido FR",
        "shop_domain": "bonjour-6239.myshopify.com",
        "currency": "EUR",
    },
    SiteCode.IT: {
        "name": "Fiido IT",
        "shop_domain": "fiido-it.myshopify.com",
        "currency": "EUR",
    },
    SiteCode.ES: {
        "name": "Fiido ES",
        "shop_domain": "fiido-es.myshopify.com",
        "currency": "EUR",
    },
    SiteCode.NL: {
        "name": "Fiido NL",
        "shop_domain": "fiidonl.myshopify.com",
        "currency": "EUR",
    },
    SiteCode.PL: {
        "name": "Fiido PL",
        "shop_domain": "fiido-pl.myshopify.com",
        "currency": "PLN",
    },
}


def get_site_config(site_code: str) -> Optional[ShopifySiteConfig]:
    """
    获取站点配置

    Args:
        site_code: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)

    Returns:
        站点配置对象，如果站点不存在或未配置 Token 则返回 None
    """
    # 标准化站点代码
    code = site_code.lower().strip()

    try:
        site_enum = SiteCode(code)
    except ValueError:
        return None

    defaults = SITE_DEFAULTS.get(site_enum)
    if not defaults:
        return None

    # 从环境变量读取 Token（必需）
    env_key = f"SHOPIFY_{code.upper()}_ACCESS_TOKEN"
    access_token = os.getenv(env_key, "")

    if not access_token:
        return None

    # 从环境变量读取可选配置
    api_version = os.getenv(f"SHOPIFY_{code.upper()}_API_VERSION", "2024-01")
    shop_domain = os.getenv(f"SHOPIFY_{code.upper()}_SHOP_DOMAIN", defaults["shop_domain"])

    return ShopifySiteConfig(
        code=code,
        name=defaults["name"],
        shop_domain=shop_domain,
        access_token=access_token,
        api_version=api_version,
        currency=defaults["currency"],
        cache_prefix=f"shopify:{code}"
    )


def get_all_configured_sites() -> Dict[str, ShopifySiteConfig]:
    """
    获取所有已配置的站点

    Returns:
        站点代码到配置的映射字典
    """
    sites = {}
    for site_enum in SiteCode:
        config = get_site_config(site_enum.value)
        if config:
            sites[site_enum.value] = config
    return sites


def is_site_configured(site_code: str) -> bool:
    """
    检查站点是否已配置

    Args:
        site_code: 站点代码

    Returns:
        是否已配置
    """
    return get_site_config(site_code) is not None


# 站点代码到订单号前缀的映射（用于自动识别）
ORDER_PREFIX_TO_SITE = {
    "US": SiteCode.US,
    "UK": SiteCode.UK,
    "EU": SiteCode.EU,
    "DE": SiteCode.DE,
    "FR": SiteCode.FR,
    "IT": SiteCode.IT,
    "ES": SiteCode.ES,
    "NL": SiteCode.NL,
    "PL": SiteCode.PL,
}


def detect_site_from_order_number(order_number: str) -> Optional[str]:
    """
    从订单号自动检测站点

    订单号格式通常为: #UK22080, UK22080, #DE12345 等

    Args:
        order_number: 订单号

    Returns:
        站点代码，如果无法识别返回 None
    """
    # 清理订单号
    clean = order_number.strip().lstrip("#").upper()

    # 尝试匹配前缀
    for prefix, site_enum in ORDER_PREFIX_TO_SITE.items():
        if clean.startswith(prefix):
            return site_enum.value

    return None
