# -*- coding: utf-8 -*-
"""
内部接口访问密钥（可选）

用于在不引入完整登录鉴权的前提下，为“内部接口/Coze 插件接口”等提供一道低成本防护。

默认不强制（兼容现有调用方），通过环境变量开启强制校验：
- INTERNAL_API_KEY_ENFORCE=true
- INTERNAL_API_KEY=<your-secret>
"""

from __future__ import annotations

import os
import secrets

from fastapi import HTTPException, Request


def _internal_key_enabled() -> bool:
    return os.getenv("INTERNAL_API_KEY_ENFORCE", "false").lower() in {"true", "1", "yes"}


def _get_internal_api_key() -> str:
    return os.getenv("INTERNAL_API_KEY", "")


async def require_internal_api_key(request: Request) -> None:
    """
    内部调用密钥校验（可选）

    - 默认不强制（INTERNAL_API_KEY_ENFORCE=false），用于兼容现有调用方
    - 强制开启后，调用方需携带请求头：
      - X-Fiido-Internal-Key 或 X-Internal-Key
    """
    if not _internal_key_enabled():
        return

    expected = _get_internal_api_key()
    if not expected:
        raise HTTPException(status_code=503, detail="INTERNAL_API_KEY not configured")

    provided = request.headers.get("X-Fiido-Internal-Key") or request.headers.get("X-Internal-Key") or ""
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid internal key")

