// Agent 相关类型
export interface AgentInfo {
  id: string
  name: string
}

export interface LoginRequest {
  agentId: string
  agentName: string
}

// Session 相关类型
export type SessionStatus = 'bot_active' | 'pending_manual' | 'manual_live' | 'after_hours_email' | 'closed'

// 【模块2】优先级等级
export type PriorityLevel = 'urgent' | 'high' | 'normal'

// 【模块2】优先级信息
export interface PriorityInfo {
  level: PriorityLevel
  is_vip: boolean
  wait_time_seconds: number
  is_timeout: boolean  // 等待超过5分钟
  is_repeat: boolean   // 二次转接
  urgent_keywords: string[]
}

export interface SessionSummary {
  session_name: string
  status: SessionStatus
  user_profile?: {
    nickname?: string
    vip?: boolean
  }
  updated_at: number
  last_message_preview?: {
    role: string
    content: string
    timestamp: number
  }
  escalation?: {
    reason: string
    trigger_at: number
    waiting_seconds: number
  }
  assigned_agent?: AgentInfo | null
  // 【模块2】优先级信息（可选，只在队列中有）
  priority?: PriorityInfo
}

export interface SessionListResponse {
  success: boolean
  data: {
    sessions: SessionSummary[]
    total: number
    limit: number
    offset: number
    has_more: boolean
  }
}

// Message 相关类型
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'agent' | 'system'
  content: string
  timestamp: number
  agent_id?: string
  agent_name?: string
}

export interface SessionDetail {
  session_name: string
  conversation_id?: string  // Coze 对话 ID
  status: SessionStatus
  history: Message[]
  escalation?: {
    reason: string
    details: string
    severity: string
    trigger_at: number
  }
  assigned_agent?: AgentInfo | null
  user_profile?: {
    nickname?: string
    vip?: boolean
  }
}

export interface SessionDetailResponse {
  success: boolean
  data: {
    session: SessionDetail
    audit_trail: any[]
  }
}

// API 请求类型
export interface TakeoverRequest {
  agent_id: string
  agent_name: string
}

export interface ReleaseRequest {
  agent_id: string
  reason: string
}

export interface ManualMessageRequest {
  session_name: string
  role: 'agent' | 'user'
  content: string
  agent_info?: {
    agent_id: string
    agent_name: string
  }
}

export interface ManualMessageResponse {
  success: boolean
  data: {
    timestamp: number
  }
}

// 协助请求类型
export type AssistStatus = 'pending' | 'answered'

export interface AssistRequest {
  id: string
  session_name: string
  requester: string
  assistant: string
  question: string
  answer?: string | null
  status: AssistStatus
  created_at: number
  answered_at?: number | null
}

// 会话转接相关
export interface TransferHistoryRecord {
  id: string
  session_name: string
  from_agent: string
  from_agent_name?: string
  to_agent: string
  to_agent_name?: string
  reason: string
  note?: string
  transferred_at: number
  accepted: boolean
  decision: 'accepted' | 'declined' | 'expired'
  responded_at?: number
  response_note?: string
}

export interface TransferRequest {
  id: string
  session_name: string
  from_agent_id: string
  from_agent_name?: string
  to_agent_id: string
  to_agent_name?: string
  reason: string
  note?: string
  status: 'pending'
  created_at: number
}

// ====================
// 管理员功能类型定义 (v3.1.3+)
// ====================

/** 坐席角色 */
export type AgentRole = 'admin' | 'agent'

/** 坐席状态 */
export type AgentStatus = 'online' | 'busy' | 'break' | 'lunch' | 'training' | 'offline'

/** 坐席工作状态详情 */
export interface AgentStatusDetails {
  status: AgentStatus
  status_note: string
  status_updated_at: number
  last_active_at: number
  current_sessions: number
  max_sessions: number
  today_stats: {
    processed_count: number
    avg_response_time: number
    avg_duration: number
    satisfaction_score: number
  }
}

/** 完整坐席信息 */
export interface Agent {
  id: string
  username: string
  name: string
  role: AgentRole
  status: AgentStatus
  status_note?: string
  status_updated_at?: number
  last_active_at?: number
  max_sessions: number
  created_at: number
  last_login: number
  avatar_url?: string
}

/** 创建坐席请求 */
export interface CreateAgentRequest {
  username: string
  password: string
  name: string
  role: AgentRole
  max_sessions?: number
  avatar_url?: string
}

/** 修改坐席请求 */
export interface UpdateAgentRequest {
  name?: string
  role?: AgentRole
  status?: AgentStatus
  max_sessions?: number
  avatar_url?: string
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/** 修改资料请求 */
export interface UpdateProfileRequest {
  name?: string
  avatar_url?: string
}

/** 重置密码请求 */
export interface ResetPasswordRequest {
  new_password: string
}

/** 坐席列表响应 */
export interface AgentsListResponse {
  success: boolean
  data: {
    items: Agent[]
    total: number
    page: number
    page_size: number
  }
}

/** 坐席操作响应 */
export interface AgentResponse {
  success: boolean
  agent?: Agent
  message?: string
}

// ====================
// 客户信息与业务上下文类型定义 (v3.2.0+)
// ====================

/** 来源渠道 */
export type SourceChannel = 'shopify_organic' | 'shopify_campaign' | 'amazon' | 'dealer' | 'other'

/** 客户画像 */
export interface CustomerProfile {
  customer_id: string
  name: string
  email: string
  phone: string
  country: string
  city: string
  language_preference: string  // en/de/fr/it/es
  payment_currency: string     // EUR/GBP
  source_channel: SourceChannel
  gdpr_consent: boolean
  marketing_subscribed: boolean
  vip_status?: string
  avatar_url?: string
  created_at: number
}

/** 客户画像响应 */
export interface CustomerProfileResponse {
  success: boolean
  data: CustomerProfile
}

// ====================
// 【模块2】队列管理类型定义
// ====================

/** 队列会话信息 */
export interface QueueSessionInfo {
  session_name: string
  position: number
  priority_level: PriorityLevel
  is_vip: boolean
  wait_time_seconds: number
  is_timeout: boolean
  urgent_keywords: string[]
  user_profile: {
    nickname: string
    vip: boolean
  }
  last_message: string
}

/** 队列响应 */
export interface QueueResponse {
  success: boolean
  data: {
    queue: QueueSessionInfo[]
    total_count: number
    vip_count: number
    avg_wait_time: number
    max_wait_time: number
  }
}
