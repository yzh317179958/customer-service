"""
Shopify Webhook Handler

Handles Shopify fulfillment events:
- fulfillments/create: Order shipped, register tracking with 17track
- Detects split packages (multiple fulfillments per order)
- Detects presale items (based on SKU prefix)

Shopify Fulfillment Webhook payload structure:
{
    "id": 123456789,
    "order_id": 987654321,
    "status": "success",
    "tracking_company": "Royal Mail",
    "tracking_number": "AB123456789GB",
    "tracking_url": "https://...",
    "line_items": [
        {"id": 111, "sku": "FB-C20-BK", "quantity": 1, ...}
    ],
    ...
}
"""

import logging
from typing import Dict, Any, List, Optional

from ..config import get_config, is_presale_sku, NotificationType

logger = logging.getLogger(__name__)


async def handle_fulfillment_create(
    payload: Dict[str, Any],
    shop_domain: str,
) -> Dict[str, Any]:
    """
    Handle Shopify fulfillment.create event

    This is triggered when an order is shipped (fulfillment created).

    Args:
        payload: Shopify fulfillment webhook payload
        shop_domain: Shop domain (e.g., "fiidouk.myshopify.com")

    Returns:
        Processing result with actions taken
    """
    config = get_config()
    result = {
        "fulfillment_id": payload.get("id"),
        "order_id": payload.get("order_id"),
        "actions": [],
    }

    try:
        # Extract fulfillment data
        fulfillment_id = payload.get("id")
        order_id = payload.get("order_id")
        tracking_number = payload.get("tracking_number")
        tracking_company = payload.get("tracking_company", "")
        line_items = payload.get("line_items", [])

        logger.info(
            f"Processing fulfillment: id={fulfillment_id}, "
            f"order={order_id}, tracking={tracking_number}"
        )

        # 1. Register tracking with 17track
        if tracking_number:
            await _register_tracking(
                order_id=str(order_id),
                tracking_number=tracking_number,
                carrier=tracking_company,
                shop_domain=shop_domain,
            )
            result["actions"].append("tracking_registered")

        # 2. Check for split package
        is_split = await _check_split_package(order_id, shop_domain)
        if is_split:
            result["is_split_package"] = True
            result["actions"].append("split_package_detected")
            # Send split package notification
            await _send_split_package_notification(
                order_id=str(order_id),
                tracking_number=tracking_number,
                carrier=tracking_company,
                shop_domain=shop_domain,
            )

        # 3. Check for presale items
        presale_skus = _detect_presale_items(line_items)
        if presale_skus:
            result["presale_skus"] = presale_skus
            result["actions"].append("presale_detected")
            # Send presale notification
            await _send_presale_notification(
                order_id=str(order_id),
                tracking_number=tracking_number,
                carrier=tracking_company,
                presale_skus=presale_skus,
                shop_domain=shop_domain,
            )

        result["status"] = "success"
        logger.info(f"Fulfillment processed: {result}")

    except Exception as e:
        logger.error(f"Fulfillment processing error: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def _register_tracking(
    order_id: str,
    tracking_number: str,
    carrier: str,
    shop_domain: str,
) -> bool:
    """
    Register tracking number with 17track

    Args:
        order_id: Shopify order ID
        tracking_number: Tracking number
        carrier: Carrier name
        shop_domain: Shop domain for site identification

    Returns:
        True if registration successful
    """
    try:
        from services.tracking import get_tracking_service

        service = get_tracking_service()

        # Determine site code from shop domain
        site_code = _get_site_code(shop_domain)

        # Generate order number for display
        order_number = f"#{site_code}{order_id[-5:]}" if order_id else None

        result = await service.register_order_tracking(
            order_id=order_id,
            tracking_number=tracking_number,
            carrier=carrier,
            order_number=order_number,
        )

        logger.info(
            f"Tracking registered: {tracking_number} -> order {order_id}, "
            f"success={result.get('success')}"
        )

        return result.get("success", False)

    except Exception as e:
        logger.error(f"Tracking registration failed: {e}")
        return False


async def _check_split_package(
    order_id: int,
    shop_domain: str,
) -> bool:
    """
    Check if order has multiple fulfillments (split package)

    A split package is when an order is shipped in multiple packages.
    We detect this by checking if the order already has previous fulfillments.

    Args:
        order_id: Shopify order ID
        shop_domain: Shop domain

    Returns:
        True if this is a split package scenario
    """
    try:
        # Get site code from domain
        site_code = _get_site_code(shop_domain)

        # Query Shopify for order fulfillment count
        from services.shopify import get_shopify_service

        service = get_shopify_service(site_code)
        order = await service.get_order(str(order_id))

        if order:
            fulfillments = order.get("fulfillments", [])
            # If there's more than 1 fulfillment, it's a split package
            return len(fulfillments) > 1

        return False

    except Exception as e:
        logger.error(f"Split package check failed: {e}")
        return False


