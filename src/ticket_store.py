"""
工单存储管理

最小可行版本：支持创建与列出工单
"""

from __future__ import annotations

import json
import time
from typing import List, Optional, Dict, Any

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None

from src.ticket import (
    Ticket,
    TicketStatus,
    TicketPriority,
    TicketCustomerInfo,
    TicketType,
    TicketCommentType,
    generate_ticket_id,
)


class TicketStore:
    """工单存储（支持 Redis / 内存双模式）"""

    def __init__(self, redis_client: Optional["redis.Redis"] = None):
        self.redis = redis_client
        self.key_prefix = "ticket"
        self.index_key = f"{self.key_prefix}:index"
        self._memory_store = {} if redis_client is None else None

    def _ticket_searchable_strings(self, ticket: Ticket) -> List[str]:
        fields: List[str] = [
            ticket.ticket_id,
            ticket.title,
            ticket.description,
            ticket.created_by,
            ticket.created_by_name or "",
            ticket.assigned_agent_id or "",
            ticket.assigned_agent_name or "",
            ticket.session_name or "",
        ]
        if ticket.customer:
            fields.extend([
                ticket.customer.name or "",
                ticket.customer.email or "",
                ticket.customer.phone or "",
                ticket.customer.country or ""
            ])

        metadata = ticket.metadata or {}
        for value in metadata.values():
            if isinstance(value, (str, int, float)):
                fields.append(str(value))
            elif isinstance(value, list):
                fields.extend(str(item) for item in value if item is not None)
            elif isinstance(value, dict):
                fields.extend(str(item) for item in value.values() if item is not None)

        return [str(field) for field in fields if field]

    # ------------------
    # 基础方法
    # ------------------
    def _save_ticket(self, ticket: Ticket):
        data = json.dumps(ticket.to_dict(), ensure_ascii=False)
        if self.redis:
            pipe = self.redis.pipeline()
            pipe.set(f"{self.key_prefix}:{ticket.ticket_id}", data)
            pipe.sadd(self.index_key, ticket.ticket_id)
            pipe.execute()
        else:
            self._memory_store[ticket.ticket_id] = data  # type: ignore

    def _load_ticket(self, ticket_id: str) -> Optional[Ticket]:
        if self.redis:
            data = self.redis.get(f"{self.key_prefix}:{ticket_id}")
        else:
            data = self._memory_store.get(ticket_id) if self._memory_store else None  # type: ignore

        if not data:
            return None

        if isinstance(data, bytes):
            data = data.decode("utf-8")

        return Ticket.from_dict(json.loads(data))

    def _load_all_ids(self) -> List[str]:
        if self.redis:
            ids = self.redis.smembers(self.index_key)
            return [id_.decode("utf-8") if isinstance(id_, bytes) else str(id_) for id_ in ids]
        if self._memory_store:
            return list(self._memory_store.keys())
        return []

    # ------------------
    # 对外接口
    # ------------------
    def create(self, ticket: Ticket) -> Ticket:
        if not ticket.ticket_id:
            ticket.ticket_id = generate_ticket_id()
        now = time.time()
        ticket.created_at = now
        ticket.updated_at = now
        ticket.add_status_history(
            from_status=None,
            to_status=ticket.status,
            changed_by=ticket.created_by,
            change_reason="created"
        )
        self._save_ticket(ticket)
        return ticket

    def create_from_payload(
        self,
        *,
        title: str,
        description: str,
        created_by: str,
        created_by_name: Optional[str] = None,
        session_name: Optional[str] = None,
        ticket_type: TicketType,
        priority: TicketPriority,
        customer: Optional[dict] = None,
        assigned_agent_id: Optional[str] = None,
        assigned_agent_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Ticket:
        ticket = Ticket(
            ticket_id=generate_ticket_id(),
            title=title,
            description=description,
            created_by=created_by,
            created_by_name=created_by_name,
            session_name=session_name,
            ticket_type=ticket_type,
            priority=priority,
            assigned_agent_id=assigned_agent_id,
            assigned_agent_name=assigned_agent_name,
            customer=TicketCustomerInfo(**customer) if customer else None,
            metadata=metadata or {},
        )
        if assigned_agent_id or assigned_agent_name:
            ticket.add_assignment_record(
                agent_id=assigned_agent_id,
                agent_name=assigned_agent_name,
                assigned_by=created_by
            )
        return self.create(ticket)

    def list(
        self,
        *,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_agent_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, List[Ticket]]:
        ids = self._load_all_ids()
        tickets: List[Ticket] = []
        for ticket_id in ids:
            ticket = self._load_ticket(ticket_id)
            if ticket:
                tickets.append(ticket)

        # 过滤
        if status:
            tickets = [t for t in tickets if t.status == status]
        if priority:
            tickets = [t for t in tickets if t.priority == priority]
        if assigned_agent_id:
            tickets = [t for t in tickets if t.assigned_agent_id == assigned_agent_id]

        # 更新时间倒序
        tickets.sort(key=lambda t: t.updated_at, reverse=True)

        total = len(tickets)
        paginated = tickets[offset:offset + limit]
        return total, paginated

    def list_archived(
        self,
        *,
        email: Optional[str] = None,
        start_ts: Optional[float] = None,
        end_ts: Optional[float] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[int, List[Ticket]]:
        ids = self._load_all_ids()
        archived: List[Ticket] = []
        for ticket_id in ids:
            ticket = self._load_ticket(ticket_id)
            if not ticket or ticket.status != TicketStatus.ARCHIVED:
                continue
            if email and (not ticket.customer or (ticket.customer.email or "").lower() != email.lower()):
                continue
            created = ticket.created_at
            if start_ts and created < start_ts:
                continue
            if end_ts and created > end_ts:
                continue
            archived.append(ticket)

        archived.sort(key=lambda t: t.archived_at or t.created_at, reverse=True)
        total = len(archived)
        paginated = archived[offset:offset + limit]
        return total, paginated

    def get(self, ticket_id: str) -> Optional[Ticket]:
        return self._load_ticket(ticket_id)

    def update_ticket(
        self,
        ticket_id: str,
        *,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_agent_id: Optional[str] = None,
        assigned_agent_name: Optional[str] = None,
        note: Optional[str] = None,
        metadata_updates: Optional[dict] = None,
        changed_by: str = "system",
        change_reason: Optional[str] = None,
    ) -> Optional[Ticket]:
        ticket = self._load_ticket(ticket_id)
        if not ticket:
            return None

        updated = False
        if ticket.status == TicketStatus.ARCHIVED:
            raise ValueError("ARCHIVED_TICKET: 已归档工单不可编辑")

        if status and ticket.status != status:
            ticket.add_status_history(
                from_status=ticket.status,
                to_status=status,
                changed_by=changed_by,
                change_reason=change_reason,
                comment=note
            )
            ticket.status = status
            if status == TicketStatus.CLOSED:
                ticket.closed_at = time.time()
            if status == TicketStatus.IN_PROGRESS and not ticket.first_response_at:
                ticket.first_response_at = time.time()
            if status == TicketStatus.RESOLVED:
                ticket.resolved_at = time.time()
            elif status in (TicketStatus.PENDING, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_CUSTOMER, TicketStatus.WAITING_VENDOR):
                ticket.resolved_at = None
            elif status != TicketStatus.CLOSED:
                ticket.closed_at = None
            if status == TicketStatus.ARCHIVED:
                ticket.archived_at = time.time()
            updated = True
        if priority and ticket.priority != priority:
            ticket.priority = priority
            updated = True
        if assigned_agent_id is not None:
            if ticket.assigned_agent_id != assigned_agent_id or ticket.assigned_agent_name != assigned_agent_name:
                ticket.assigned_agent_id = assigned_agent_id
                ticket.assigned_agent_name = assigned_agent_name
                ticket.add_assignment_record(
                    agent_id=assigned_agent_id,
                    agent_name=assigned_agent_name,
                    assigned_by=changed_by,
                    note=note
                )
                updated = True
        if metadata_updates:
            ticket.metadata.update(metadata_updates)
            updated = True
        if note:
            notes = ticket.metadata.setdefault("notes", [])
            notes.append({
                "note": note,
                "timestamp": time.time()
            })
            updated = True

        if updated:
            ticket.updated_at = time.time()
            self._save_ticket(ticket)

        return ticket

    def add_comment(
        self,
        ticket_id: str,
        *,
        content: str,
        author_id: str,
        author_name: Optional[str],
        comment_type: TicketCommentType = TicketCommentType.INTERNAL,
        mentions: Optional[List[str]] = None
    ) -> Optional[TicketComment]:
        ticket = self._load_ticket(ticket_id)
        if not ticket:
            return None
        if ticket.status == TicketStatus.ARCHIVED:
            raise ValueError("ARCHIVED_TICKET: 无法对归档工单添加评论")

        comment = ticket.add_comment(
            content=content,
            author_id=author_id,
            author_name=author_name,
            comment_type=comment_type,
            mentions=mentions
        )
        ticket.updated_at = time.time()
        self._save_ticket(ticket)
        return comment

    def delete_comment(self, ticket_id: str, comment_id: str) -> bool:
        ticket = self._load_ticket(ticket_id)
        if not ticket:
            return False
        for idx, comment in enumerate(ticket.comments):
            if comment.comment_id == comment_id:
                del ticket.comments[idx]
                ticket.updated_at = time.time()
                self._save_ticket(ticket)
                return True
        return False

    def list_comments(self, ticket_id: str) -> Optional[List[TicketComment]]:
        ticket = self._load_ticket(ticket_id)
        if not ticket:
            return None
        return ticket.comments

    def reopen_ticket(
        self,
        ticket_id: str,
        *,
        agent_id: str,
        reason: str,
        comment: Optional[str] = None
    ) -> Ticket:
        ticket = self._load_ticket(ticket_id)
        if not ticket:
            raise ValueError("TICKET_NOT_FOUND")
        if ticket.status == TicketStatus.ARCHIVED:
            raise ValueError("TICKET_ARCHIVED: 已归档工单无法重开")
        if ticket.status != TicketStatus.CLOSED:
            raise ValueError("INVALID_STATUS: 仅已关闭工单可重开")
        if ticket.closed_at and (time.time() - ticket.closed_at) > 30 * 86400:
            raise ValueError("TIME_LIMIT_EXCEEDED: 超过30天无法重开")

        ticket.reopened_count += 1
        ticket.reopened_at = time.time()
        ticket.reopened_by = agent_id
        ticket.closed_at = None
        previous_status = ticket.status
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.add_status_history(
            from_status=previous_status,
            to_status=TicketStatus.IN_PROGRESS,
            changed_by=agent_id,
            change_reason=f"reopen: {reason}",
            comment=comment
        )
        if comment:
            notes = ticket.metadata.setdefault("notes", [])
            notes.append({
                "note": comment,
                "timestamp": ticket.reopened_at,
                "type": "reopen"
            })
        ticket.updated_at = ticket.reopened_at
        self._save_ticket(ticket)
        return ticket

    def archive_ticket(
        self,
        ticket_id: str,
        *,
        agent_id: str = "system",
        reason: Optional[str] = None
    ) -> Ticket:
        ticket = self._load_ticket(ticket_id)
        if not ticket:
            raise ValueError("TICKET_NOT_FOUND")
        if ticket.status != TicketStatus.CLOSED:
            raise ValueError("INVALID_STATUS: 仅已关闭工单可归档")

        ticket.status = TicketStatus.ARCHIVED
        ticket.archived_at = time.time()
        ticket.add_status_history(
            from_status=TicketStatus.CLOSED,
            to_status=TicketStatus.ARCHIVED,
            changed_by=agent_id,
            change_reason=reason or "archive",
            comment=None
        )
        ticket.updated_at = ticket.archived_at
        self._save_ticket(ticket)
        return ticket

    def auto_archive_closed(
        self,
        *,
        older_than_seconds: int = 30 * 86400,
        agent_id: str = "system"
    ) -> Dict[str, Any]:
        """自动归档关闭超过阈值的工单"""
        now = time.time()
        archived = []
        for ticket_id in self._load_all_ids():
            ticket = self._load_ticket(ticket_id)
            if not ticket:
                continue
            if ticket.status != TicketStatus.CLOSED:
                continue
            if not ticket.closed_at:
                continue
            if (now - ticket.closed_at) < older_than_seconds:
                continue
            ticket = self.archive_ticket(
                ticket_id,
                agent_id=agent_id,
                reason=f"auto_archive_{older_than_seconds//86400}d"
            )
            archived.append(ticket.ticket_id)

        return {
            "archived_count": len(archived),
            "ticket_ids": archived
        }

    def search(self, query: str, *, limit: int = 50) -> tuple[int, List[Ticket]]:
        """根据关键词搜索工单"""
        if not query or not query.strip():
            return 0, []

        limit = max(1, min(limit, 200))
        normalized = query.strip()
        normalized_upper = normalized.upper()
        normalized_lower = normalized.lower()

        # 精确匹配：工单ID
        ticket = self.get(normalized_upper)
        if not ticket and normalized_upper != normalized:
            ticket = self.get(normalized)
        if ticket:
            return 1, [ticket]

        all_tickets: List[Ticket] = []
        for ticket_id in self._load_all_ids():
            loaded = self._load_ticket(ticket_id)
            if loaded:
                all_tickets.append(loaded)

        # 精确匹配：订单号
        if normalized_upper.startswith("ORD"):
            order_matches: List[Ticket] = []
            order_keys = [
                "order_id",
                "order_number",
                "related_order_id",
                "order_no",
                "shopify_order_id"
            ]
            for ticket in all_tickets:
                metadata = ticket.metadata or {}
                for key in order_keys:
                    value = metadata.get(key)
                    if value and str(value).upper() == normalized_upper:
                        order_matches.append(ticket)
                        break
            order_matches.sort(key=lambda t: t.updated_at, reverse=True)
            return len(order_matches), order_matches[:limit]

        results: List[Ticket] = []
        for ticket in all_tickets:
            searchable_fields = self._ticket_searchable_strings(ticket)
            if any(
                normalized_lower in field.lower()
                for field in searchable_fields
                if field
            ):
                results.append(ticket)

        results.sort(key=lambda t: t.updated_at, reverse=True)
        total = len(results)
        limited = results[:limit]
        return total, limited

    def filter_tickets(
        self,
        *,
        statuses: Optional[List[TicketStatus]] = None,
        priorities: Optional[List[TicketPriority]] = None,
        ticket_types: Optional[List[TicketType]] = None,
        assigned: Optional[str] = None,
        assigned_agent_ids: Optional[List[str]] = None,
        keyword: Optional[str] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        created_start: Optional[float] = None,
        created_end: Optional[float] = None,
        updated_start: Optional[float] = None,
        updated_end: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        sort_desc: bool = True,
        current_agent_id: Optional[str] = None
    ) -> tuple[int, List[Ticket]]:
        """多条件筛选工单"""
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        statuses_set = set(statuses) if statuses else None
        priorities_set = set(priorities) if priorities else None
        types_set = set(ticket_types) if ticket_types else None
        assigned_ids_set = {agent_id for agent_id in (assigned_agent_ids or []) if agent_id}
        keyword_lower = keyword.strip().lower() if keyword and keyword.strip() else None
        tags_set = {tag.lower() for tag in (tags or []) if tag}
        categories_set = {cat.lower() for cat in (categories or []) if cat}

        filtered: List[Ticket] = []
        for ticket_id in self._load_all_ids():
            ticket = self._load_ticket(ticket_id)
            if not ticket:
                continue

            if statuses_set and ticket.status not in statuses_set:
                continue
            if priorities_set and ticket.priority not in priorities_set:
                continue
            if types_set and ticket.ticket_type not in types_set:
                continue

            if assigned_ids_set:
                if (ticket.assigned_agent_id or "") not in assigned_ids_set:
                    continue

            if assigned:
                if assigned == "unassigned":
                    if ticket.assigned_agent_id:
                        continue
                elif assigned == "mine":
                    if not current_agent_id or ticket.assigned_agent_id != current_agent_id:
                        continue
                else:
                    if ticket.assigned_agent_id != assigned:
                        continue

            if created_start is not None and ticket.created_at < created_start:
                continue
            if created_end is not None and ticket.created_at > created_end:
                continue
            if updated_start is not None and ticket.updated_at < updated_start:
                continue
            if updated_end is not None and ticket.updated_at > updated_end:
                continue

            if tags_set:
                metadata_tags = (ticket.metadata or {}).get("tags", [])
                if isinstance(metadata_tags, str):
                    metadata_values = [metadata_tags]
                elif isinstance(metadata_tags, dict):
                    metadata_values = list(metadata_tags.values())
                elif isinstance(metadata_tags, list):
                    metadata_values = metadata_tags
                else:
                    metadata_values = []
                normalized_tags = {str(tag).lower() for tag in metadata_values if tag}
                if not normalized_tags.intersection(tags_set):
                    continue

            if categories_set:
                metadata = ticket.metadata or {}
                category_values: List[str] = []
                if "category" in metadata and metadata["category"]:
                    category_values.append(str(metadata["category"]))
                categories_value = metadata.get("categories")
                if isinstance(categories_value, str):
                    category_values.append(categories_value)
                elif isinstance(categories_value, list):
                    category_values.extend(str(item) for item in categories_value if item)
                elif isinstance(categories_value, dict):
                    category_values.extend(str(item) for item in categories_value.values() if item)
                normalized_categories = {value.lower() for value in category_values if value}
                if not normalized_categories.intersection(categories_set):
                    continue

            if keyword_lower:
                searchable_fields = self._ticket_searchable_strings(ticket)
                if not any(keyword_lower in field.lower() for field in searchable_fields):
                    continue

            filtered.append(ticket)

        priority_weight = {
            TicketPriority.URGENT: 4,
            TicketPriority.HIGH: 3,
            TicketPriority.MEDIUM: 2,
            TicketPriority.LOW: 1
        }
        status_weight = {
            TicketStatus.PENDING: 6,
            TicketStatus.IN_PROGRESS: 5,
            TicketStatus.WAITING_CUSTOMER: 4,
            TicketStatus.WAITING_VENDOR: 3,
            TicketStatus.RESOLVED: 2,
            TicketStatus.CLOSED: 1,
            TicketStatus.ARCHIVED: 0
        }

        def sort_key(ticket: Ticket):
            if sort_by == "priority":
                return priority_weight.get(ticket.priority, 0)
            if sort_by == "status":
                return status_weight.get(ticket.status, 0)

            value = getattr(ticket, sort_by, None)
            if value is None:
                return 0
            if isinstance(value, TicketStatus):
                return status_weight.get(value, 0)
            if isinstance(value, TicketPriority):
                return priority_weight.get(value, 0)
            return value

        filtered.sort(key=sort_key, reverse=sort_desc)

        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        return total, paginated

    def get_sla_summary(self) -> Dict[str, Any]:
        """计算工单 SLA 概览"""
        ids = self._load_all_ids()
        total = 0
        first_response_sum = 0.0
        first_response_count = 0
        resolution_sum = 0.0
        resolution_count = 0
        open_tickets = 0
        pending_tickets = 0

        for ticket_id in ids:
            ticket = self._load_ticket(ticket_id)
            if not ticket:
                continue
            total += 1
            if ticket.first_response_at:
                first_response_sum += ticket.first_response_at - ticket.created_at
                first_response_count += 1
            if ticket.resolved_at:
                resolution_sum += ticket.resolved_at - ticket.created_at
                resolution_count += 1
            if ticket.status in {
                TicketStatus.PENDING,
                TicketStatus.IN_PROGRESS,
                TicketStatus.WAITING_CUSTOMER,
                TicketStatus.WAITING_VENDOR
            }:
                open_tickets += 1
            if ticket.status == TicketStatus.PENDING:
                pending_tickets += 1

        avg_first = (first_response_sum / first_response_count) if first_response_count else None
        avg_resolution = (resolution_sum / resolution_count) if resolution_count else None

        return {
            "total_tickets": total,
            "open_tickets": open_tickets,
            "pending_tickets": pending_tickets,
            "first_response_count": first_response_count,
            "avg_first_response_seconds": avg_first,
            "resolution_count": resolution_count,
            "avg_resolution_seconds": avg_resolution
        }

    def detect_sla_alerts(
        self,
        *,
        critical_first_response_seconds: int = 600,
        critical_resolution_seconds: int = 86400
    ) -> Dict[str, Any]:
        """检测超出 SLA 的工单"""
        now = time.time()
        first_response_alerts = []
        resolution_alerts = []

        for ticket_id in self._load_all_ids():
            ticket = self._load_ticket(ticket_id)
            if not ticket:
                continue
            if not ticket.first_response_at:
                elapsed = now - ticket.created_at
                if elapsed > critical_first_response_seconds:
                    first_response_alerts.append({
                        "ticket_id": ticket.ticket_id,
                        "elapsed_seconds": elapsed,
                        "priority": ticket.priority
                    })
            if ticket.status in {
                TicketStatus.PENDING,
                TicketStatus.IN_PROGRESS,
                TicketStatus.WAITING_CUSTOMER,
                TicketStatus.WAITING_VENDOR
            }:
                elapsed = now - ticket.created_at
                if elapsed > critical_resolution_seconds:
                    resolution_alerts.append({
                        "ticket_id": ticket.ticket_id,
                        "elapsed_seconds": elapsed,
                        "priority": ticket.priority
                    })

        return {
            "first_response_alerts": first_response_alerts,
            "resolution_alerts": resolution_alerts
        }

    def batch_assign(
        self,
        ticket_ids: List[str],
        *,
        assigned_agent_id: str,
        assigned_agent_name: Optional[str],
        changed_by: str,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量指派工单

        Args:
            ticket_ids: 工单ID列表
            assigned_agent_id: 目标坐席ID
            assigned_agent_name: 目标坐席姓名
            changed_by: 操作者
            note: 备注
        """
        updated_tickets: List[Ticket] = []
        failures: List[Dict[str, str]] = []

        for ticket_id in ticket_ids:
            try:
                ticket = self.update_ticket(
                    ticket_id,
                    assigned_agent_id=assigned_agent_id,
                    assigned_agent_name=assigned_agent_name,
                    note=note,
                    changed_by=changed_by,
                    change_reason="batch_assign"
                )
                if ticket:
                    updated_tickets.append(ticket)
                else:
                    failures.append({
                        "ticket_id": ticket_id,
                        "error": "TICKET_NOT_FOUND"
                    })
            except ValueError as exc:
                failures.append({
                    "ticket_id": ticket_id,
                    "error": str(exc)
                })

        return {
            "tickets": updated_tickets,
            "failed": failures
        }

    def batch_close(
        self,
        ticket_ids: List[str],
        *,
        reason: Optional[str],
        comment: Optional[str],
        changed_by: str
    ) -> Dict[str, Any]:
        """
        批量关闭工单（仅支持已解决状态）
        """
        successes: List[Ticket] = []
        failures: List[Dict[str, str]] = []

        for ticket_id in ticket_ids:
            ticket = self._load_ticket(ticket_id)
            if not ticket:
                failures.append({"ticket_id": ticket_id, "error": "TICKET_NOT_FOUND"})
                continue
            if ticket.status != TicketStatus.RESOLVED:
                failures.append({
                    "ticket_id": ticket_id,
                    "error": "INVALID_STATUS: 仅已解决工单可关闭"
                })
                continue

            try:
                updated = self.update_ticket(
                    ticket_id,
                    status=TicketStatus.CLOSED,
                    note=comment,
                    changed_by=changed_by,
                    change_reason=reason or "batch_close"
                )
                if updated:
                    successes.append(updated)
                else:
                    failures.append({"ticket_id": ticket_id, "error": "UNKNOWN_ERROR"})
            except ValueError as exc:
                failures.append({"ticket_id": ticket_id, "error": str(exc)})

        return {
            "tickets": successes,
            "failed": failures
        }

    def batch_update_priority(
        self,
        ticket_ids: List[str],
        *,
        priority: TicketPriority,
        reason: Optional[str],
        changed_by: str
    ) -> Dict[str, Any]:
        """批量调整优先级"""
        successes: List[Ticket] = []
        failures: List[Dict[str, str]] = []

        for ticket_id in ticket_ids:
            try:
                ticket = self.update_ticket(
                    ticket_id,
                    priority=priority,
                    changed_by=changed_by,
                    change_reason=reason or "batch_priority"
                )
                if ticket:
                    successes.append(ticket)
                else:
                    failures.append({"ticket_id": ticket_id, "error": "TICKET_NOT_FOUND"})
            except ValueError as exc:
                failures.append({"ticket_id": ticket_id, "error": str(exc)})

        return {
            "tickets": successes,
            "failed": failures
        }
