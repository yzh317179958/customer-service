"""
兼容层 - 重导出新架构模块
"""
from services.session.regulator import Regulator, RegulatorConfig

__all__ = ["Regulator", "RegulatorConfig"]
