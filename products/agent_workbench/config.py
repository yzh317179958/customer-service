# -*- coding: utf-8 -*-
"""
坐席工作台 - 独立启动配置

提供坐席工作台模块独立启动时所需的配置参数
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentWorkbenchConfig:
    """坐席工作台产品配置"""

    # 服务配置
    host: str = field(default_factory=lambda: os.getenv("AGENT_WORKBENCH_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("AGENT_WORKBENCH_PORT", "8002")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # 产品标识
    product_name: str = "坐席工作台"
    product_code: str = "agent_workbench"
    api_prefix: str = "/api"

    # 功能开关
    enable_sla_alerts: bool = field(
        default_factory=lambda: os.getenv("ENABLE_SLA_ALERTS", "true").lower() == "true"
    )
    enable_heartbeat_monitor: bool = field(
        default_factory=lambda: os.getenv("ENABLE_HEARTBEAT_MONITOR", "true").lower() == "true"
    )

    # CORS 配置
    cors_origins: list = field(default_factory=lambda: [
        "http://localhost:3000",   # 坐席工作台前端 (vite dev)
        "http://localhost:5173",   # 备用前端端口
        "http://localhost:5174",   # 备用前端端口
        "http://localhost:8080",   # 其他前端端口
        "https://ai.fiido.com",    # 生产环境
    ])

    def __post_init__(self):
        """初始化后处理"""
        # 从环境变量扩展 CORS origins
        extra_origins = os.getenv("CORS_ORIGINS", "")
        if extra_origins:
            self.cors_origins.extend(extra_origins.split(","))


def get_config() -> AgentWorkbenchConfig:
    """获取坐席工作台配置"""
    return AgentWorkbenchConfig()
