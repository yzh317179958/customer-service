"""
Notification Module (products/notification)

Provides logistics notification features:
- Split package notification
- Presale shipment notification
- Exception alert
- Delivery confirmation

Usage:
    # Standalone mode
    uvicorn products.notification.main:app --port 8001

    # Full stack mode (via backend.py)
    from products.notification.routes import router
"""

from .config import (
    NotificationConfig,
    NotificationType,
    get_config,
    get_carrier_timeout,
    is_presale_sku,
)

__all__ = [
    "NotificationConfig",
    "NotificationType",
    "get_config",
    "get_carrier_timeout",
    "is_presale_sku",
]
