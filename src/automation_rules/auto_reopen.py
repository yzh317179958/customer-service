"""
客户回复自动恢复规则

增量3-8: 当客户在等待反馈阶段回复时，自动将工单恢复为处理中并恢复 SLA 计时
"""

from __future__ import annotations

from typing import Awaitable, Callable, List, Optional, Sequence

from src.agent_auth import AgentManager
from src.session_state import SessionState
from src.ticket import Ticket, TicketStatus
from src.ticket_store import TicketStore

NotifyCallback = Callable[[str, dict], Awaitable[None]]


class CustomerReplyAutoReopen:
    """
    监听客户回复事件，自动恢复等待客户状态的工单
    """

    def __init__(
        self,
        ticket_store: Optional[TicketStore],
        agent_manager: Optional[AgentManager] = None
    ):
        self.ticket_store = ticket_store
        self.agent_manager = agent_manager

    def update_dependencies(
        self,
        *,
        ticket_store: Optional[TicketStore] = None,
        agent_manager: Optional[AgentManager] = None
    ):
        """运行时更新依赖"""
        if ticket_store is not None:
            self.ticket_store = ticket_store
        if agent_manager is not None:
            self.agent_manager = agent_manager

    async def handle_reply(
        self,
        session_state: SessionState,
        notify_callback: Optional[NotifyCallback] = None
    ) -> List[Ticket]:
        """
        处理客户回复事件
        Args:
            session_state: 当前会话状态
            notify_callback: 可选的通知回调（发送 SSE 等）
        Returns:
            更新后的工单列表
        """
        if not self.ticket_store:
            return []
        ticket_ids = self._extract_ticket_ids(session_state)
        if not ticket_ids:
            return []

        updated: List[Ticket] = []
        for ticket_id in ticket_ids:
            ticket = self.ticket_store.get(ticket_id)
            if not ticket or ticket.status != TicketStatus.WAITING_CUSTOMER:
                continue

            updated_ticket = self.ticket_store.update_ticket(
                ticket_id,
                status=TicketStatus.IN_PROGRESS,
                changed_by="system",
                change_reason="customer_reply_auto_resume",
                note="客户回复，系统自动恢复处理中"
            )
            if not updated_ticket:
                continue

            updated.append(updated_ticket)

            if notify_callback:
                target = self._resolve_notify_target(updated_ticket.assigned_agent_id)
                if target:
                    payload = {
                        "type": "customer_replied",
                        "ticket_id": updated_ticket.ticket_id,
                        "session_name": session_state.session_name,
                        "status": (
                            updated_ticket.status.value
                            if isinstance(updated_ticket.status, TicketStatus)
                            else updated_ticket.status
                        ),
                        "message": "客户已回复，系统自动将工单恢复处理中"
                    }
                    await notify_callback(target, payload)

        return updated

    def _extract_ticket_ids(self, session_state: SessionState) -> Sequence[str]:
        """获取关联的工单 ID，最新的优先"""
        if not session_state.tickets:
            return []
        ordered: List[str] = []
        seen = set()
        for ticket_id in reversed(session_state.tickets):
            if not ticket_id or ticket_id in seen:
                continue
            ordered.append(ticket_id)
            seen.add(ticket_id)
        return ordered

    def _resolve_notify_target(self, assigned_agent_id: Optional[str]) -> Optional[str]:
        """根据坐席ID解析通知目标（username）"""
        if not assigned_agent_id:
            return None

        if self.agent_manager:
            agent = self.agent_manager.get_agent_by_id(assigned_agent_id)
            if agent:
                return agent.username
        return assigned_agent_id
