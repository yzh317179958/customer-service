"""
兼容层 - 重导出新架构模块
"""
from services.session.redis_store import RedisSessionStore

__all__ = ["RedisSessionStore"]
