"""
Notification Sender

Renders email templates and sends notifications via email service.

Functions:
- send_split_package_notice: Split package shipment notification
- send_presale_notice: Presale item shipped notification
- send_exception_alert: Shipping exception alert
- send_delivery_confirm: Delivery confirmation

Uses Jinja2 for template rendering and services/email for sending.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.email import get_email_service

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Jinja2 environment
_jinja_env: Optional[Environment] = None


def get_jinja_env() -> Environment:
    """Get Jinja2 environment with templates loaded"""
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )
    return _jinja_env


def render_template(template_name: str, **kwargs) -> str:
    """
    Render an email template with context

    Args:
        template_name: Template filename (e.g., "delivery_confirm.html")
        **kwargs: Template context variables

    Returns:
        Rendered HTML string
    """
    env = get_jinja_env()
    template = env.get_template(template_name)

    # Add common context
    context = {
        "year": datetime.now().year,
        **kwargs,
    }

    return template.render(**context)


async def send_split_package_notice(
    email: str,
    order_number: str,
    tracking_number: str,
    carrier: str,
    package_number: int,
    total_packages: int,
    items: Optional[List[Dict[str, Any]]] = None,
    tracking_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send split package notification

    When an order is shipped in multiple packages, notify customer
    about each package separately.

    Args:
        email: Customer email
        order_number: Order number (e.g., "#UK12345")
        tracking_number: Tracking number for this package
        carrier: Carrier name
        package_number: Which package this is (1, 2, 3...)
        total_packages: Total number of packages
        items: List of items in this package
        tracking_url: Tracking URL

    Returns:
        Send result from email service
    """
    try:
        html_content = render_template(
            "split_package.html",
            order_number=order_number,
            tracking_number=tracking_number,
            carrier=carrier,
            package_number=package_number,
            total_packages=total_packages,
            items=items or [],
            tracking_url=tracking_url,
        )

        subject = f"Your Order {order_number} Update - Package {package_number} of {total_packages}"

        service = get_email_service()
        result = service.send_email(
            subject=subject,
            html_content=html_content,
            recipients=[email],
            email_type="notification",
            related_id=order_number,
            metadata={
                "notification_type": "split_package",
                "tracking_number": tracking_number,
                "package_number": package_number,
                "total_packages": total_packages,
            },
        )

        if result["success"]:
            logger.info(
                f"Split package notification sent: {order_number} "
                f"pkg {package_number}/{total_packages} -> {email}"
            )
        else:
            logger.error(
                f"Split package notification failed: {order_number}, "
                f"error={result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Split package notification error: {e}")
        return {"success": False, "error": str(e)}


