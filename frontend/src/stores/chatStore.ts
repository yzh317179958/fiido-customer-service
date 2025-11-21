import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Message,
  BotConfig,
  SessionStatus,
  EscalationInfo,
  AgentInfo,
  EscalationReason
} from '@/types'

export const useChatStore = defineStore('chat', () => {
  // ============ 原有状态 ============
  const messages = ref<Message[]>([])
  const isLoading = ref(false)

  // ⚠️ 重要修复：使用内存中的随机 ID，确保每个标签页都是独立会话
  // 不使用 sessionStorage（标签页可能共享）
  // 每次刷新页面或打开新标签页都会生成新的 session_id
  const sessionId = ref(generateSessionId())

  // conversation_id 只保存在内存中，不持久化
  const conversationId = ref<string>('')
  const isChatOpen = ref(false)
  const isFirstMessage = ref(true)

  const botConfig = ref<BotConfig>({
    name: 'Fiido 客服',
    icon_url: '',
    description: 'Fiido 智能客服助手',
    welcome: '您好！我是Fiido智能客服助手,很高兴为您服务。请问有什么可以帮助您的？'
  })

  // ============ 人工接管状态（新增）============

  /**
   * 会话状态
   * - bot_active: AI 服务中
   * - pending_manual: 等待人工接入
   * - manual_live: 人工服务中
   * - after_hours_email: 非工作时间（邮件）
   * - closed: 已关闭
   */
  const sessionStatus = ref<SessionStatus>('bot_active')

  /**
   * 人工升级信息
   * 记录触发人工接管的原因、严重程度等
   */
  const escalationInfo = ref<EscalationInfo | null>(null)

  /**
   * 当前坐席信息
   * 当状态为 manual_live 时，记录当前服务的坐席
   */
  const agentInfo = ref<AgentInfo | null>(null)

  /**
   * 是否正在转人工中
   */
  const isEscalating = ref(false)

  // ============ 原有计算属性 ============
  const hasMessages = computed(() => messages.value.length > 0)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])

  // ============ 人工接管计算属性（新增）============

  /**
   * 是否处于人工模式（等待或进行中）
   */
  const isManualMode = computed(() => {
    return sessionStatus.value === 'pending_manual' ||
           sessionStatus.value === 'manual_live'
  })

  /**
   * 是否可以发送消息
   * - 不在加载中
   * - 不在等待人工状态
   * - 不在已关闭状态
   */
  const canSendMessage = computed(() => {
    return !isLoading.value &&
           sessionStatus.value !== 'pending_manual' &&
           sessionStatus.value !== 'closed'
  })

  /**
   * 是否可以转人工
   * - 当前状态为 bot_active
   * - 不在转人工中
   */
  const canEscalate = computed(() => {
    return sessionStatus.value === 'bot_active' && !isEscalating.value
  })

  /**
   * 状态显示文本
   */
  const statusText = computed(() => {
    switch (sessionStatus.value) {
      case 'bot_active':
        return 'AI 服务中'
      case 'pending_manual':
        return '等待人工接入'
      case 'manual_live':
        return agentInfo.value
          ? `人工客服 ${agentInfo.value.name}`
          : '人工服务中'
      case 'after_hours_email':
        return '非工作时间（已转邮件）'
      case 'closed':
        return '会话已关闭'
      default:
        return 'AI 服务中'
    }
  })

  /**
   * 状态显示颜色类
   */
  const statusColorClass = computed(() => {
    switch (sessionStatus.value) {
      case 'bot_active':
        return 'status-ai'
      case 'pending_manual':
        return 'status-pending'
      case 'manual_live':
        return 'status-manual'
      case 'after_hours_email':
        return 'status-email'
      case 'closed':
        return 'status-closed'
      default:
        return 'status-ai'
    }
  })

  // ============ 原有方法 ============
  function generateSessionId(): string {
    // 生成完全随机的 session_id，确保每个标签页/窗口都不同
    const id = `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}_${Math.random().toString(36).substring(2, 15)}`
    console.log('🆕 生成新会话 ID:', id)
    console.log('💡 提示：每个标签页/窗口都有独立的 session_id，实现完全隔离')
    return id
  }

  function addMessage(message: Message) {
    messages.value.push(message)
    if (isFirstMessage.value) {
      isFirstMessage.value = false
    }
  }

  function updateLastMessage(content: string) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content += content
    }
  }

  function clearMessages() {
    messages.value = []
    isFirstMessage.value = true
    console.log('🗑️  清空聊天记录')
  }

  function setConversationId(id: string) {
    conversationId.value = id
    // 不持久化，只保存在内存中
    console.log('💬 设置 Conversation ID:', id)
  }

  function setBotConfig(config: Partial<BotConfig>) {
    botConfig.value = { ...botConfig.value, ...config }
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function toggleChat() {
    isChatOpen.value = !isChatOpen.value
  }

  function openChat() {
    isChatOpen.value = true
  }

  function closeChat() {
    isChatOpen.value = false
  }

  // ============ 人工接管方法（新增）============

  /**
   * 更新会话状态
   * @param status 新的会话状态
   */
  function updateSessionStatus(status: SessionStatus) {
    const oldStatus = sessionStatus.value
    sessionStatus.value = status
    console.log(`📊 会话状态变更: ${oldStatus} → ${status}`)
  }

  /**
   * 设置人工升级信息
   * @param info 升级信息
   */
  function setEscalationInfo(info: EscalationInfo) {
    escalationInfo.value = info
    console.log('🚨 人工升级信息:', info)
  }

  /**
   * 设置坐席信息
   * @param agent 坐席信息
   */
  function setAgentInfo(agent: AgentInfo | null) {
    agentInfo.value = agent
    if (agent) {
      console.log(`👤 坐席已接入: ${agent.name} (${agent.id})`)
    } else {
      console.log('👤 坐席已离开')
    }
  }

  /**
   * 转人工
   * @param reason 转人工原因（默认为用户手动请求）
   * @returns Promise<boolean> 是否成功
   */
  async function escalateToManual(reason: EscalationReason = 'manual'): Promise<boolean> {
    if (!canEscalate.value) {
      console.warn('⚠️  当前状态不允许转人工')
      return false
    }

    isEscalating.value = true

    try {
      const response = await fetch('/api/manual/escalate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_name: sessionId.value,
          reason
        })
      })

      const data = await response.json()

      if (data.success && data.data) {
        // 更新状态
        updateSessionStatus(data.data.status)

        // 设置升级信息
        if (data.data.escalation) {
          setEscalationInfo(data.data.escalation)
        }

        console.log('✅ 转人工成功')
        return true
      } else {
        console.error('❌ 转人工失败:', data.error)
        return false
      }
    } catch (error) {
      console.error('❌ 转人工请求异常:', error)
      return false
    } finally {
      isEscalating.value = false
    }
  }

  /**
   * 刷新会话状态
   * 从服务器获取最新的会话状态
   * @returns Promise<boolean> 是否成功
   */
  async function refreshSessionStatus(): Promise<boolean> {
    try {
      const response = await fetch(`/api/sessions/${sessionId.value}`)

      if (!response.ok) {
        // 404 表示会话不存在，这是正常的（新会话）
        if (response.status === 404) {
          console.log('💡 会话不存在，保持当前状态')
          return true
        }
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      if (data.success && data.data && data.data.session) {
        const session = data.data.session

        // 更新状态
        updateSessionStatus(session.status)

        // 更新升级信息
        if (session.escalation) {
          setEscalationInfo(session.escalation)
        }

        // 更新坐席信息
        if (session.assigned_agent) {
          setAgentInfo(session.assigned_agent)
        } else {
          setAgentInfo(null)
        }

        console.log('🔄 会话状态已刷新')
        return true
      }

      return false
    } catch (error) {
      console.error('❌ 刷新会话状态失败:', error)
      return false
    }
  }

  /**
   * 重置人工接管状态
   * 用于新会话或会话结束时
   */
  function resetManualState() {
    sessionStatus.value = 'bot_active'
    escalationInfo.value = null
    agentInfo.value = null
    isEscalating.value = false
    console.log('🔄 人工接管状态已重置')
  }

  return {
    // 原有状态
    messages,
    isLoading,
    sessionId,
    conversationId,
    botConfig,
    isChatOpen,
    isFirstMessage,

    // 原有计算属性
    hasMessages,
    lastMessage,

    // 人工接管状态（新增）
    sessionStatus,
    escalationInfo,
    agentInfo,
    isEscalating,

    // 人工接管计算属性（新增）
    isManualMode,
    canSendMessage,
    canEscalate,
    statusText,
    statusColorClass,

    // 原有方法
    addMessage,
    updateLastMessage,
    clearMessages,
    setConversationId,
    setBotConfig,
    setLoading,
    toggleChat,
    openChat,
    closeChat,
    generateSessionId,

    // 人工接管方法（新增）
    updateSessionStatus,
    setEscalationInfo,
    setAgentInfo,
    escalateToManual,
    refreshSessionStatus,
    resetManualState
  }
})

