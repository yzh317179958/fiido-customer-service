export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant' | 'agent' | 'system'  // 扩展支持人工和系统消息
  timestamp: Date
  sender?: string
  agent_info?: AgentInfo  // 人工消息的坐席信息
  isDivider?: boolean     // 是否为分隔线消息
}

export interface BotConfig {
  name: string
  icon_url: string
  description: string
  welcome: string
}

export interface ChatRequest {
  message: string
  user_id: string
  conversation_id?: string
}

export interface ConversationResponse {
  success: boolean
  conversation_id?: string
  error?: string
}

export interface Product {
  id: string
  name: string
  price: string
  image: string
  badge?: string
  badgeType?: 'hot' | 'new' | 'premium'
}

// ============ 人工接管功能类型定义 ============

/**
 * 会话状态枚举
 */
export type SessionStatus =
  | 'bot_active'           // AI服务中
  | 'pending_manual'       // 等待人工接入
  | 'manual_live'          // 人工服务中
  | 'after_hours_email'    // 非工作时间（邮件）
  | 'closed'               // 已关闭

/**
 * 人工升级原因
 */
export type EscalationReason =
  | 'keyword'     // 关键词触发
  | 'fail_loop'   // AI连续失败
  | 'sentiment'   // 情绪检测
  | 'vip'         // VIP用户
  | 'manual'      // 用户手动请求

/**
 * 人工升级严重程度
 */
export type EscalationSeverity = 'low' | 'medium' | 'high'

/**
 * 坐席信息
 */
export interface AgentInfo {
  id: string        // 坐席ID
  name: string      // 坐席名称
  avatar?: string   // 坐席头像（可选）
}

/**
 * 人工升级信息
 */
export interface EscalationInfo {
  reason: EscalationReason      // 升级原因
  details: string               // 详细说明
  severity: EscalationSeverity  // 严重程度
  trigger_at: number            // 触发时间（UTC时间戳）
}

/**
 * SSE 事件类型
 */
export interface SSEEvent {
  type: 'message' | 'manual_message' | 'status_change' | 'error' | 'done'
  content?: string
  role?: 'agent' | 'user' | 'system'
  timestamp?: number
  agent_id?: string
  agent_name?: string
  status?: SessionStatus
  agent_info?: AgentInfo
}

/**
 * 人工升级请求
 */
export interface ManualEscalateRequest {
  session_name: string
  reason: EscalationReason
}

/**
 * 人工升级响应
 */
export interface ManualEscalateResponse {
  success: boolean
  data?: {
    session_name: string
    status: SessionStatus
    escalation: EscalationInfo
  }
  error?: string
}

/**
 * 会话状态响应
 */
export interface SessionStateResponse {
  success: boolean
  data?: {
    session: {
      session_name: string
      status: SessionStatus
      history: Array<{
        id: string
        role: string
        content: string
        timestamp: number
        agent_info?: AgentInfo
      }>
      escalation?: EscalationInfo
      assigned_agent?: AgentInfo
    }
    audit_trail: Array<{
      status_from: string
      status_to: string
      operator: string
      timestamp: number
    }>
  }
  error?: string
}
