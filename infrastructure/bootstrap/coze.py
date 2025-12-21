# -*- coding: utf-8 -*-
"""
基础设施 - Coze AI 客户端初始化模块

提供 Coze 客户端的统一初始化，支持：
- OAuth+JWT 鉴权
- Token 自动刷新
- JWTOAuthApp（用于 Chat SDK）
"""

import os
from dataclasses import dataclass
from typing import Optional, Any, Callable


@dataclass
class CozeConfig:
    """Coze 配置"""
    workflow_id: str = ""
    app_id: str = ""
    api_base: str = "https://api.coze.com"
    private_key_file: str = ""
    client_id: str = ""
    public_key_id: str = ""

    @classmethod
    def from_env(cls) -> "CozeConfig":
        """从环境变量加载配置"""
        return cls(
            workflow_id=os.getenv("COZE_WORKFLOW_ID", ""),
            app_id=os.getenv("COZE_APP_ID", ""),
            api_base=os.getenv("COZE_API_BASE", "https://api.coze.com"),
            private_key_file=os.getenv("COZE_OAUTH_PRIVATE_KEY_FILE", ""),
            client_id=os.getenv("COZE_OAUTH_CLIENT_ID", ""),
            public_key_id=os.getenv("COZE_OAUTH_PUBLIC_KEY_ID", "")
        )

    def validate(self):
        """验证必填配置"""
        if not self.workflow_id:
            raise ValueError("COZE_WORKFLOW_ID 环境变量未设置")
        if not self.app_id:
            raise ValueError("COZE_APP_ID 环境变量未设置")


# ============================================================================
# 全局单例
# ============================================================================

_coze_client = None
_token_manager = None
_jwt_oauth_app = None
_config: Optional[CozeConfig] = None
_initialized = False
_token_manager_factory: Optional[Callable[[], Any]] = None


def register_token_manager_factory(factory: Callable[[], Any]) -> None:
    """
    注册 Token 管理器工厂
    """
    global _token_manager_factory
    _token_manager_factory = factory


def init_coze_client(config: Optional[CozeConfig] = None) -> Any:
    """
    初始化 Coze 客户端（单例模式）

    Args:
        config: Coze 配置，默认从环境变量读取

    Returns:
        Coze 客户端实例

    Raises:
        ValueError: 配置缺失或初始化失败时抛出
    """
    global _coze_client, _token_manager, _jwt_oauth_app, _config, _initialized

    if _initialized and _coze_client is not None:
        return _coze_client

    _config = config or CozeConfig.from_env()
    _config.validate()

    try:
        import httpx
        from cozepy import Coze, TokenAuth, JWTOAuthApp

        # 初始化 Token 管理器
        if _token_manager_factory is None:
            raise ValueError("Coze token manager factory not registered")

        _token_manager = _token_manager_factory()
        access_token = _token_manager.get_access_token()

        # 创建 HTTP 客户端（禁用代理避免 SOCKS 协议问题）
        http_timeout = httpx.Timeout(
            connect=float(os.getenv("HTTP_TIMEOUT_CONNECT", 10.0)),
            read=float(os.getenv("HTTP_TIMEOUT_READ", 30.0)),
            write=10.0,
            pool=10.0
        )
        http_client = httpx.Client(
            timeout=http_timeout,
            trust_env=False
        )

        # 创建 Coze 客户端
        _coze_client = Coze(
            auth=TokenAuth(token=access_token),
            base_url=_config.api_base,
            http_client=http_client
        )

        print(f"[Bootstrap] ✅ Coze 客户端初始化成功")
        print(f"   API Base: {_config.api_base}")
        print(f"   App ID: {_config.app_id}")
        print(f"   Workflow ID: {_config.workflow_id}")
        print(f"   Token 预览: {access_token[:30]}...")

        # 初始化 JWTOAuthApp（用于 Chat SDK）
        if _config.private_key_file and os.path.exists(_config.private_key_file):
            with open(_config.private_key_file, "r") as f:
                private_key = f.read()

            _jwt_oauth_app = JWTOAuthApp(
                client_id=_config.client_id,
                private_key=private_key,
                public_key_id=_config.public_key_id,
                base_url=_config.api_base,
            )
            print(f"[Bootstrap] ✅ JWTOAuthApp 初始化成功 (用于 Chat SDK)")
        else:
            print(f"[Bootstrap] ⚠️ 未找到私钥文件，Chat SDK token 生成将不可用")

        _initialized = True
        return _coze_client

    except Exception as e:
        raise ValueError(f"Coze 客户端初始化失败: {str(e)}")


def get_coze_client() -> Any:
    """
    获取 Coze 客户端实例

    Returns:
        Coze 客户端实例

    Raises:
        RuntimeError: 未初始化时抛出
    """
    if _coze_client is None:
        raise RuntimeError("Coze client not initialized. Call init_coze_client() first.")
    return _coze_client


def get_token_manager() -> Any:
    """获取 Token 管理器"""
    return _token_manager


def get_jwt_oauth_app() -> Optional[Any]:
    """获取 JWTOAuthApp（可能为 None）"""
    return _jwt_oauth_app


def get_workflow_id() -> str:
    """获取 Workflow ID"""
    return _config.workflow_id if _config else ""


def get_app_id() -> str:
    """获取 App ID"""
    return _config.app_id if _config else ""


def refresh_token_if_needed():
    """
    检查并刷新 Token

    在每次 API 调用前调用，确保 token 有效
    """
    global _coze_client

    if _token_manager is None or _coze_client is None:
        return

    try:
        from cozepy import TokenAuth
        new_token = _token_manager.get_access_token()
        _coze_client._auth = TokenAuth(token=new_token)
    except Exception as e:
        print(f"[Bootstrap] ⚠️ Token 刷新失败: {e}")


def reset():
    """重置初始化状态（仅用于测试）"""
    global _coze_client, _token_manager, _jwt_oauth_app, _config, _initialized
    _coze_client = None
    _token_manager = None
    _jwt_oauth_app = None
    _config = None
    _initialized = False
