"""
TicketStore 批量调整优先级测试
"""

from src.ticket_store import TicketStore
from src.ticket import Ticket, TicketPriority, TicketStatus, TicketType


def _ticket(ticket_id: str, priority: TicketPriority = TicketPriority.MEDIUM) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        title="Title",
        description="Desc",
        created_by="tester",
        created_by_name="Tester",
        ticket_type=TicketType.AFTER_SALE,
        priority=priority,
        status=TicketStatus.PENDING
    )


def test_batch_priority_updates_all():
    store = TicketStore()
    store.create(_ticket("TKT-A"))
    store.create(_ticket("TKT-B"))

    result = store.batch_update_priority(
        ["TKT-A", "TKT-B"],
        priority=TicketPriority.HIGH,
        reason="VIP request",
        changed_by="admin"
    )

    assert len(result["tickets"]) == 2
    assert not result["failed"]
    assert store.get("TKT-A").priority == TicketPriority.HIGH
    assert store.get("TKT-B").priority == TicketPriority.HIGH


def test_batch_priority_handles_missing():
    store = TicketStore()
    store.create(_ticket("TKT-C"))

    result = store.batch_update_priority(
        ["TKT-C", "TKT-D"],
        priority=TicketPriority.LOW,
        reason=None,
        changed_by="admin"
    )

    assert len(result["tickets"]) == 1
    assert result["failed"][0]["ticket_id"] == "TKT-D"