async def send_presale_notice(
    email: str,
    order_number: str,
    tracking_number: str,
    carrier: str,
    product_name: Optional[str] = None,
    estimated_delivery: Optional[str] = None,
    tracking_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send presale shipment notification

    When a presale/preorder item is finally shipped, send special
    notification thanking customer for waiting.

    Args:
        email: Customer email
        order_number: Order number
        tracking_number: Tracking number
        carrier: Carrier name
        product_name: Product name (if available)
        estimated_delivery: Estimated delivery time
        tracking_url: Tracking URL

    Returns:
        Send result from email service
    """
    try:
        html_content = render_template(
            "presale_shipped.html",
            order_number=order_number,
            tracking_number=tracking_number,
            carrier=carrier,
            product_name=product_name,
            estimated_delivery=estimated_delivery,
            tracking_url=tracking_url,
        )

        subject = f"Great News - Your Pre-order {order_number} Has Shipped!"

        service = get_email_service()
        result = service.send_email(
            subject=subject,
            html_content=html_content,
            recipients=[email],
            email_type="notification",
            related_id=order_number,
            metadata={
                "notification_type": "presale_shipped",
                "tracking_number": tracking_number,
                "product_name": product_name,
            },
        )

        if result["success"]:
            logger.info(
                f"Presale notification sent: {order_number} -> {email}"
            )
        else:
            logger.error(
                f"Presale notification failed: {order_number}, "
                f"error={result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Presale notification error: {e}")
        return {"success": False, "error": str(e)}


async def send_exception_alert(
    email: str,
    order_number: str,
    tracking_number: str,
    exception_type: str,
    exception_message: Optional[str] = None,
    tracking_url: Optional[str] = None,
    support_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send shipping exception alert

    When tracking shows an exception (lost, damaged, address issue, etc.),
    notify customer with appropriate guidance.

    Args:
        email: Customer email
        order_number: Order number
        tracking_number: Tracking number
        exception_type: Type of exception (lost, damaged, address_issue, etc.)
        exception_message: Exception message from carrier
        tracking_url: Tracking URL
        support_url: Customer support URL

    Returns:
        Send result from email service
    """
    try:
        # Map exception types to user-friendly messages
        exception_messages = {
            "lost": "Your package may be lost in transit. We are investigating.",
            "damaged": "Your package was reported as damaged during transit.",
            "address_issue": "There is a problem with the delivery address.",
            "customs_issue": "Your package is held at customs clearance.",
            "no_one_home": "Delivery was attempted but no one was available.",
            "refused": "The package was refused at delivery.",
            "returned": "Your package is being returned to sender.",
        }

        message = exception_message or exception_messages.get(
            exception_type, "There is an issue with your delivery."
        )

        html_content = render_template(
            "exception_alert.html",
            order_number=order_number,
            tracking_number=tracking_number,
            exception_type=exception_type,
            exception_message=message,
            tracking_url=tracking_url,
            support_url=support_url,
        )

        # Critical exceptions get different subject
        if exception_type in ["lost", "damaged"]:
            subject = f"Important: Issue with Your Order {order_number}"
        else:
            subject = f"Shipping Update - Order {order_number}"

        service = get_email_service()
        result = service.send_email(
            subject=subject,
            html_content=html_content,
            recipients=[email],
            email_type="notification",
            related_id=order_number,
            metadata={
                "notification_type": "exception_alert",
                "tracking_number": tracking_number,
                "exception_type": exception_type,
            },
        )

        if result["success"]:
            logger.info(
                f"Exception alert sent: {order_number} "
                f"type={exception_type} -> {email}"
            )
        else:
            logger.error(
                f"Exception alert failed: {order_number}, "
                f"error={result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Exception alert error: {e}")
        return {"success": False, "error": str(e)}


async def send_delivery_confirm(
    email: str,
    order_number: str,
    tracking_number: str,
    delivery_date: Optional[str] = None,
    delivery_location: Optional[str] = None,
    review_url: Optional[str] = None,
    support_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send delivery confirmation

    When package is delivered, send confirmation email with
    review request and support links.

    Args:
        email: Customer email
        order_number: Order number
        tracking_number: Tracking number
        delivery_date: Delivery date/time
        delivery_location: Where the package was left
        review_url: Product review URL
        support_url: Customer support URL

    Returns:
        Send result from email service
    """
    try:
        # Format delivery date
        if not delivery_date:
            delivery_date = datetime.now().strftime("%B %d, %Y")

        html_content = render_template(
            "delivery_confirm.html",
            order_number=order_number,
            tracking_number=tracking_number,
            delivery_date=delivery_date,
            delivery_location=delivery_location,
            review_url=review_url,
            support_url=support_url,
        )

        subject = f"Your Order {order_number} Has Been Delivered!"

        service = get_email_service()
        result = service.send_email(
            subject=subject,
            html_content=html_content,
            recipients=[email],
            email_type="notification",
            related_id=order_number,
            metadata={
                "notification_type": "delivery_confirm",
                "tracking_number": tracking_number,
                "delivery_date": delivery_date,
            },
        )

        if result["success"]:
            logger.info(
                f"Delivery confirmation sent: {order_number} -> {email}"
            )
        else:
            logger.error(
                f"Delivery confirmation failed: {order_number}, "
                f"error={result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Delivery confirmation error: {e}")
        return {"success": False, "error": str(e)}


# Convenience function to check if templates exist
def check_templates() -> Dict[str, bool]:
    """Check if all required templates exist"""
    templates = [
        "split_package.html",
        "presale_shipped.html",
        "exception_alert.html",
        "delivery_confirm.html",
    ]

    return {
        template: (TEMPLATE_DIR / template).exists()
        for template in templates
    }
