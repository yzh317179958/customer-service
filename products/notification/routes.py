"""
Webhook Routes

Defines API endpoints for receiving webhooks from:
- Shopify: Fulfillment events (order shipped)
- 17track: Tracking status updates

Endpoints:
    POST /webhook/shopify  - Shopify fulfillment webhook
    POST /webhook/17track  - 17track status push
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, Response, Header, HTTPException

from .config import get_config
from services.tracking import verify_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/shopify")
async def shopify_webhook(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-SHA256"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
):
    """
    Shopify Webhook endpoint

    Receives fulfillment events when orders are shipped.
    Triggers:
    - Split package notification (if order has multiple fulfillments)
    - Presale shipment notification (if SKU matches presale pattern)
    - Tracking registration with 17track

    Headers:
        X-Shopify-Topic: Event type (e.g., "fulfillments/create")
        X-Shopify-Hmac-SHA256: Request signature
        X-Shopify-Shop-Domain: Shop domain
    """
    config = get_config()

    if not config.enabled:
        logger.debug("Notification module disabled, ignoring Shopify webhook")
        return {"status": "disabled"}

    try:
        payload = await request.json()
        logger.info(
            f"Shopify webhook received: topic={x_shopify_topic}, "
            f"shop={x_shopify_shop_domain}"
        )

        # Route to appropriate handler based on topic
        if x_shopify_topic == "fulfillments/create":
            from .handlers.shopify_handler import handle_fulfillment_create
            result = await handle_fulfillment_create(payload, x_shopify_shop_domain or "")
            return {"status": "processed", "topic": x_shopify_topic, "result": result}

        elif x_shopify_topic == "orders/create":
            from .handlers.shopify_handler import handle_order_create
            result = await handle_order_create(payload, x_shopify_shop_domain or "")
            return {"status": "processed", "topic": x_shopify_topic, "result": result}

        else:
            logger.debug(f"Unhandled Shopify topic: {x_shopify_topic}")
            return {"status": "ignored", "topic": x_shopify_topic}

    except Exception as e:
        logger.error(f"Shopify webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/17track")
async def track17_webhook(
    request: Request,
    x_17track_signature: str = Header(None, alias="X-17track-Signature"),
):
    """
    17track Webhook endpoint

    Receives tracking status updates.
    Triggers:
    - Delivery confirmation (status=Delivered)
    - Exception alert (status=Alert, Undelivered)

    Headers:
        X-17track-Signature: HMAC-SHA256 signature
    """
    config = get_config()

    if not config.enabled:
        logger.debug("Notification module disabled, ignoring 17track webhook")
        return {"status": "disabled"}

    try:
        # Get raw body for signature verification
        body = await request.body()

        # Verify signature
        if config.webhook_secret:
            if not verify_webhook_signature(body, x_17track_signature or ""):
                logger.warning("17track webhook signature verification failed")
                raise HTTPException(status_code=401, detail="Invalid signature")

        payload = await request.json()
        logger.info(f"17track webhook received: event={payload.get('event')}")

        # Process tracking update
        from .handlers.tracking_handler import handle_tracking_update
        result = await handle_tracking_update(payload)

        return {"status": "processed", "event": payload.get("event"), "result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"17track webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health():
    """Webhook endpoint health check"""
    config = get_config()
    return {
        "status": "healthy",
        "enabled": config.enabled,
        "endpoints": ["/webhook/shopify", "/webhook/17track"],
    }
