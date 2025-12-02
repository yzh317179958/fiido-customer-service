"""
工单系统数据模型

L1-2-Part1: 工单核心功能（最小可行版本）
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class TicketType(str, Enum):
    """工单类型"""
    PRE_SALE = "pre_sale"       # 售前咨询
    AFTER_SALE = "after_sale"   # 售后问题
    COMPLAINT = "complaint"     # 投诉与建议


class TicketStatus(str, Enum):
    """工单状态 - MVP 版本"""
    PENDING = "pending"              # 待处理（默认）
    IN_PROGRESS = "in_progress"      # 处理中
    WAITING_CUSTOMER = "waiting_customer"  # 等待客户反馈
    WAITING_VENDOR = "waiting_vendor"  # 等待第三方
    RESOLVED = "resolved"            # 已解决，等待关闭
    CLOSED = "closed"                # 已关闭
    ARCHIVED = "archived"            # 已归档


class TicketPriority(str, Enum):
    """工单优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCustomerInfo(BaseModel):
    """客户信息（可选）"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None


class TicketCommentType(str, Enum):
    INTERNAL = "internal"
    PUBLIC = "public"


class TicketComment(BaseModel):
    comment_id: str
    content: str
    author_id: str
    author_name: Optional[str] = None
    comment_type: TicketCommentType = TicketCommentType.INTERNAL
    created_at: float = Field(default_factory=lambda: time.time())
    ticket_id: Optional[str] = None
    mentions: List[str] = Field(default_factory=list)


class TicketAssignmentRecord(BaseModel):
    """工单指派历史"""
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    assigned_by: Optional[str] = None
    note: Optional[str] = None
    assigned_at: float = Field(default_factory=lambda: time.time())


class TicketStatusHistory(BaseModel):
    """工单状态历史记录"""
    history_id: str
    from_status: Optional[TicketStatus] = None
    to_status: TicketStatus
    changed_by: str
    change_reason: Optional[str] = None
    comment: Optional[str] = None
    changed_at: float = Field(default_factory=lambda: time.time())


class Ticket(BaseModel):
    """工单实体"""
    ticket_id: str
    title: str
    description: str
    session_name: Optional[str] = None  # 关联的会话ID
    ticket_type: TicketType = TicketType.AFTER_SALE
    status: TicketStatus = TicketStatus.PENDING
    priority: TicketPriority = TicketPriority.MEDIUM
    created_by: str
    created_by_name: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    customer: Optional[TicketCustomerInfo] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    history: List[TicketStatusHistory] = Field(default_factory=list)
    closed_at: Optional[float] = None
    archived_at: Optional[float] = None
    reopened_count: int = 0
    reopened_at: Optional[float] = None
    reopened_by: Optional[str] = None
    first_response_at: Optional[float] = None
    resolved_at: Optional[float] = None
    assignments: List[TicketAssignmentRecord] = Field(default_factory=list)
    comments: List[TicketComment] = Field(default_factory=list)
    created_at: float = Field(default_factory=lambda: time.time())
    updated_at: float = Field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, Any]:
        data = self.dict()
        if self.customer:
            data["customer"] = self.customer.dict()
        data["history"] = [record.dict() for record in self.history]
        data["assignments"] = [record.dict() for record in self.assignments]
        data["comments"] = [record.dict() for record in self.comments]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticket":
        if data.get("customer") and not isinstance(data["customer"], TicketCustomerInfo):
            data["customer"] = TicketCustomerInfo(**data["customer"])
        if data.get("history"):
            records = []
            for record in data["history"]:
                if not isinstance(record, TicketStatusHistory):
                    records.append(TicketStatusHistory(**record))
                else:
                    records.append(record)
            data["history"] = records
        if data.get("assignments"):
            assignment_records = []
            for record in data["assignments"]:
                if not isinstance(record, TicketAssignmentRecord):
                    assignment_records.append(TicketAssignmentRecord(**record))
                else:
                    assignment_records.append(record)
            data["assignments"] = assignment_records
        if data.get("comments"):
            comment_records = []
            for record in data["comments"]:
                if not isinstance(record, TicketComment):
                    comment_records.append(TicketComment(**record))
                else:
                    comment_records.append(record)
            data["comments"] = comment_records
        return cls(**data)

    def add_status_history(
        self,
        *,
        from_status: Optional[TicketStatus],
        to_status: TicketStatus,
        changed_by: str,
        change_reason: Optional[str] = None,
        comment: Optional[str] = None
    ):
        record = TicketStatusHistory(
            history_id=f"history_{uuid.uuid4().hex[:12]}",
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            change_reason=change_reason,
            comment=comment
        )
        self.history.append(record)

    def add_assignment_record(
        self,
        *,
        agent_id: Optional[str],
        agent_name: Optional[str],
        assigned_by: Optional[str],
        note: Optional[str] = None
    ):
        record = TicketAssignmentRecord(
            agent_id=agent_id,
            agent_name=agent_name,
            assigned_by=assigned_by,
            note=note
        )
        self.assignments.append(record)

    def add_comment(
        self,
        *,
        content: str,
        author_id: str,
        author_name: Optional[str],
        comment_type: TicketCommentType,
        mentions: Optional[List[str]] = None
    ) -> TicketComment:
        comment = TicketComment(
            comment_id=f"comment_{uuid.uuid4().hex[:12]}",
            content=content,
            author_id=author_id,
            author_name=author_name,
            comment_type=comment_type,
            ticket_id=self.ticket_id,
            mentions=self._normalize_mentions(mentions or [])
        )
        self.comments.append(comment)
        return comment

    @staticmethod
    def _normalize_mentions(mentions: List[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for mention in mentions:
            if mention is None:
                continue
            value = str(mention).strip()
            if not value or value in seen:
                continue
            normalized.append(value)
            seen.add(value)
        return normalized


def generate_ticket_id() -> str:
    """根据时间生成易读工单号"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"TKT-{timestamp}-{suffix}"
