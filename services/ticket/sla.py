"""
SLA 计时器核心逻辑

实现首次响应时效(FRT)和解决时效(RT)计时
支持根据优先级和工单类型设置不同目标
支持暂停/恢复计时

增量3-1: v3.7.1
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List

from services.ticket.models import Ticket, TicketPriority, TicketStatus, TicketType


class SLAStatus(str, Enum):
    """SLA 状态枚举"""
    NORMAL = "normal"      # 剩余时间 > 50%
    WARNING = "warning"    # 50% >= 剩余时间 > 20%
    URGENT = "urgent"      # 20% >= 剩余时间 > 0%
    VIOLATED = "violated"  # 剩余时间 <= 0%
    COMPLETED = "completed"  # 已完成（已响应或已解决）


# SLA 目标配置（单位：秒）
# 首次响应时效（FRT）目标 - 按优先级
FRT_TARGETS: Dict[TicketPriority, int] = {
    TicketPriority.URGENT: 5 * 60,      # 紧急: 5分钟
    TicketPriority.HIGH: 15 * 60,       # 高: 15分钟
    TicketPriority.MEDIUM: 30 * 60,     # 中: 30分钟
    TicketPriority.LOW: 60 * 60,        # 低: 60分钟
}

# 解决时效（RT）目标 - 按优先级和工单类型组合
RT_TARGETS: Dict[TicketPriority, Dict[TicketType, int]] = {
    TicketPriority.URGENT: {
        TicketType.PRE_SALE: 2 * 3600,      # 售前紧急: 2小时
        TicketType.AFTER_SALE: 4 * 3600,    # 售后紧急: 4小时
        TicketType.COMPLAINT: 2 * 3600,     # 投诉紧急: 2小时
    },
    TicketPriority.HIGH: {
        TicketType.PRE_SALE: 4 * 3600,      # 售前高: 4小时
        TicketType.AFTER_SALE: 8 * 3600,    # 售后高: 8小时
        TicketType.COMPLAINT: 4 * 3600,     # 投诉高: 4小时
    },
    TicketPriority.MEDIUM: {
        TicketType.PRE_SALE: 8 * 3600,      # 售前中: 8小时
        TicketType.AFTER_SALE: 24 * 3600,   # 售后中: 24小时
        TicketType.COMPLAINT: 8 * 3600,     # 投诉中: 8小时
    },
    TicketPriority.LOW: {
        TicketType.PRE_SALE: 24 * 3600,     # 售前低: 24小时
        TicketType.AFTER_SALE: 48 * 3600,   # 售后低: 48小时
        TicketType.COMPLAINT: 24 * 3600,    # 投诉低: 24小时
    },
}

# SLA 暂停状态（等待客户/第三方时暂停计时）
SLA_PAUSE_STATUSES = {
    TicketStatus.WAITING_CUSTOMER,
    TicketStatus.WAITING_VENDOR,
}


def get_frt_target(priority: TicketPriority) -> int:
    """获取首次响应时效目标（秒）"""
    return FRT_TARGETS.get(priority, FRT_TARGETS[TicketPriority.MEDIUM])


def get_rt_target(priority: TicketPriority, ticket_type: TicketType) -> int:
    """获取解决时效目标（秒）"""
    priority_targets = RT_TARGETS.get(priority, RT_TARGETS[TicketPriority.MEDIUM])
    return priority_targets.get(ticket_type, priority_targets[TicketType.AFTER_SALE])


def calculate_sla_status(remaining_ratio: float) -> SLAStatus:
    """根据剩余时间比例计算SLA状态"""
    if remaining_ratio <= 0:
        return SLAStatus.VIOLATED
    if remaining_ratio <= 0.2:
        return SLAStatus.URGENT
    if remaining_ratio <= 0.5:
        return SLAStatus.WARNING
    return SLAStatus.NORMAL


@dataclass
class SLAInfo:
    """SLA 信息"""
    # 首次响应 SLA
    frt_target_seconds: int
    frt_elapsed_seconds: float
    frt_remaining_seconds: float
    frt_status: SLAStatus
    frt_completed: bool

    # 解决时效 SLA
    rt_target_seconds: int
    rt_elapsed_seconds: float
    rt_remaining_seconds: float
    rt_status: SLAStatus
    rt_completed: bool

    # 暂停信息
    is_paused: bool
    paused_duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frt_target_seconds": self.frt_target_seconds,
            "frt_elapsed_seconds": round(self.frt_elapsed_seconds, 2),
            "frt_remaining_seconds": round(self.frt_remaining_seconds, 2),
            "frt_remaining_minutes": round(self.frt_remaining_seconds / 60, 1),
            "frt_status": self.frt_status.value,
            "frt_completed": self.frt_completed,
            "rt_target_seconds": self.rt_target_seconds,
            "rt_elapsed_seconds": round(self.rt_elapsed_seconds, 2),
            "rt_remaining_seconds": round(self.rt_remaining_seconds, 2),
            "rt_remaining_hours": round(self.rt_remaining_seconds / 3600, 2),
            "rt_status": self.rt_status.value,
            "rt_completed": self.rt_completed,
            "is_paused": self.is_paused,
            "paused_duration_seconds": round(self.paused_duration_seconds, 2),
        }


class SLATimer:
    """SLA 计时器"""

    def __init__(self, ticket: Ticket):
        self.ticket = ticket
        self.ticket_id = ticket.ticket_id
        self.priority = ticket.priority
        self.ticket_type = ticket.ticket_type
        self.created_at = ticket.created_at
        self.first_response_at = ticket.first_response_at
        self.resolved_at = ticket.resolved_at
        self.status = ticket.status

        # 目标时效
        self.frt_target = get_frt_target(self.priority)
        self.rt_target = get_rt_target(self.priority, self.ticket_type)

        # 从 metadata 获取暂停累计时间
        self.paused_duration = ticket.metadata.get("sla_paused_duration", 0.0)

    def is_paused(self) -> bool:
        """检查SLA是否暂停"""
        return self.status in SLA_PAUSE_STATUSES

    def get_frt_elapsed(self, now: Optional[float] = None) -> float:
        """
        获取首次响应已用时间（秒）

        如果已响应，返回创建到首次响应的时间
        否则返回创建到现在的时间
        """
        if now is None:
            now = time.time()

        if self.first_response_at:
            return self.first_response_at - self.created_at
        return now - self.created_at

    def get_frt_remaining(self, now: Optional[float] = None) -> float:
        """
        获取首次响应剩余时间（秒）

        返回值可能为负数（已超时）
        """
        elapsed = self.get_frt_elapsed(now)
        return max(0, self.frt_target - elapsed)

    def get_frt_status(self, now: Optional[float] = None) -> SLAStatus:
        """获取首次响应SLA状态"""
        if self.first_response_at:
            return SLAStatus.COMPLETED

        remaining = self.get_frt_remaining(now)
        ratio = remaining / self.frt_target if self.frt_target > 0 else 0
        return calculate_sla_status(ratio)

    def get_rt_elapsed(self, now: Optional[float] = None) -> float:
        """
        获取解决时效已用时间（秒）

        如果已解决，返回创建到解决的时间（减去暂停时间）
        否则返回创建到现在的时间（减去暂停时间）
        暂停时间不计入
        """
        if now is None:
            now = time.time()

        if self.resolved_at:
            total = self.resolved_at - self.created_at
        else:
            total = now - self.created_at

        # 减去暂停时间
        return max(0, total - self.paused_duration)

    def get_rt_remaining(self, now: Optional[float] = None) -> float:
        """
        获取解决时效剩余时间（秒）

        返回值可能为负数（已超时）
        暂停状态下冻结计时
        """
        if self.is_paused():
            # 暂停状态下，使用已记录的时间计算
            elapsed = self.get_rt_elapsed(now)
        else:
            elapsed = self.get_rt_elapsed(now)

        return max(0, self.rt_target - elapsed)

    def get_rt_status(self, now: Optional[float] = None) -> SLAStatus:
        """获取解决时效SLA状态"""
        if self.resolved_at:
            return SLAStatus.COMPLETED

        # 归档、关闭状态不再计算
        if self.status in {TicketStatus.CLOSED, TicketStatus.ARCHIVED}:
            return SLAStatus.COMPLETED

        remaining = self.get_rt_remaining(now)
        ratio = remaining / self.rt_target if self.rt_target > 0 else 0
        return calculate_sla_status(ratio)

    def get_sla_info(self, now: Optional[float] = None) -> SLAInfo:
        """获取完整的 SLA 信息"""
        if now is None:
            now = time.time()

        return SLAInfo(
            frt_target_seconds=self.frt_target,
            frt_elapsed_seconds=self.get_frt_elapsed(now),
            frt_remaining_seconds=self.get_frt_remaining(now),
            frt_status=self.get_frt_status(now),
            frt_completed=self.first_response_at is not None,
            rt_target_seconds=self.rt_target,
            rt_elapsed_seconds=self.get_rt_elapsed(now),
            rt_remaining_seconds=self.get_rt_remaining(now),
            rt_status=self.get_rt_status(now),
            rt_completed=self.resolved_at is not None,
            is_paused=self.is_paused(),
            paused_duration_seconds=self.paused_duration,
        )

    def should_alert(self, now: Optional[float] = None) -> Dict[str, bool]:
        """
        检查是否需要发送告警

        返回:
            {
                "frt_alert": bool,  # 首次响应需要告警
                "rt_alert": bool,   # 解决时效需要告警
            }
        """
        frt_status = self.get_frt_status(now)
        rt_status = self.get_rt_status(now)

        return {
            "frt_alert": frt_status in {SLAStatus.URGENT, SLAStatus.VIOLATED},
            "rt_alert": rt_status in {SLAStatus.URGENT, SLAStatus.VIOLATED},
        }


def calculate_ticket_sla(ticket: Ticket, now: Optional[float] = None) -> Dict[str, Any]:
    """
    计算单个工单的 SLA 信息

    Args:
        ticket: 工单对象
        now: 当前时间（可选，用于测试）

    Returns:
        SLA 信息字典
    """
    timer = SLATimer(ticket)
    return timer.get_sla_info(now).to_dict()


@dataclass
class SLAAlert:
    """SLA 预警信息"""
    ticket_id: str
    alert_type: str  # "frt" 或 "rt"
    status: SLAStatus  # "warning", "urgent", "violated"
    remaining_seconds: float
    target_seconds: int
    assigned_to: Optional[str]
    priority: str
    ticket_type: str
    created_at: float  # 工单创建时间

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "alert_type": self.alert_type,
            "status": self.status.value,
            "remaining_seconds": round(self.remaining_seconds, 2),
            "remaining_minutes": round(self.remaining_seconds / 60, 1),
            "target_seconds": self.target_seconds,
            "target_minutes": round(self.target_seconds / 60, 1),
            "assigned_to": self.assigned_to,
            "priority": self.priority,
            "ticket_type": self.ticket_type,
            "created_at": self.created_at,
        }


def check_sla_alerts(ticket: Ticket, now: Optional[float] = None) -> List[SLAAlert]:
    """
    检查工单是否需要发送 SLA 预警

    只对 warning/urgent/violated 状态的 SLA 生成预警

    Args:
        ticket: 工单对象
        now: 当前时间

    Returns:
        预警列表（可能包含 FRT 和 RT 两个预警）
    """
    timer = SLATimer(ticket)
    alerts: List[SLAAlert] = []

    # 检查 FRT
    frt_status = timer.get_frt_status(now)
    if frt_status in {SLAStatus.WARNING, SLAStatus.URGENT, SLAStatus.VIOLATED}:
        alerts.append(SLAAlert(
            ticket_id=ticket.ticket_id,
            alert_type="frt",
            status=frt_status,
            remaining_seconds=timer.get_frt_remaining(now),
            target_seconds=timer.frt_target,
            assigned_to=ticket.assigned_agent_id,
            priority=ticket.priority.value,
            ticket_type=ticket.ticket_type.value,
            created_at=ticket.created_at,
        ))

    # 检查 RT
    rt_status = timer.get_rt_status(now)
    if rt_status in {SLAStatus.WARNING, SLAStatus.URGENT, SLAStatus.VIOLATED}:
        alerts.append(SLAAlert(
            ticket_id=ticket.ticket_id,
            alert_type="rt",
            status=rt_status,
            remaining_seconds=timer.get_rt_remaining(now),
            target_seconds=timer.rt_target,
            assigned_to=ticket.assigned_agent_id,
            priority=ticket.priority.value,
            ticket_type=ticket.ticket_type.value,
            created_at=ticket.created_at,
        ))

    return alerts


def format_alert_message(alert: SLAAlert) -> str:
    """
    格式化预警消息用于通知显示

    Args:
        alert: SLA 预警对象

    Returns:
        格式化的消息文本
    """
    alert_type_label = "首次响应" if alert.alert_type == "frt" else "解决时效"
    status_label = {
        SLAStatus.WARNING: "⚠️ 即将超时",
        SLAStatus.URGENT: "🔴 紧急",
        SLAStatus.VIOLATED: "❌ 已超时",
    }.get(alert.status, "")

    remaining = alert.remaining_seconds
    if remaining <= 0:
        time_text = "已超时"
    elif remaining < 60:
        time_text = f"剩余 {int(remaining)} 秒"
    elif remaining < 3600:
        time_text = f"剩余 {round(remaining / 60, 1)} 分钟"
    else:
        time_text = f"剩余 {round(remaining / 3600, 2)} 小时"

    return f"{status_label} 工单 {alert.ticket_id} {alert_type_label}{time_text}"
