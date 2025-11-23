"""
工作时间配置模块

功能：
- 解析环境变量中的工作时间配置
- 提供 is_in_shift() 函数判断当前是否在工作时间
- 支持时区、周末、节假日配置
"""

import os
from datetime import datetime, time
from typing import List, Optional
import pytz
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ShiftConfig:
    """工作时间配置管理"""

    def __init__(self):
        # 工作时间配置
        self.shift_start = self._parse_time(
            os.getenv('HUMAN_SHIFT_START', '09:00')
        )
        self.shift_end = self._parse_time(
            os.getenv('HUMAN_SHIFT_END', '18:00')
        )

        # 时区配置
        timezone_str = os.getenv('TIMEZONE', 'Asia/Shanghai')
        try:
            self.timezone = pytz.timezone(timezone_str)
        except Exception:
            print(f"⚠️  无效时区 '{timezone_str}'，使用默认 Asia/Shanghai")
            self.timezone = pytz.timezone('Asia/Shanghai')

        # 周末是否禁用人工服务
        self.weekends_disabled = os.getenv('WEEKENDS_DISABLED', 'true').lower() == 'true'

        # 节假日列表（格式：YYYY-MM-DD,YYYY-MM-DD）
        holidays_str = os.getenv('HOLIDAYS', '')
        self.holidays = self._parse_holidays(holidays_str)

        print(f"✅ ShiftConfig 初始化完成:")
        print(f"   工作时间: {self.shift_start.strftime('%H:%M')} - {self.shift_end.strftime('%H:%M')}")
        print(f"   时区: {self.timezone}")
        print(f"   周末禁用: {self.weekends_disabled}")
        print(f"   节假日: {len(self.holidays)} 天")

    def _parse_time(self, time_str: str) -> time:
        """解析时间字符串 (HH:MM)"""
        try:
            parts = time_str.split(':')
            return time(int(parts[0]), int(parts[1]))
        except Exception:
            print(f"⚠️  无效时间格式 '{time_str}'，使用默认值")
            return time(9, 0)

    def _parse_holidays(self, holidays_str: str) -> List[str]:
        """解析节假日列表"""
        if not holidays_str.strip():
            return []

        holidays = []
        for date_str in holidays_str.split(','):
            date_str = date_str.strip()
            if date_str:
                try:
                    # 验证日期格式
                    datetime.strptime(date_str, '%Y-%m-%d')
                    holidays.append(date_str)
                except ValueError:
                    print(f"⚠️  无效日期格式 '{date_str}'，已忽略")

        return holidays

    def is_in_shift(self, check_time: Optional[datetime] = None) -> bool:
        """
        判断指定时间是否在工作时间内

        Args:
            check_time: 要检查的时间，默认为当前时间

        Returns:
            bool: True 表示在工作时间内
        """
        if check_time is None:
            check_time = datetime.now(self.timezone)
        elif check_time.tzinfo is None:
            # 如果没有时区信息，添加配置的时区
            check_time = self.timezone.localize(check_time)
        else:
            # 转换到配置的时区
            check_time = check_time.astimezone(self.timezone)

        # 检查是否为节假日
        date_str = check_time.strftime('%Y-%m-%d')
        if date_str in self.holidays:
            return False

        # 检查是否为周末
        if self.weekends_disabled and check_time.weekday() >= 5:  # 5=周六, 6=周日
            return False

        # 检查时间范围
        current_time = check_time.time()

        # 处理跨天的情况（如 22:00 - 06:00）
        if self.shift_start <= self.shift_end:
            # 正常情况：09:00 - 18:00
            return self.shift_start <= current_time <= self.shift_end
        else:
            # 跨天情况：22:00 - 06:00
            return current_time >= self.shift_start or current_time <= self.shift_end

    def get_config(self) -> dict:
        """获取配置信息（用于 API 返回）"""
        return {
            'shift_start': self.shift_start.strftime('%H:%M'),
            'shift_end': self.shift_end.strftime('%H:%M'),
            'timezone': str(self.timezone),
            'weekends_disabled': self.weekends_disabled,
            'holidays': self.holidays,
            'is_in_shift': self.is_in_shift()
        }

    def get_next_shift_time(self) -> Optional[datetime]:
        """
        获取下一个工作时间开始时刻

        Returns:
            datetime: 下一个工作时间开始，如果当前在工作时间则返回 None
        """
        if self.is_in_shift():
            return None

        now = datetime.now(self.timezone)

        # 尝试找到下一个工作日
        for days_ahead in range(1, 8):  # 最多查找一周
            next_date = now + timedelta(days=days_ahead)

            # 跳过节假日
            if next_date.strftime('%Y-%m-%d') in self.holidays:
                continue

            # 跳过周末
            if self.weekends_disabled and next_date.weekday() >= 5:
                continue

            # 返回这一天的工作开始时间
            return self.timezone.localize(
                datetime.combine(next_date.date(), self.shift_start)
            )

        return None


# 全局实例
shift_config: Optional[ShiftConfig] = None


def get_shift_config() -> ShiftConfig:
    """获取全局 ShiftConfig 实例"""
    global shift_config
    if shift_config is None:
        shift_config = ShiftConfig()
    return shift_config


def is_in_shift() -> bool:
    """快捷函数：判断当前是否在工作时间"""
    return get_shift_config().is_in_shift()


# 需要导入 timedelta
from datetime import timedelta
