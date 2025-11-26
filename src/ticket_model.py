"""
工单系统数据模型

提供工单、评论、附件、活动日志等数据结构定义
支持跨部门协作、流程流转、SLA管理等功能
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from enum import Enum
from datetime import datetime, timezone


class TicketCategory(str, Enum):
    """工单分类"""
    PRE_SALES = "pre_sales"           # 售前配置
    ORDER_MODIFY = "order_modify"     # 订单修改
    SHIPPING = "shipping"             # 物流异常
    AFTER_SALES = "after_sales"       # 售后维修
    COMPLIANCE = "compliance"         # 合规申诉
    TECHNICAL = "technical"           # 技术故障
    RETURNS = "returns"               # 退换货
    WARRANTY = "warranty"             # 保修


class TicketPriority(str, Enum):
    """工单优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    """工单状态"""
    PENDING = "pending"                       # 待接单
    IN_PROGRESS = "in_progress"               # 处理中
    WAITING_CUSTOMER = "waiting_customer"     # 待客户
    WAITING_PARTS = "waiting_parts"           # 待配件
    RESOLVED = "resolved"                     # 已解决
    CLOSED = "closed"                         # 已关闭


class Department(str, Enum):
    """部门"""
    SALES_EU = "sales_eu"           # 欧洲售前
    SERVICE_CN = "service_cn"       # 深圳售后
    WAREHOUSE = "warehouse"         # 配件仓
    COMPLIANCE = "compliance"       # 合规团队
    TECHNICAL = "technical"         # 技术支持
    LOGISTICS = "logistics"         # 物流团队


class SLAStatus(str, Enum):
    """SLA状态"""
    WITHIN = "within"         # 在SLA时间内
    WARNING = "warning"       # 即将超时(80%时间已用)
    BREACHED = "breached"     # 已超时


class Attachment(BaseModel):
    """附件"""
    id: str
    filename: str
    file_url: str
    file_size: int              # 字节
    content_type: str           # MIME类型
    uploaded_by: str            # 上传者
    uploaded_at: float          # UTC时间戳


class Comment(BaseModel):
    """评论"""
    id: str
    content: str
    author_id: str
    author_name: str
    mentions: List[str] = []    # @提到的用户ID列表
    created_at: float           # UTC时间戳
    is_internal: bool = False   # 是否内部评论(不向用户显示)


class Activity(BaseModel):
    """活动日志"""
    id: str
    action: str                 # "created", "status_changed", "assigned", "commented", etc.
    description: str
    operator_id: str
    operator_name: str
    timestamp: float            # UTC时间戳
    details: dict = {}          # 额外详情


class Ticket(BaseModel):
    """工单主模型"""

    # 基础信息
    ticket_id: str = Field(..., description="工单唯一ID")
    ticket_number: str = Field(..., description="显示编号 (TK-2023001)")
    title: str = Field(..., min_length=1, max_length=200, description="工单标题")
    description: str = Field(..., description="工单描述")

    # 关联信息
    session_id: Optional[str] = Field(None, description="关联的会话ID")
    customer_id: str = Field(..., description="客户ID")
    order_id: Optional[str] = Field(None, description="关联订单ID")
    bike_model: Optional[str] = Field(None, description="车型")
    vin: Optional[str] = Field(None, description="车辆VIN")

    # 分类与优先级
    category: TicketCategory = Field(..., description="工单分类")
    priority: TicketPriority = Field(default=TicketPriority.NORMAL, description="优先级")
    tags: List[str] = Field(default_factory=list, description="标签")

    # 状态与流转
    status: TicketStatus = Field(default=TicketStatus.PENDING, description="工单状态")
    assignee_id: Optional[str] = Field(None, description="当前负责人ID")
    assignee_name: Optional[str] = Field(None, description="当前负责人姓名")
    department: Department = Field(..., description="当前部门")
    created_by: str = Field(..., description="创建者ID")
    created_by_name: str = Field(..., description="创建者姓名")
    created_at: float = Field(..., description="创建时间(UTC时间戳)")
    updated_at: float = Field(..., description="更新时间(UTC时间戳)")
    resolved_at: Optional[float] = Field(None, description="解决时间(UTC时间戳)")
    closed_at: Optional[float] = Field(None, description="关闭时间(UTC时间戳)")

    # SLA
    sla_deadline: Optional[float] = Field(None, description="SLA截止时间(UTC时间戳)")
    sla_status: SLAStatus = Field(default=SLAStatus.WITHIN, description="SLA状态")

    # AI分析
    ai_summary: Optional[str] = Field(None, description="AI生成的摘要")
    customer_intent: Optional[str] = Field(None, description="客户诉求")
    ai_conclusion: Optional[str] = Field(None, description="AI处理结论")

    # 附件与评论
    attachments: List[Attachment] = Field(default_factory=list, description="附件列表")
    comments: List[Comment] = Field(default_factory=list, description="评论列表")
    activity_log: List[Activity] = Field(default_factory=list, description="活动日志")

    # 版本控制
    version: int = Field(default=0, description="版本号,用于乐观锁")


