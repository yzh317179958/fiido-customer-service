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
