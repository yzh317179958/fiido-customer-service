"""
工单存储管理模块

提供工单的CRUD操作、查询过滤、版本控制等功能
支持内存存储(MVP)和Redis存储(未来扩展)
"""

import asyncio
import time
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from src.ticket_model import (
    Ticket, TicketStatus, TicketCategory, TicketPriority,
    Department, Activity, Comment, Attachment,
    calculate_sla_deadline, calculate_sla_status, SLAStatus
)


class TicketStore(ABC):
    """工单存储抽象类"""

    @abstractmethod
    async def create(self, ticket: Ticket) -> Ticket:
        """创建工单"""
        pass

    @abstractmethod
    async def get(self, ticket_id: str) -> Optional[Ticket]:
        """获取工单"""
        pass

    @abstractmethod
    async def update(self, ticket: Ticket) -> Ticket:
        """更新工单"""
        pass

    @abstractmethod
    async def delete(self, ticket_id: str) -> bool:
        """删除工单"""
        pass

    @abstractmethod
    async def list(
        self,
        status: Optional[TicketStatus] = None,
        department: Optional[Department] = None,
        assignee_id: Optional[str] = None,
        category: Optional[TicketCategory] = None,
        priority: Optional[TicketPriority] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """查询工单列表"""
        pass

    @abstractmethod
    async def get_by_session(self, session_id: str) -> Optional[Ticket]:
        """根据session_id获取工单"""
        pass


class InMemoryTicketStore(TicketStore):
    """内存工单存储 (MVP)"""

    def __init__(self):
        self._store: Dict[str, Ticket] = {}
        self._lock = asyncio.Lock()
        self._counter = 0  # 工单编号计数器

    def _generate_ticket_number(self) -> str:
        """生成工单编号 TK-YYYYNNNNN"""
        self._counter += 1
        year = datetime.now().year
        return f"TK-{year}{self._counter:05d}"

    async def create(self, ticket: Ticket) -> Ticket:
        """创建工单"""
        async with self._lock:
            # 生成工单编号
            if not ticket.ticket_number:
                ticket.ticket_number = self._generate_ticket_number()

            # 计算SLA
            if not ticket.sla_deadline:
                ticket.sla_deadline = calculate_sla_deadline(
                    ticket.category,
                    ticket.priority,
                    ticket.created_at
                )

            ticket.sla_status = calculate_sla_status(ticket.sla_deadline)

            # 保存
            self._store[ticket.ticket_id] = ticket

            # 添加创建活动日志
            activity = Activity(
                id=f"activity_{uuid.uuid4().hex[:16]}",
                action="created",
                description=f"工单创建: {ticket.title}",
                operator_id=ticket.created_by,
                operator_name=ticket.created_by_name,
                timestamp=ticket.created_at,
                details={
                    "category": ticket.category,
                    "priority": ticket.priority,
                    "department": ticket.department
                }
            )
            ticket.activity_log.append(activity)

            return ticket

    async def get(self, ticket_id: str) -> Optional[Ticket]:
        """获取工单"""
        async with self._lock:
            ticket = self._store.get(ticket_id)
            if ticket:
                # 更新SLA状态
                ticket.sla_status = calculate_sla_status(ticket.sla_deadline)
            return ticket

    async def update(self, ticket: Ticket) -> Ticket:
        """更新工单 (带版本检查)"""
        async with self._lock:
            current = self._store.get(ticket.ticket_id)

            if not current:
                raise ValueError(f"工单不存在: {ticket.ticket_id}")

            # 版本检查 (乐观锁)
            if current.version != ticket.version:
                raise ValueError("工单已被其他操作修改,请刷新后重试")

            # 递增版本号
            ticket.version += 1
            ticket.updated_at = datetime.now(timezone.utc).timestamp()

            # 更新SLA状态
            ticket.sla_status = calculate_sla_status(ticket.sla_deadline)

            self._store[ticket.ticket_id] = ticket
            return ticket

    async def delete(self, ticket_id: str) -> bool:
        """删除工单"""
        async with self._lock:
            if ticket_id in self._store:
                del self._store[ticket_id]
                return True
            return False

    async def list(
        self,
        status: Optional[TicketStatus] = None,
        department: Optional[Department] = None,
        assignee_id: Optional[str] = None,
        category: Optional[TicketCategory] = None,
        priority: Optional[TicketPriority] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """查询工单列表"""
        async with self._lock:
            # 过滤
            filtered = list(self._store.values())

            if status:
                filtered = [t for t in filtered if t.status == status]

            if department:
                filtered = [t for t in filtered if t.department == department]

            if assignee_id:
                filtered = [t for t in filtered if t.assignee_id == assignee_id]

            if category:
                filtered = [t for t in filtered if t.category == category]

            if priority:
                filtered = [t for t in filtered if t.priority == priority]

            # 排序 (优先级降序, 创建时间降序)
            priority_order = {
                TicketPriority.URGENT: 4,
                TicketPriority.HIGH: 3,
                TicketPriority.NORMAL: 2,
                TicketPriority.LOW: 1
            }

            filtered.sort(
                key=lambda t: (
                    -priority_order.get(t.priority, 0),
                    -t.created_at
                ),
                reverse=False
            )

            # 分页
            total = len(filtered)
            start = (page - 1) * page_size
            end = start + page_size
            items = filtered[start:end]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }

    async def get_by_session(self, session_id: str) -> Optional[Ticket]:
        """根据session_id获取工单"""
        async with self._lock:
            for ticket in self._store.values():
                if ticket.session_id == session_id:
                    return ticket
            return None

    async def add_comment(self, ticket_id: str, comment: Comment, operator_id: str, operator_name: str) -> Ticket:
        """添加评论"""
        ticket = await self.get(ticket_id)
        if not ticket:
            raise ValueError(f"工单不存在: {ticket_id}")

        ticket.comments.append(comment)

        # 添加活动日志
        activity = Activity(
            id=f"activity_{uuid.uuid4().hex[:16]}",
            action="commented",
            description=f"{operator_name} 添加了评论",
            operator_id=operator_id,
            operator_name=operator_name,
            timestamp=comment.created_at,
            details={"comment_id": comment.id}
        )
        ticket.activity_log.append(activity)

        return await self.update(ticket)

    async def add_attachment(self, ticket_id: str, attachment: Attachment, operator_id: str, operator_name: str) -> Ticket:
        """添加附件"""
        ticket = await self.get(ticket_id)
        if not ticket:
            raise ValueError(f"工单不存在: {ticket_id}")

        ticket.attachments.append(attachment)

        # 添加活动日志
        activity = Activity(
            id=f"activity_{uuid.uuid4().hex[:16]}",
            action="attachment_added",
            description=f"{operator_name} 上传了附件: {attachment.filename}",
            operator_id=operator_id,
            operator_name=operator_name,
            timestamp=attachment.uploaded_at,
            details={"attachment_id": attachment.id}
        )
        ticket.activity_log.append(activity)

        return await self.update(ticket)

    async def assign(self, ticket_id: str, assignee_id: str, assignee_name: str, department: Department, operator_id: str, operator_name: str) -> Ticket:
        """指派工单"""
        ticket = await self.get(ticket_id)
        if not ticket:
            raise ValueError(f"工单不存在: {ticket_id}")

        old_assignee = ticket.assignee_name or "未分配"

        ticket.assignee_id = assignee_id
        ticket.assignee_name = assignee_name
        ticket.department = department

        # 添加活动日志
        activity = Activity(
            id=f"activity_{uuid.uuid4().hex[:16]}",
            action="assigned",
            description=f"工单从 {old_assignee} 指派给 {assignee_name} ({department})",
            operator_id=operator_id,
            operator_name=operator_name,
            timestamp=time.time(),
            details={
                "from_assignee": old_assignee,
                "to_assignee": assignee_name,
                "department": department
            }
        )
        ticket.activity_log.append(activity)

        return await self.update(ticket)

    async def update_status(self, ticket_id: str, new_status: TicketStatus, operator_id: str, operator_name: str, comment: Optional[str] = None) -> Ticket:
        """更新状态"""
        ticket = await self.get(ticket_id)
        if not ticket:
            raise ValueError(f"工单不存在: {ticket_id}")

        old_status = ticket.status
        ticket.status = new_status

        current_time = time.time()

        # 更新时间戳
        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = current_time
        elif new_status == TicketStatus.CLOSED:
            ticket.closed_at = current_time

        # 添加活动日志
        activity = Activity(
            id=f"activity_{uuid.uuid4().hex[:16]}",
            action="status_changed",
            description=f"状态从 {old_status} 变更为 {new_status}",
            operator_id=operator_id,
            operator_name=operator_name,
            timestamp=current_time,
            details={
                "from_status": old_status,
                "to_status": new_status,
                "comment": comment
            }
        )
        ticket.activity_log.append(activity)

        return await self.update(ticket)


# 全局工单存储实例
_ticket_store: Optional[TicketStore] = None


def get_ticket_store() -> TicketStore:
    """获取工单存储实例"""
    global _ticket_store
    if _ticket_store is None:
        _ticket_store = InMemoryTicketStore()
    return _ticket_store


def set_ticket_store(store: TicketStore):
    """设置工单存储实例 (用于测试或切换Redis存储)"""
    global _ticket_store
    _ticket_store = store
