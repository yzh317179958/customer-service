"""
17track Webhook Handler

Handles 17track tracking status update pushes:
- Delivered: Send delivery confirmation email
- Alert/Undelivered: Send exception alert email
- Status changes: Log and process

Uses services/tracking for webhook parsing and data models.
"""

import logging
from typing import Dict, Any, Optional, List

from services.tracking import (
    parse_17track_push,
    parse_17track_batch_push,
    is_delivery_event,
    is_exception_event,
    get_exception_type,
    get_tracking_service,
    WebhookEvent,
    TrackingStatus,
)

from ..config import get_config, NotificationType

logger = logging.getLogger(__name__)


async def handle_tracking_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle 17track webhook push

    Parses the webhook payload and routes to appropriate handlers
    based on the tracking status.

    Args:
        payload: 17track webhook payload

    Returns:
        Processing result with actions taken
    """
    result = {
        "event_type": payload.get("event"),
        "processed": 0,
        "actions": [],
    }

    try:
        # Parse webhook data (handles both single and batch)
        events = parse_17track_batch_push(payload)

        if not events:
            logger.warning("No events parsed from 17track webhook")
            result["status"] = "no_events"
            return result

        result["processed"] = len(events)

        # Process each event
        for event in events:
            event_result = await _process_event(event)
            if event_result.get("action"):
                result["actions"].append(event_result)

        result["status"] = "success"

    except Exception as e:
        logger.error(f"17track webhook processing error: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def _process_event(event: WebhookEvent) -> Dict[str, Any]:
    """
    Process a single tracking event

    Args:
        event: Parsed webhook event

    Returns:
        Processing result
    """
    result = {
        "tracking_number": event.tracking_number,
        "status": event.new_status.value if event.new_status else None,
    }

    try:
        # Check for delivery
        if is_delivery_event(event):
            await handle_delivered(event)
            result["action"] = NotificationType.DELIVERY_CONFIRM
            logger.info(f"Delivery event processed: {event.tracking_number}")

        # Check for exception
        elif is_exception_event(event):
            exception_type = get_exception_type(event)
            await handle_exception(event, exception_type)
            result["action"] = NotificationType.EXCEPTION_ALERT
            result["exception_type"] = exception_type
            logger.info(
                f"Exception event processed: {event.tracking_number}, "
                f"type={exception_type}"
            )

        else:
            # Regular status update - just log
            logger.debug(
                f"Status update: {event.tracking_number} -> "
                f"{event.new_status.value if event.new_status else 'unknown'}"
            )

    except Exception as e:
        logger.error(f"Event processing error: {event.tracking_number}, {e}")
        result["error"] = str(e)

    return result


async def handle_delivered(event: WebhookEvent) -> bool:
    """
    Handle delivery confirmation event

    Sends delivery confirmation email to customer.

    Args:
        event: Webhook event with Delivered status

    Returns:
        True if notification sent successfully
    """
    try:
        tracking_number = event.tracking_number
        order_id = event.order_id

        logger.info(
            f"Processing delivery: tracking={tracking_number}, order={order_id}"
        )

        # Get order details if we have order_id
        customer_email = None
        order_number = None

        if order_id:
            order_info = await _get_order_info(order_id)
            if order_info:
                customer_email = order_info.get("email")
                order_number = order_info.get("order_number")

        # Send delivery confirmation
        if customer_email:
            from .notification_sender import send_delivery_confirm

            # Extract delivery details from event
            delivery_date = None
            delivery_location = None
            if event.last_event:
                delivery_date = event.last_event.timestamp
                # Try to extract location from event message
                if event.last_event.description:
                    desc = event.last_event.description.lower()
                    if "mailbox" in desc:
                        delivery_location = "Mailbox"
                    elif "door" in desc:
                        delivery_location = "Front door"
                    elif "neighbor" in desc:
                        delivery_location = "Neighbor"

            await send_delivery_confirm(
                email=customer_email,
                order_number=order_number or f"Order #{order_id}",
                tracking_number=tracking_number,
                delivery_date=delivery_date,
                delivery_location=delivery_location,
            )

        logger.info(
            f"Delivery confirmation pending: {tracking_number} "
            f"(email={customer_email})"
        )

        return True

    except Exception as e:
        logger.error(f"Delivery handling error: {e}")
        return False


async def handle_exception(
    event: WebhookEvent,
    exception_type: str,
) -> bool:
    """
    Handle exception/alert event

    Sends exception alert email to customer and/or support team.

    Args:
        event: Webhook event with Alert/Undelivered status
        exception_type: Type of exception (lost, damaged, address_issue, etc.)

    Returns:
        True if notification sent successfully
    """
    try:
        tracking_number = event.tracking_number
        order_id = event.order_id

        logger.info(
            f"Processing exception: tracking={tracking_number}, "
            f"type={exception_type}, order={order_id}"
        )

        # Get order details
        customer_email = None
        order_number = None

        if order_id:
            order_info = await _get_order_info(order_id)
            if order_info:
                customer_email = order_info.get("email")
                order_number = order_info.get("order_number")

        # Send exception alert
        if customer_email:
            from .notification_sender import send_exception_alert

            # Get exception message from event
            exception_message = None
            if event.last_event and event.last_event.description:
                exception_message = event.last_event.description

            # Generate tracking URL
            tracking_url = f"https://t.17track.net/en#nums={tracking_number}"

            await send_exception_alert(
                email=customer_email,
                order_number=order_number or f"Order #{order_id}",
                tracking_number=tracking_number,
                exception_type=exception_type,
                exception_message=exception_message,
                tracking_url=tracking_url,
            )

        logger.info(
            f"Exception alert pending: {tracking_number} "
            f"(type={exception_type}, email={customer_email})"
        )

        return True

    except Exception as e:
        logger.error(f"Exception handling error: {e}")
        return False


async def _get_order_info(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Get order information from Shopify

    Args:
        order_id: Order ID

    Returns:
        Order info dict with email, order_number, etc.
    """
    try:
        # Try to find the order across all sites
        # In production, we should have site info from the tracking registration
        from services.shopify import get_shopify_service

        # Try UK first (most common)
        for site in ["uk", "us", "eu", "de"]:
            try:
                service = get_shopify_service(site)
                order = await service.get_order_by_id(order_id)
                if order:
                    return {
                        "email": order.get("email"),
                        "order_number": order.get("name"),  # e.g., "#UK12345"
                        "site": site,
                    }
            except Exception:
                continue

        return None

    except Exception as e:
        logger.error(f"Failed to get order info: {e}")
        return None


async def handle_status_change(
    tracking_number: str,
    old_status: Optional[TrackingStatus],
    new_status: TrackingStatus,
) -> None:
    """
    Handle general status change

    This can be used for logging, analytics, or triggering
    other actions based on status transitions.

    Args:
        tracking_number: Tracking number
        old_status: Previous status (if known)
        new_status: New status
    """
    logger.info(
        f"Status change: {tracking_number} "
        f"{old_status.value if old_status else '?'} -> {new_status.value}"
    )

    # Could add:
    # - Analytics tracking
    # - Status history recording
    # - Custom business logic
