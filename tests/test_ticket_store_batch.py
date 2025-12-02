"""
TicketStore 批量分配单元测试
"""

from src.ticket_store import TicketStore
from src.ticket import Ticket, TicketPriority, TicketStatus, TicketType


def _build_ticket(ticket_id: str) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        title="Test",
        description="desc",
        created_by="tester",
        created_by_name="Tester",
        ticket_type=TicketType.AFTER_SALE,
        priority=TicketPriority.MEDIUM
    )


def test_batch_assign_updates_multiple_tickets():
    store = TicketStore()
    ticket_a = _build_ticket("TKT-1")
    ticket_b = _build_ticket("TKT-2")
    store.create(ticket_a)
    store.create(ticket_b)

    result = store.batch_assign(
        ["TKT-1", "TKT-2"],
        assigned_agent_id="agent_x",
        assigned_agent_name="Agent X",
        changed_by="admin"
    )

    assert len(result["tickets"]) == 2
    assert not result["failed"]
    refreshed_a = store.get("TKT-1")
    refreshed_b = store.get("TKT-2")
    assert refreshed_a.assigned_agent_id == "agent_x"
    assert refreshed_b.assigned_agent_name == "Agent X"


def test_batch_assign_handles_missing_ticket():
    store = TicketStore()
    ticket = _build_ticket("TKT-3")
    store.create(ticket)

    result = store.batch_assign(
        ["TKT-3", "UNKNOWN"],
        assigned_agent_id="agent_y",
        assigned_agent_name=None,
        changed_by="admin"
    )

    assert len(result["tickets"]) == 1
    assert result["failed"]
    assert result["failed"][0]["ticket_id"] == "UNKNOWN"
    assert store.get("TKT-3").assigned_agent_id == "agent_y"
