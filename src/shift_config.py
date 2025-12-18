"""
兼容层 - 重导出新架构模块
"""
from services.session.shift_config import get_shift_config, is_in_shift, ShiftConfig

__all__ = ["get_shift_config", "is_in_shift", "ShiftConfig"]
