"""
TicketStore 批量关闭单元测试
"""

from src.ticket_store import TicketStore
from src.ticket import Ticket, TicketPriority, TicketStatus, TicketType


def _resolved_ticket(ticket_id: str) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        title="Resolved ticket",
        description="desc",
        status=TicketStatus.RESOLVED,
        created_by="tester",
        created_by_name="Tester",
        ticket_type=TicketType.AFTER_SALE,
        priority=TicketPriority.MEDIUM
    )


def test_batch_close_only_accepts_resolved():
    store = TicketStore()
    resolved = _resolved_ticket("TKT-R1")
    pending = Ticket(
        ticket_id="TKT-P1",
        title="Pending",
        description="pending",
        created_by="tester",
        created_by_name="Tester",
        ticket_type=TicketType.AFTER_SALE,
        priority=TicketPriority.MEDIUM
    )
    store.create(resolved)
    store.create(pending)

    result = store.batch_close(
        ["TKT-R1", "TKT-P1"],
        reason="User confirmed",
        comment="Batch close",
        changed_by="admin"
    )

    assert len(result["tickets"]) == 1
    assert result["tickets"][0].status == TicketStatus.CLOSED
    assert result["failed"]
    assert store.get("TKT-R1").status == TicketStatus.CLOSED
    assert store.get("TKT-P1").status == TicketStatus.PENDING


def test_batch_close_handles_missing_ticket():
    store = TicketStore()
    resolved = _resolved_ticket("TKT-R2")
    store.create(resolved)

    result = store.batch_close(
        ["TKT-R2", "UNKNOWN"],
        reason="done",
        comment=None,
        changed_by="admin"
    )

    assert len(result["tickets"]) == 1
    assert result["failed"][0]["ticket_id"] == "UNKNOWN"