class CreateTicketRequest(BaseModel):
    """创建工单请求"""
    session_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    category: TicketCategory
    priority: TicketPriority = TicketPriority.NORMAL
    order_id: Optional[str] = None
    bike_model: Optional[str] = None
    vin: Optional[str] = None
    customer_id: str
    department: Department


class UpdateTicketRequest(BaseModel):
    """更新工单请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    tags: Optional[List[str]] = None


class AssignTicketRequest(BaseModel):
    """指派工单请求"""
    assignee_id: str
    assignee_name: str
    department: Department


class UpdateStatusRequest(BaseModel):
    """更新状态请求"""
    status: TicketStatus
    comment: Optional[str] = None


class AddCommentRequest(BaseModel):
    """添加评论请求"""
    content: str = Field(..., min_length=1)
    mentions: List[str] = Field(default_factory=list)
    is_internal: bool = False


class SLAConfig(BaseModel):
    """SLA配置"""
    category: TicketCategory
    priority: TicketPriority
    response_time_minutes: int    # 响应时间(分钟)
    resolution_time_minutes: int  # 解决时间(分钟)


# SLA配置表 (基于任务拆解文档)
DEFAULT_SLA_CONFIGS = [
    SLAConfig(category=TicketCategory.PRE_SALES, priority=TicketPriority.NORMAL, response_time_minutes=120, resolution_time_minutes=1440),
    SLAConfig(category=TicketCategory.ORDER_MODIFY, priority=TicketPriority.HIGH, response_time_minutes=30, resolution_time_minutes=240),
    SLAConfig(category=TicketCategory.SHIPPING, priority=TicketPriority.HIGH, response_time_minutes=60, resolution_time_minutes=720),
    SLAConfig(category=TicketCategory.AFTER_SALES, priority=TicketPriority.NORMAL, response_time_minutes=240, resolution_time_minutes=2880),
    SLAConfig(category=TicketCategory.TECHNICAL, priority=TicketPriority.URGENT, response_time_minutes=15, resolution_time_minutes=480),
    SLAConfig(category=TicketCategory.COMPLIANCE, priority=TicketPriority.HIGH, response_time_minutes=120, resolution_time_minutes=1440),
]


def get_sla_config(category: TicketCategory, priority: TicketPriority) -> Optional[SLAConfig]:
    """获取SLA配置"""
    for config in DEFAULT_SLA_CONFIGS:
        if config.category == category and config.priority == priority:
            return config
    return None


def calculate_sla_deadline(category: TicketCategory, priority: TicketPriority, created_at: float) -> float:
    """计算SLA截止时间"""
    config = get_sla_config(category, priority)
    if not config:
        # 默认24小时
        return created_at + 86400

    # resolution_time_minutes转换为秒
    return created_at + (config.resolution_time_minutes * 60)


def calculate_sla_status(deadline: float, current_time: Optional[float] = None) -> SLAStatus:
    """计算SLA状态"""
    if current_time is None:
        current_time = datetime.now(timezone.utc).timestamp()

    if current_time >= deadline:
        return SLAStatus.BREACHED

    time_remaining = deadline - current_time
    time_total = deadline - (deadline - time_remaining)  # 简化:直接用deadline作为基准

    # 如果剩余时间少于20%,显示warning
    # 这里简化处理:如果距离截止时间少于1小时,显示warning
    if time_remaining < 3600:
        return SLAStatus.WARNING

    return SLAStatus.WITHIN