def _detect_presale_items(line_items: List[Dict[str, Any]]) -> List[str]:
    """
    Detect presale items in fulfillment

    Args:
        line_items: List of line items from fulfillment

    Returns:
        List of presale SKUs found
    """
    presale_skus = []

    for item in line_items:
        sku = item.get("sku", "")
        if is_presale_sku(sku):
            presale_skus.append(sku)

    return presale_skus


def _get_site_code(shop_domain: str) -> str:
    """
    Get site code from shop domain

    Args:
        shop_domain: Shopify shop domain

    Returns:
        Site code (us, uk, eu, etc.)
    """
    domain_lower = shop_domain.lower()

    site_map = {
        "fiidofiido": "us",
        "fiidouk": "uk",
        "fiido-eu": "eu",
        "de-fiido": "de",
        "bonjour-6239": "fr",
        "fiido-it": "it",
        "fiido-es": "es",
        "fiidonl": "nl",
        "fiido-pl": "pl",
    }

    for key, code in site_map.items():
        if key in domain_lower:
            return code

    return "us"  # Default to US


async def handle_order_create(
    payload: Dict[str, Any],
    shop_domain: str,
) -> Dict[str, Any]:
    """
    Handle Shopify order.create event

    Can be used to detect presale orders at creation time.

    Args:
        payload: Shopify order webhook payload
        shop_domain: Shop domain

    Returns:
        Processing result
    """
    # This handler is optional, mainly for future use
    order_id = payload.get("id")
    logger.info(f"Order created: {order_id}")

    return {
        "order_id": order_id,
        "status": "received",
    }


async def _send_split_package_notification(
    order_id: str,
    tracking_number: str,
    carrier: str,
    shop_domain: str,
) -> bool:
    """
    Send split package notification to customer

    Args:
        order_id: Shopify order ID
        tracking_number: Tracking number
        carrier: Carrier name
        shop_domain: Shop domain

    Returns:
        True if notification sent successfully
    """
    try:
        from .notification_sender import send_split_package_notice
        from services.shopify import get_shopify_service

        site_code = _get_site_code(shop_domain)
        service = get_shopify_service(site_code)

        # Get order details
        order = await service.get_order(order_id)
        if not order:
            logger.warning(f"Order not found for split package: {order_id}")
            return False

        email = order.get("email")
        order_number = order.get("name", f"#{order_id}")
        fulfillments = order.get("fulfillments", [])

        if not email:
            logger.warning(f"No email for split package order: {order_id}")
            return False

        # Get package count
        total_packages = len(fulfillments)
        package_number = total_packages  # This fulfillment is the latest

        # Generate tracking URL
        tracking_url = _generate_tracking_url(tracking_number, carrier)

        await send_split_package_notice(
            email=email,
            order_number=order_number,
            tracking_number=tracking_number,
            carrier=carrier,
            package_number=package_number,
            total_packages=total_packages,
            tracking_url=tracking_url,
        )

        return True

    except Exception as e:
        logger.error(f"Split package notification failed: {e}")
        return False


async def _send_presale_notification(
    order_id: str,
    tracking_number: str,
    carrier: str,
    presale_skus: List[str],
    shop_domain: str,
) -> bool:
    """
    Send presale shipment notification to customer

    Args:
        order_id: Shopify order ID
        tracking_number: Tracking number
        carrier: Carrier name
        presale_skus: List of presale SKUs in this fulfillment
        shop_domain: Shop domain

    Returns:
        True if notification sent successfully
    """
    try:
        from .notification_sender import send_presale_notice
        from services.shopify import get_shopify_service

        site_code = _get_site_code(shop_domain)
        service = get_shopify_service(site_code)

        # Get order details
        order = await service.get_order(order_id)
        if not order:
            logger.warning(f"Order not found for presale: {order_id}")
            return False

        email = order.get("email")
        order_number = order.get("name", f"#{order_id}")

        if not email:
            logger.warning(f"No email for presale order: {order_id}")
            return False

        # Get product name from first presale SKU
        product_name = None
        for item in order.get("line_items", []):
            if item.get("sku") in presale_skus:
                product_name = item.get("name")
                break

        # Generate tracking URL
        tracking_url = _generate_tracking_url(tracking_number, carrier)

        await send_presale_notice(
            email=email,
            order_number=order_number,
            tracking_number=tracking_number,
            carrier=carrier,
            product_name=product_name,
            tracking_url=tracking_url,
        )

        return True

    except Exception as e:
        logger.error(f"Presale notification failed: {e}")
        return False


def _generate_tracking_url(tracking_number: str, carrier: str) -> str:
    """Generate tracking URL based on carrier"""
    carrier_lower = carrier.lower()

    # Common carrier tracking URLs
    carrier_urls = {
        "royal mail": f"https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
        "dhl": f"https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
        "ups": f"https://www.ups.com/track?tracknum={tracking_number}",
        "fedex": f"https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        "usps": f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        "yunexpress": f"https://www.yuntrack.com/Track/Detail?PackageNo={tracking_number}",
        "4px": f"https://track.4px.com/?invitecode=1001#{tracking_number}",
    }

    for key, url in carrier_urls.items():
        if key in carrier_lower:
            return url

    # Default to 17track
    return f"https://t.17track.net/en#nums={tracking_number}"
