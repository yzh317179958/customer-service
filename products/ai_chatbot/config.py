# -*- coding: utf-8 -*-
"""
AI 智能客服 - 独立启动配置

提供 AI 客服模块独立启动时所需的配置参数
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AIChatbotConfig:
    """AI 客服产品配置"""

    # 服务配置
    host: str = field(default_factory=lambda: os.getenv("AI_CHATBOT_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("AI_CHATBOT_PORT", "8001")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # 产品标识
    product_name: str = "AI智能客服"
    product_code: str = "ai_chatbot"
    api_prefix: str = "/api"

    # 功能开关
    enable_regulator: bool = field(
        default_factory=lambda: os.getenv("ENABLE_REGULATOR", "true").lower() == "true"
    )
    enable_warmup: bool = field(
        default_factory=lambda: os.getenv("WARMUP_ENABLED", "true").lower() == "true"
    )

    # CORS 配置
    cors_origins: list = field(default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://ai.fiido.com",
    ])

    def __post_init__(self):
        """初始化后处理"""
        # 从环境变量扩展 CORS origins
        extra_origins = os.getenv("CORS_ORIGINS", "")
        if extra_origins:
            self.cors_origins.extend(extra_origins.split(","))


def get_config() -> AIChatbotConfig:
    """获取 AI 客服配置"""
    return AIChatbotConfig()
