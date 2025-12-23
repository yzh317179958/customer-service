"""
Notification Handlers

Handlers for processing notifications:
- shopify_handler: Shopify Webhook processing (fulfillment events)
- tracking_handler: 17track push processing (status updates)
- notification_sender: Email notification sending
"""

from .shopify_handler import handle_fulfillment_create, handle_order_create
from .tracking_handler import handle_tracking_update, handle_status_change
from .notification_sender import (
    send_split_package_notice,
    send_presale_notice,
    send_exception_alert,
    send_delivery_confirm,
    render_template,
    check_templates,
)

__all__ = [
    # Shopify handlers
    "handle_fulfillment_create",
    "handle_order_create",
    # 17track handlers
    "handle_tracking_update",
    "handle_status_change",
    # Notification senders
    "send_split_package_notice",
    "send_presale_notice",
    "send_exception_alert",
    "send_delivery_confirm",
    "render_template",
    "check_templates",
]
