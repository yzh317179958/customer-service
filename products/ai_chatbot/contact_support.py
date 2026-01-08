"""
AI Chatbot - Contact Support (contact-only manual handoff)

This module centralizes:
- the feature flag controlling whether the future manual-handoff flow is enabled
- the default (English) contact message shown to end users when they request a human
"""

from __future__ import annotations

import os


ENABLE_MANUAL_HANDOFF_ENV = "ENABLE_MANUAL_HANDOFF"


def is_manual_handoff_enabled() -> bool:
    """
    Feature flag for the future human-handoff workflow.

    Default: disabled (false). When disabled, callers should keep AI responding and only show
    contact info (no status transition, no pending_manual/manual_live flow).
    """
    return os.getenv(ENABLE_MANUAL_HANDOFF_ENV, "false").strip().lower() in {"1", "true", "yes", "y", "on"}


def get_contact_support_message(locale: str | None = None) -> str:
    """
    Return the end-user contact message.

    Default locale is English. Chinese can be added later if needed.
    """
    normalized = (locale or "en").strip().lower()
    if normalized.startswith("zh"):
        return (
            "您可以通过以下方式联系我们：\n"
            "邮箱：service@fiido.com\n"
            "电话：(852) 56216918（服务时间：周一至周五，上午9点至晚上10点，GMT+8）\n"
            "\n"
            "祝您骑行愉快!"
        )

    return (
        "You can reach our support team via:\n"
        "Email: service@fiido.com\n"
        "Phone: (852) 56216918 (Service hours: Monday–Friday, 9:00 AM–10:00 PM, GMT+8)\n"
        "\n"
        "Happy riding!"
    )

