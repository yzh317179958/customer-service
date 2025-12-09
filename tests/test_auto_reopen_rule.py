import asyncio

import pytest

import src.ticket_store as ticket_store_module
from src.agent_auth import Agent, AgentRole, AgentStatus
from src.automation_rules.auto_reopen import CustomerReplyAutoReopen
from src.session_state import SessionState
from src.ticket import Ticket, TicketPriority, TicketStatus, TicketType
from src.ticket_store import TicketStore


class DummyAgentManager:
    def __init__(self, agent: Agent):
        self._agent = agent

    def get_agent_by_id(self, agent_id: str):
        if self._agent.id == agent_id:
            return self._agent
        return None


def _make_waiting_ticket() -> Ticket:
    return Ticket(
        ticket_id="TKT-1001",
        title="等待客户回复",
        description="请提供序列号",
        created_by="agent_1",
        ticket_type=TicketType.AFTER_SALE,
        priority=TicketPriority.HIGH,
        status=TicketStatus.WAITING_CUSTOMER,
        assigned_agent_id="agent-123",
        assigned_agent_name="Alice",
        metadata={
            "sla_pause_started_at": 1_000.0,
            "sla_paused_duration": 0.0
        }
    )


def test_customer_reply_rule_resumes_ticket(monkeypatch):
    store = TicketStore()
    ticket = _make_waiting_ticket()
    store._save_ticket(ticket)

    session = SessionState(session_name="session_auto_reopen")
    session.add_ticket_reference(ticket.ticket_id)

    agent = Agent(
        id="agent-123",
        username="agent_user",
        password_hash="hash",
        name="Tester",
        role=AgentRole.AGENT,
        status=AgentStatus.ONLINE
    )
    manager = DummyAgentManager(agent)
    rule = CustomerReplyAutoReopen(store, agent_manager=manager)

    sent_notifications = []

    async def fake_notify(target: str, payload: dict):
        sent_notifications.append((target, payload))

    monkeypatch.setattr(ticket_store_module.time, "time", lambda: 1_200.0)

    updated_tickets = asyncio.run(
        rule.handle_reply(session, notify_callback=fake_notify)
    )

    assert len(updated_tickets) == 1

    refreshed = store.get(ticket.ticket_id)
    assert refreshed is not None
    assert refreshed.status == TicketStatus.IN_PROGRESS
    assert refreshed.metadata["sla_paused_duration"] == pytest.approx(200.0)
    assert "sla_pause_started_at" not in refreshed.metadata

    # 验证通知使用坐席 username 作为目标
    assert sent_notifications
    target, payload = sent_notifications[0]
    assert target == "agent_user"
    assert payload["type"] == "customer_replied"
    assert payload["ticket_id"] == ticket.ticket_id

