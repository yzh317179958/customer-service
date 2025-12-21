"""
AI 智能客服 - 依赖注入模块

提供 AI 客服模块所需的依赖获取函数，
通过 FastAPI Depends 注入到路由处理器中。

注意：全局变量在 backend.py 的 lifespan 中初始化，
这里通过 getter 函数获取，避免循环导入。
"""

from typing import Optional, Callable
from cozepy import Coze

# 全局变量引用（由 backend.py 在 lifespan 中设置）
_coze_client: Optional[Coze] = None
_token_manager = None
_session_store = None
_regulator = None
_jwt_oauth_app = None
_sse_queues: dict = {}
_smart_assignment_engine = None
_customer_reply_auto_reopen = None

# 配置变量
_workflow_id: str = ""
_app_id: str = ""


def set_coze_client(client: Coze):
    """设置 Coze 客户端（由 backend.py 调用）"""
    global _coze_client
    _coze_client = client


def set_token_manager(manager):
    """设置 Token 管理器（由 backend.py 调用）"""
    global _token_manager
    _token_manager = manager


def set_session_store(store):
    """设置会话存储（由 backend.py 调用）"""
    global _session_store
    _session_store = store


def set_regulator(reg):
    """设置监管引擎（由 backend.py 调用）"""
    global _regulator
    _regulator = reg


def set_jwt_oauth_app(app):
    """设置 JWT OAuth App（由 backend.py 调用）"""
    global _jwt_oauth_app
    _jwt_oauth_app = app


def set_config(workflow_id: str, app_id: str):
    """设置配置（由 backend.py 调用）"""
    global _workflow_id, _app_id
    _workflow_id = workflow_id
    _app_id = app_id


def set_sse_queues(queues: dict):
    """设置 SSE 队列（由 backend.py 调用）"""
    global _sse_queues
    _sse_queues = queues


def set_smart_assignment_engine(engine):
    """设置智能分配引擎（由 backend.py 调用）"""
    global _smart_assignment_engine
    _smart_assignment_engine = engine


def set_customer_reply_auto_reopen(rule):
    """设置客户回复自动恢复规则（由 backend.py 调用）"""
    global _customer_reply_auto_reopen
    _customer_reply_auto_reopen = rule


# ==================== Getter 函数（用于 Depends 注入）====================

def get_coze_client() -> Coze:
    """获取 Coze 客户端"""
    if _coze_client is None:
        raise RuntimeError("Coze client not initialized")
    return _coze_client


def get_token_manager():
    """获取 Token 管理器"""
    if _token_manager is None:
        raise RuntimeError("Token manager not initialized")
    return _token_manager


def get_session_store():
    """获取会话存储"""
    if _session_store is None:
        raise RuntimeError("Session store not initialized")
    return _session_store


def get_regulator():
    """获取监管引擎"""
    return _regulator  # 可以为 None


def get_jwt_oauth_app():
    """获取 JWT OAuth App"""
    return _jwt_oauth_app  # 可以为 None


def get_workflow_id() -> str:
    """获取 Workflow ID"""
    return _workflow_id


def get_app_id() -> str:
    """获取 App ID"""
    return _app_id


def get_sse_queues() -> dict:
    """获取 SSE 队列"""
    return _sse_queues


def get_smart_assignment_engine():
    """获取智能分配引擎"""
    return _smart_assignment_engine


def get_customer_reply_auto_reopen():
    """获取客户回复自动恢复规则"""
    return _customer_reply_auto_reopen


# ==================== 依赖注入帮助函数 ====================

def refresh_coze_client_if_needed():
    """
    检查并刷新 Coze 客户端的 token

    在每次 API 调用前调用此函数，确保 token 有效
    """
    global _coze_client

    if _token_manager is None or _coze_client is None:
        return

    try:
        # 获取最新的 access token（会自动刷新过期的 token）
        new_token = _token_manager.get_access_token()

        # 更新 Coze 客户端的 auth
        from cozepy import TokenAuth
        _coze_client._auth = TokenAuth(token=new_token)

    except Exception as e:
        print(f"⚠️ Token 刷新失败: {e}")
