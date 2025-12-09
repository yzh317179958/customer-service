import pytest

import src.ticket_store as ticket_store_module
from src.ticket_store import TicketStore
from src.ticket import Ticket, TicketPriority, TicketStatus, TicketType


def _make_ticket(ticket_id: str = "TKT-001") -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        title="测试工单",
        description="需要客户补充信息",
        created_by="agent_1",
        created_by_name="Tester",
        ticket_type=TicketType.AFTER_SALE,
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.IN_PROGRESS,
        created_at=0,
        updated_at=0
    )


def test_update_ticket_tracks_sla_pause_duration(monkeypatch):
    """
    进入等待客户状态时记录暂停时间，恢复处理中时累加暂停时长
    """
    store = TicketStore()
    ticket = _make_ticket()
    store._save_ticket(ticket)

    current_time = {"value": 1_000.0}

    def fake_time() -> float:
        return current_time["value"]

    monkeypatch.setattr(ticket_store_module.time, "time", fake_time)

    # 进入等待客户，记录开始时间
    current_time["value"] = 1_010.0
    store.update_ticket(ticket.ticket_id, status=TicketStatus.WAITING_CUSTOMER)
    waiting_ticket = store.get(ticket.ticket_id)
    assert waiting_ticket is not None
    assert waiting_ticket.metadata["sla_pause_started_at"] == pytest.approx(1_010.0)
    assert waiting_ticket.metadata.get("sla_paused_duration", 0.0) == pytest.approx(0.0)

    # 恢复处理中时累计暂停时长
    current_time["value"] = 1_025.0
    store.update_ticket(ticket.ticket_id, status=TicketStatus.IN_PROGRESS)
    resumed_ticket = store.get(ticket.ticket_id)
    assert resumed_ticket is not None
    assert "sla_pause_started_at" not in resumed_ticket.metadata
    assert resumed_ticket.metadata["sla_paused_duration"] == pytest.approx(15.0)

