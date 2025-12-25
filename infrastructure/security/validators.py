# -*- coding: utf-8 -*-
"""
安全防护组件 - 输入校验工具

提供输入验证和清理功能：
- 消息长度限制
- XSS 防护（HTML 转义）
- 订单号格式校验
"""

import html
import re
from typing import Optional

from fastapi import HTTPException


def validate_message_length(
    message: str,
    max_length: int = 2000,
    field_name: str = "message"
) -> str:
    """
    验证消息长度

    Args:
        message: 消息内容
        max_length: 最大长度，默认 2000 字符
        field_name: 字段名称，用于错误消息

    Returns:
        原始消息（验证通过）

    Raises:
        HTTPException: 消息过长时抛出 400 错误
    """
    if message is None:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": f"{field_name} is required",
                "code": "MISSING_FIELD"
            }
        )

    if len(message) > max_length:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": f"{field_name} is too long. Maximum {max_length} characters allowed.",
                "code": "MESSAGE_TOO_LONG",
                "max_length": max_length,
                "actual_length": len(message)
            }
        )

    return message


def sanitize_input(text: str, escape_html: bool = True) -> str:
    """
    清理用户输入

    处理 XSS 攻击向量：
    - HTML 特殊字符转义（<, >, &, ", '）
    - 移除 NULL 字节
    - 规范化空白字符

    Args:
        text: 原始文本
        escape_html: 是否转义 HTML，默认 True

    Returns:
        清理后的文本

    Usage:
        user_input = sanitize_input(request.message)
    """
    if not text:
        return text

    # 移除 NULL 字节（可能导致安全问题）
    result = text.replace('\x00', '')

    # HTML 转义（防止 XSS）
    if escape_html:
        result = html.escape(result)

    # 规范化连续空白
    result = re.sub(r'\s+', ' ', result)

    # 移除首尾空白
    result = result.strip()

    return result


def validate_order_number(order_number: str) -> str:
    """
    验证订单号格式

    支持的格式：
    - Shopify 订单号: #12345, UK12345, US12345 等
    - 纯数字: 12345678
    - 带前缀: ORD-12345, ORDER-12345

    Args:
        order_number: 订单号

    Returns:
        清理后的订单号

    Raises:
        HTTPException: 格式无效时抛出 400 错误
    """
    if not order_number:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Order number is required",
                "code": "MISSING_ORDER_NUMBER"
            }
        )

    # 清理：移除首尾空白，转大写
    cleaned = order_number.strip().upper()

    # 移除开头的 # 符号
    if cleaned.startswith('#'):
        cleaned = cleaned[1:]

    # 验证格式：允许字母、数字、连字符
    # 常见格式: UK12345, US12345, ORD-12345, 12345678
    pattern = r'^[A-Z]{0,10}[\-]?[A-Z0-9]{3,30}$'

    if not re.match(pattern, cleaned):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid order number format",
                "code": "INVALID_ORDER_NUMBER",
                "example": "UK12345, #12345, ORD-12345"
            }
        )

    return cleaned


def validate_tracking_number(tracking_number: str) -> str:
    """
    验证物流单号格式

    支持的格式：
    - 标准物流单号: YT2412345678901234, 4PX 开头等
    - 长度: 8-40 字符

    Args:
        tracking_number: 物流单号

    Returns:
        清理后的物流单号

    Raises:
        HTTPException: 格式无效时抛出 400 错误
    """
    if not tracking_number:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Tracking number is required",
                "code": "MISSING_TRACKING_NUMBER"
            }
        )

    # 清理：移除首尾空白，转大写
    cleaned = tracking_number.strip().upper()

    # 移除空格和连字符（某些物流单号带格式）
    cleaned = re.sub(r'[\s\-]', '', cleaned)

    # 验证长度
    if len(cleaned) < 8 or len(cleaned) > 40:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Tracking number length must be 8-40 characters",
                "code": "INVALID_TRACKING_NUMBER_LENGTH"
            }
        )

    # 验证格式：只允许字母和数字
    if not re.match(r'^[A-Z0-9]+$', cleaned):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Tracking number can only contain letters and numbers",
                "code": "INVALID_TRACKING_NUMBER_FORMAT"
            }
        )

    return cleaned


def validate_email(email: str) -> str:
    """
    验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        清理后的邮箱（小写）

    Raises:
        HTTPException: 格式无效时抛出 400 错误
    """
    if not email:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Email is required",
                "code": "MISSING_EMAIL"
            }
        )

    # 清理
    cleaned = email.strip().lower()

    # 简单邮箱格式验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, cleaned):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid email format",
                "code": "INVALID_EMAIL"
            }
        )

    return cleaned


def validate_username(username: str) -> str:
    """
    验证用户名格式（坐席登录）

    规则：
    - 长度 3-30 字符
    - 只允许字母、数字、下划线

    Args:
        username: 用户名

    Returns:
        清理后的用户名

    Raises:
        HTTPException: 格式无效时抛出 400 错误
    """
    if not username:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Username is required",
                "code": "MISSING_USERNAME"
            }
        )

    # 清理
    cleaned = username.strip()

    # 长度检查
    if len(cleaned) < 3 or len(cleaned) > 30:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Username must be 3-30 characters",
                "code": "INVALID_USERNAME_LENGTH"
            }
        )

    # 格式检查
    if not re.match(r'^[a-zA-Z0-9_]+$', cleaned):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Username can only contain letters, numbers, and underscores",
                "code": "INVALID_USERNAME_FORMAT"
            }
        )

    return cleaned
