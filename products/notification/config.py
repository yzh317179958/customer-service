"""
物流通知模块配置

管理通知相关的配置项，包括：
- 邮件发送配置
- 异常监控阈值
- 承运商超时规则
"""

import os
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class NotificationConfig:
    """通知模块配置"""

    # 模块开关
    enabled: bool = False

    # 邮件发送
    email_from: str = "noreply@fiido.com"
    email_from_name: str = "Fiido Support"

    # Webhook 配置
    webhook_secret: str = ""

    # 异常监控阈值（天）
    overseas_warehouse_timeout: int = 7  # 海外仓超时天数
    china_warehouse_timeout: int = 12    # 中国仓超时天数

    @classmethod
    def from_env(cls) -> "NotificationConfig":
        """从环境变量加载配置"""
        return cls(
            enabled=os.getenv("ENABLE_NOTIFICATION", "false").lower() == "true",
            email_from=os.getenv("NOTIFICATION_EMAIL_FROM", "noreply@fiido.com"),
            email_from_name=os.getenv("NOTIFICATION_EMAIL_FROM_NAME", "Fiido Support"),
            webhook_secret=os.getenv("TRACK17_WEBHOOK_SECRET", ""),
            overseas_warehouse_timeout=int(os.getenv("NOTIFICATION_OVERSEAS_TIMEOUT", "7")),
            china_warehouse_timeout=int(os.getenv("NOTIFICATION_CHINA_TIMEOUT", "12")),
        )


# 承运商分类
OVERSEAS_CARRIERS = [
    "royal mail", "royalmail", "dpd", "dpd uk", "hermes", "evri",
    "yodel", "parcelforce", "dhl", "ups", "fedex", "tnt",
]

CHINA_CARRIERS = [
    "yunexpress", "yanwen", "4px", "sf express", "cne express",
    "china post", "ems",
]


def get_carrier_timeout(carrier: str) -> int:
    """
    根据承运商获取超时阈值

    Args:
        carrier: 承运商名称

    Returns:
        超时天数
    """
    config = get_config()
    carrier_lower = carrier.lower().strip()

    if carrier_lower in OVERSEAS_CARRIERS:
        return config.overseas_warehouse_timeout
    elif carrier_lower in CHINA_CARRIERS:
        return config.china_warehouse_timeout
    else:
        # 默认使用海外仓阈值
        return config.overseas_warehouse_timeout


# 预售商品 SKU 前缀（用于识别预售商品）
PRESALE_SKU_PREFIXES: List[str] = [
    "PRE-",
    "PRESALE-",
    "PO-",  # Pre-order
]


def is_presale_sku(sku: str) -> bool:
    """
    判断是否为预售商品 SKU

    Args:
        sku: 商品 SKU

    Returns:
        是否为预售商品
    """
    if not sku:
        return False
    sku_upper = sku.upper()
    return any(sku_upper.startswith(prefix) for prefix in PRESALE_SKU_PREFIXES)


# 通知类型
class NotificationType:
    """通知类型常量"""

    SPLIT_PACKAGE = "split_package"       # 拆包裹通知
    PRESALE_SHIPPED = "presale_shipped"   # 预售发货通知
    EXCEPTION_ALERT = "exception_alert"   # 异常告警
    DELIVERY_CONFIRM = "delivery_confirm" # 签收确认


# 全局配置实例
_config: NotificationConfig = None


def get_config() -> NotificationConfig:
    """获取配置实例"""
    global _config
    if _config is None:
        _config = NotificationConfig.from_env()
    return _config


def reload_config():
    """重新加载配置"""
    global _config
    _config = NotificationConfig.from_env()
