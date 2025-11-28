<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import { clearConversationHistory } from '@/api/chat'
import ChatMessage from './ChatMessage.vue'
import WelcomeScreen from './WelcomeScreen.vue'
import StatusBar from './StatusBar.vue'

const chatStore = useChatStore()
const chatInput = ref('')
const chatMessagesRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const showMenu = ref(false)
let statusPollInterval: number | null = null

const API_BASE_URL = computed(() => `http://${window.location.hostname}:8000`)

// 🔴 P0-9.5: 输入框禁用逻辑
const isInputDisabled = computed(() => {
  return chatStore.isLoading || chatStore.sessionStatus === 'closed'
})

// 🔴 P0-9.6: 动态 placeholder
const inputPlaceholder = computed(() => {
  switch (chatStore.sessionStatus) {
    case 'bot_active':
      return '请输入您的问题...'
    case 'pending_manual':
      return '等待人工接入...'
    case 'manual_live':
      return '向客服发送消息...'
    case 'after_hours_email':
      return '非工作时间，请留言'
    case 'closed':
      return '会话已关闭'
    default:
      return '请输入消息...'
  }
})

// Auto-scroll to bottom
const scrollToBottom = () => {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

// Watch messages for auto-scroll
watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})

// Watch chat open state to focus input
watch(() => chatStore.isChatOpen, (isOpen) => {
  if (isOpen) {
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

const handleClose = () => {
  chatStore.closeChat()
  showMenu.value = false
}

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const closeMenu = () => {
  showMenu.value = false
}

const handleNewConversation = async () => {
  closeMenu()

  if (!confirm('确定要开始新对话吗？当前对话记录将被清空。')) {
    return
  }

  try {
    console.log('🆕 创建新对话...')

    const response = await fetch(`${API_BASE_URL.value}/api/conversation/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatStore.sessionId })
    })

    const data = await response.json()

    if (data.success && data.conversation_id) {
      chatStore.setConversationId(data.conversation_id)
      chatStore.clearMessages()
      console.log('✅ 新对话已创建:', data.conversation_id)
      alert('✅ 新对话已创建！')
    } else {
      alert('❌ 创建新对话失败: ' + (data.error || '未知错误'))
      console.error('创建新对话失败:', data)
    }
  } catch (error) {
    alert('❌ 请求失败: ' + (error as Error).message)
    console.error('创建新对话异常:', error)
  }
}

const handleClearConversation = () => {
  closeMenu()

  // 添加分隔线消息
  chatStore.addMessage({
    id: `divider-${Date.now()}`,
    content: '--- 历史对话分隔线 ---',
    role: 'system',
    timestamp: new Date(),
    sender: 'System',
    isDivider: true
  })
  console.log('🗑️  已添加历史对话分隔线')
}

const handleNewSession = async () => {
  closeMenu()

  // 立即清空界面，无需等待
  chatStore.clearMessages()
  console.log('🔄 创建新会话...')

  // 异步调用后端创建新会话，不阻塞UI
  try {
    const response = await fetch(`${API_BASE_URL.value}/api/conversation/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatStore.sessionId })
    })

    const data = await response.json()

    if (data.success && data.conversation_id) {
      chatStore.setConversationId(data.conversation_id)
      console.log('✅ 新会话已创建, Conversation ID:', data.conversation_id)
    } else {
      console.error('⚠️  创建新会话失败:', data)
    }
  } catch (error) {
    console.error('❌ 创建新会话异常:', error)
  }
}

const handleEscalateToManual = async () => {
  closeMenu()

  if (!chatStore.canEscalate) {
    console.warn('⚠️  当前状态不允许转人工')
    return
  }

  if (!confirm('确定要转接人工客服吗？')) {
    return
  }

  try {
    console.log('🚀 发起转人工请求...')
    const success = await chatStore.escalateToManual('manual')

    if (success) {
      console.log('✅ 转人工成功')
      alert('✅ 已转接人工客服，请稍候...')

      // 添加系统消息提示
      chatStore.addMessage({
        id: `system-${Date.now()}`,
        content: '正在为您转接人工客服，请稍候...',
        role: 'system',
        timestamp: new Date(),
        sender: 'System'
      })
    } else {
      alert('❌ 转人工失败，请稍后重试')
      console.error('❌ 转人工失败')
    }
  } catch (error) {
    alert('❌ 请求失败: ' + (error as Error).message)
    console.error('❌ 转人工异常:', error)
  }
}

const sendMessage = async () => {
  if (chatStore.isLoading || !chatInput.value.trim()) return

  const message = chatInput.value.trim()
  chatInput.value = ''

  // 🔴 P0-9.1: 根据状态判断发送方式
  const status = chatStore.sessionStatus

  // Add user message
  chatStore.addMessage({
    id: Date.now().toString(),
    content: message,
    role: 'user',
    timestamp: new Date(),
    sender: '我'
  })

  chatStore.setLoading(true)

  try {
    // 🔴 P0-9.2: pending_manual状态 - 禁止发送
    if (status === 'pending_manual') {
      chatStore.addMessage({
        id: `system-${Date.now()}`,
        content: '正在为您转接人工客服，请稍候...',
        role: 'system',
        timestamp: new Date(),
        sender: 'System'
      })
      chatStore.setLoading(false)
      return
    }

    // 🔴 P0-9.3: manual_live状态 - 调用人工消息接口
    if (status === 'manual_live') {
      const response = await fetch(`${API_BASE_URL.value}/api/manual/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_name: chatStore.sessionId,
          role: 'user',
          content: message
        })
      })

      const data = await response.json()

      if (!data.success) {
        throw new Error(data.error || '发送失败')
      }

      console.log('✅ 人工模式消息已发送')
      chatStore.setLoading(false)
      return
    }

    // 🔴 P0-9.4: bot_active状态 - 调用AI接口（现有逻辑）
    const requestBody: any = {
      message,
      user_id: chatStore.sessionId
    }

    if (chatStore.conversationId) {
      requestBody.conversation_id = chatStore.conversationId
      console.log('💬 使用 Conversation ID:', chatStore.conversationId)
    }

    const response = await fetch(`${API_BASE_URL.value}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    // Add bot message placeholder
    const botMessage = {
      id: (Date.now() + 1).toString(),
      content: '',
      role: 'assistant' as const,
      timestamp: new Date(),
      sender: chatStore.botConfig.name
    }
    chatStore.addMessage(botMessage)

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) throw new Error('No reader available')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            // 🔴 P0-8.1: AI消息（现有逻辑）
            if (data.type === 'message') {
              chatStore.updateLastMessage(data.content)
              scrollToBottom()
            }

            // 🔴 P0-8.2: 错误消息（现有逻辑）
            else if (data.type === 'error') {
              chatStore.updateLastMessage('抱歉，发生了错误：' + data.content)

              // 如果是人工接管错误
              if (data.content === 'MANUAL_IN_PROGRESS') {
                chatStore.updateSessionStatus('manual_live')
              }
            }

            // 🔴 P0-8.3: 人工消息（新增）
            else if (data.type === 'manual_message') {
              if (data.role === 'agent') {
                // 坐席消息
                chatStore.addMessage({
                  id: Date.now().toString(),
                  content: data.content,
                  role: 'agent',
                  timestamp: new Date(data.timestamp * 1000),
                  agent_info: {
                    id: data.agent_id,
                    name: data.agent_name
                  }
                })
              } else if (data.role === 'system') {
                // 系统消息
                chatStore.addMessage({
                  id: `system-${Date.now()}`,
                  content: data.content,
                  role: 'system',
                  timestamp: new Date(data.timestamp * 1000),
                  sender: 'System'
                })
              }
              scrollToBottom()
              console.log('📨 收到人工消息:', data.role, data.content)
            }

            // 🔴 P0-8.4: 状态变化（新增）
            else if (data.type === 'status_change') {
              chatStore.updateSessionStatus(data.status)

              // 如果转为人工模式，保存坐席信息
              if (data.status === 'manual_live' && data.agent_info) {
                chatStore.setAgentInfo({
                  id: data.agent_info.agent_id,
                  name: data.agent_info.agent_name
                })
              }

              console.log('📊 SSE状态变化:', data.status)
            }
          } catch (e) {
            console.error('解析错误:', e)
          }
        }
      }
    }
  } catch (error) {
    console.error('错误:', error)
    chatStore.addMessage({
      id: `system-${Date.now()}`,
      content: '抱歉，发送失败，请稍后重试。',
      role: 'system',
      timestamp: new Date(),
      sender: 'System'
    })
  } finally {
    chatStore.setLoading(false)
    inputRef.value?.focus()
  }
}

const handleKeyPress = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// Initialize conversation on mount
const initializeConversation = async () => {
  try {
    console.log('🔄 初始化会话...')

    const response = await fetch(`${API_BASE_URL.value}/api/conversation/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatStore.sessionId })
    })

    const data = await response.json()

    if (data.success && data.conversation_id) {
      chatStore.setConversationId(data.conversation_id)
      console.log('✅ 会话初始化成功, Conversation ID:', data.conversation_id)
    } else {
      console.error('⚠️  会话初始化失败:', data)
    }
  } catch (error) {
    console.error('❌ 会话初始化异常:', error)
  }
}

// 🔴 P1-2: 加载会话历史（用户打开页面时回填历史消息）
const loadSessionHistory = async () => {
  try {
    console.log('📚 加载会话历史...')

    const response = await fetch(`${API_BASE_URL.value}/api/sessions/${chatStore.sessionId}`)

    // 404 表示新会话，无历史记录
    if (response.status === 404) {
      console.log('ℹ️  新会话，无历史记录')
      return
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    if (data.success && data.data.session) {
      const session = data.data.session

      // 1. 恢复会话状态
      if (session.status && session.status !== chatStore.sessionStatus) {
        chatStore.updateSessionStatus(session.status)
        console.log('✅ 恢复会话状态:', session.status)
      }

      // 2. 恢复升级信息
      if (session.escalation) {
        chatStore.setEscalationInfo({
          reason: session.escalation.reason,
          details: session.escalation.details || '',
          severity: session.escalation.severity || 'medium',
          trigger_at: session.escalation.trigger_at
        })
        console.log('✅ 恢复升级信息:', session.escalation.reason)
      }

      // 3. 恢复坐席信息
      if (session.assigned_agent) {
        chatStore.setAgentInfo({
          id: session.assigned_agent.id,
          name: session.assigned_agent.name
        })
        console.log('✅ 恢复坐席信息:', session.assigned_agent.name)
      }

      // 4. 恢复历史消息
      if (session.history && session.history.length > 0) {
        console.log(`📨 加载 ${session.history.length} 条历史消息`)

        // 按时间戳排序
        const sortedHistory = [...session.history].sort((a: any, b: any) =>
          a.timestamp - b.timestamp
        )

        // 添加历史消息到前端
        sortedHistory.forEach((msg: any) => {
          // 检查是否已存在（避免重复）
          const exists = chatStore.messages.some(
            m => Math.abs(m.timestamp.getTime() / 1000 - msg.timestamp) < 0.1 &&
                 m.content === msg.content
          )

          if (!exists) {
            let sender = 'System'
            if (msg.role === 'user') {
              sender = '我'
            } else if (msg.role === 'assistant') {
              sender = chatStore.botConfig.name
            } else if (msg.role === 'agent') {
              sender = msg.agent_name || '客服'
            }

            chatStore.addMessage({
              id: `history-${msg.role}-${msg.timestamp}`,
              content: msg.content,
              role: msg.role,
              timestamp: new Date(msg.timestamp * 1000),
              sender: sender,
              agent_info: msg.agent_id ? {
                id: msg.agent_id,
                name: msg.agent_name || '客服'
              } : undefined
            })
          }
        })

        console.log('✅ 历史消息加载完成')
        scrollToBottom()
      }

      // 5. 如果是人工模式，启动轮询
      if (session.status === 'pending_manual' || session.status === 'manual_live') {
        startStatusPolling()
      }
    }
  } catch (error) {
    console.error('⚠️  加载历史失败:', error)
  }
}

// Handle product inquiry from other components
onMounted(async () => {
  window.addEventListener('ask-product', ((e: CustomEvent) => {
    chatInput.value = `请介绍一下 ${e.detail} 的详细信息`
    sendMessage()
  }) as EventListener)

  // Load bot config
  loadBotConfig()

  // Initialize conversation immediately
  await initializeConversation()

  // 🔴 P1-2: 加载历史消息
  await loadSessionHistory()
})

const loadBotConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL.value}/api/bot/info`)
    const data = await response.json()

    if (data.success && data.bot) {
      chatStore.setBotConfig({
        name: data.bot.name || 'Fiido 客服',
        icon_url: data.bot.icon_url || '',
        description: data.bot.description || '',
        welcome: data.bot.welcome || '您好！我是Fiido智能客服助手,很高兴为您服务。请问有什么可以帮助您的？'
      })
      console.log('✅ Bot 配置加载成功:', chatStore.botConfig)
    }
  } catch (error) {
    console.error('⚠️  Bot 配置加载失败,使用默认配置:', error)
  }
}

// 🔴 新增: 轮询会话状态
const pollSessionStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL.value}/api/sessions/${chatStore.sessionId}`)

    if (response.status === 404) {
      // 会话不存在，这是正常情况（新会话）
      return
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    if (data.success && data.data.session) {
      const session = data.data.session
      const newStatus = session.status

      // 只在状态真正变化时更新
      if (newStatus !== chatStore.sessionStatus) {
        console.log(`🔄 状态轮询: ${chatStore.sessionStatus} → ${newStatus}`)
        chatStore.updateSessionStatus(newStatus)

        // 如果转为 manual_live，保存坐席信息
        if (newStatus === 'manual_live' && session.assigned_agent) {
          chatStore.setAgentInfo({
            id: session.assigned_agent.id,
            name: session.assigned_agent.name
          })
        }
      }

      // 🔴 新增: 同步历史消息（检查是否有新消息）
      if (session.history && session.history.length > 0) {
        // 获取后端最后一条消息
        const lastBackendMessage = session.history[session.history.length - 1]
        const lastBackendTimestamp = lastBackendMessage.timestamp

        // 获取前端最后一条消息
        const frontendMessages = chatStore.messages
        const lastFrontendMessage = frontendMessages.length > 0
          ? frontendMessages[frontendMessages.length - 1]
          : null

        const lastFrontendTimestamp = lastFrontendMessage
          ? lastFrontendMessage.timestamp.getTime() / 1000
          : 0

        // 如果后端有新消息（时间戳更新）
        if (lastBackendTimestamp > lastFrontendTimestamp) {
          console.log('📨 检测到新消息，同步历史')

          // 找出所有新消息（时间戳大于前端最后一条消息）
          const newMessages = session.history.filter((msg: any) =>
            msg.timestamp > lastFrontendTimestamp
          )

          // 添加新消息到前端
          newMessages.forEach((msg: any) => {
            // 检查是否已存在（避免重复）
            const exists = chatStore.messages.some(
              m => Math.abs(m.timestamp.getTime() / 1000 - msg.timestamp) < 0.1
            )

            if (!exists) {
              chatStore.addMessage({
                id: `${msg.role}-${msg.timestamp}`,
                content: msg.content,
                role: msg.role,
                timestamp: new Date(msg.timestamp * 1000),
                sender: msg.role === 'agent' ? (msg.agent_name || '客服') :
                        msg.role === 'user' ? '我' : 'System',
                agent_info: msg.agent_id ? {
                  id: msg.agent_id,
                  name: msg.agent_name || '客服'
                } : undefined
              })
              console.log(`✅ 添加新消息: ${msg.role} - ${msg.content.substring(0, 20)}...`)
            }
          })

          scrollToBottom()
        }
      }
    }
  } catch (error) {
    console.error('⚠️  状态轮询失败:', error)
  }
}

// 启动状态轮询（仅在 pending_manual 或 manual_live 状态下）
const startStatusPolling = () => {
  if (statusPollInterval !== null) {
    return // 已经在轮询
  }

  console.log('🔄 启动状态轮询')
  statusPollInterval = window.setInterval(() => {
    const status = chatStore.sessionStatus
    if (status === 'pending_manual' || status === 'manual_live') {
      pollSessionStatus()
    } else if (status === 'bot_active' || status === 'closed') {
      // 恢复到稳定状态，停止轮询
      stopStatusPolling()
    }
  }, 2000) // 每2秒轮询一次
}

// 停止状态轮询
const stopStatusPolling = () => {
  if (statusPollInterval !== null) {
    console.log('⏸️  停止状态轮询')
    clearInterval(statusPollInterval)
    statusPollInterval = null
  }
}

// 监听状态变化，自动启动/停止轮询
watch(() => chatStore.sessionStatus, (newStatus) => {
  if (newStatus === 'pending_manual' || newStatus === 'manual_live') {
    startStatusPolling()
  } else if (newStatus === 'bot_active' || newStatus === 'closed') {
    stopStatusPolling()
  }
})

// Close menu when clicking outside
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  // 如果点击的不是菜单容器内的元素，则关闭菜单
  if (!target.closest('.floating-menu-container')) {
    if (showMenu.value) {
      closeMenu()
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// 组件卸载时清理轮询
onUnmounted(() => {
  stopStatusPolling()
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div>
    <!-- Overlay -->
    <div
      class="chat-overlay"
      :class="{ show: chatStore.isChatOpen }"
      @click="handleClose"
    ></div>

    <!-- Chat Panel -->
    <div class="chat-panel" :class="{ open: chatStore.isChatOpen }">
      <div class="chat-header">
        <h2>{{ chatStore.botConfig.name }}</h2>
        <button class="chat-close" @click="handleClose">&times;</button>
      </div>

      <!-- Status Bar (新增) -->
      <StatusBar />

      <!-- Messages Area -->
      <div class="chat-messages" ref="chatMessagesRef">
        <WelcomeScreen v-if="chatStore.isFirstMessage && chatStore.messages.length === 0" />
        <ChatMessage
          v-for="message in chatStore.messages"
          :key="message.id"
          :message="message"
        />
        <!-- Typing Indicator -->
        <div v-if="chatStore.isLoading" class="message bot">
          <div class="message-avatar">
            <img src="/fiido2.png" :alt="chatStore.botConfig.name">
          </div>
          <div class="message-body">
            <div class="typing-indicator">
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="chat-input-area">
        <div class="chat-input-wrapper">
          <!-- Floating Action Menu -->
          <div class="floating-menu-container" @click.stop>
            <!-- Main Bubble Button -->
            <button class="main-bubble" @click="toggleMenu" :class="{ active: showMenu }">
              <svg v-if="!showMenu" class="plus-icon" viewBox="0 0 24 24">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
              </svg>
              <svg v-else class="close-icon" viewBox="0 0 24 24">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>

            <!-- Sub Bubbles -->
            <transition name="bubble">
              <div v-if="showMenu" class="sub-bubbles">
                <button
                  class="sub-bubble"
                  @click="handleEscalateToManual"
                  title="转人工客服"
                  :disabled="!chatStore.canEscalate"
                  :class="{ disabled: !chatStore.canEscalate }"
                >
                  <span class="bubble-text">转人工</span>
                </button>
                <button class="sub-bubble" @click="handleClearConversation" title="清除对话">
                  <span class="bubble-text">清除对话</span>
                </button>
                <button class="sub-bubble" @click="handleNewSession" title="新建对话">
                  <span class="bubble-text">新建对话</span>
                </button>
              </div>
            </transition>
          </div>

          <input
            ref="inputRef"
            v-model="chatInput"
            type="text"
            class="chat-input"
            :placeholder="inputPlaceholder"
            @keypress="handleKeyPress"
            :disabled="isInputDisabled"
          >
          <button
            class="chat-send"
            @click="sendMessage"
            :disabled="isInputDisabled || !chatInput.trim()"
          >
            <svg viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>

        <!-- 🔴 P0-9.7: 等待提示 -->
        <div v-if="chatStore.sessionStatus === 'pending_manual'" class="waiting-tip">
          <span class="tip-icon">⏳</span>
          <span>正在为您转接人工客服，请稍候...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Define CSS Variables for easier theme management */
:root {
  --primary-color: #6366f1; /* 现代紫蓝色 */
  --primary-hover-color: #818cf8; /* 浅紫蓝色 */
  --secondary-color: #ec4899; /* 粉红色 */
  --secondary-hover-color: #f472b6; /* 浅粉红色 */
  --header-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* 渐变紫色 */
  --header-text: #fff;
  --panel-bg: #ffffff;
  --chat-bg: #f9fafb; /* 极浅灰背景 */
  --input-border: #e5e7eb;
  --input-focus-border: var(--primary-color);
  --button-text: #fff;
  --button-disabled-bg: #f3f4f6;
  --button-disabled-border: #d1d5db;
  --button-disabled-text: #9ca3af;
  --warning-bg: #fef3c7; /* 柔和黄色 */
  --warning-text: #d97706; /* 橙色文字 */
  --shadow-light: rgba(99, 102, 241, 0.08);
  --shadow-medium: rgba(99, 102, 241, 0.12);
  --shadow-strong: rgba(99, 102, 241, 0.16);
}

.chat-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.6); /* Slightly darker overlay */
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease-in-out;
  z-index: 999;
}

.chat-overlay.show {
  opacity: 1;
  visibility: visible;
}

.chat-panel {
  position: fixed;
  top: 0;
  right: -450px;
  width: 420px;
  height: 100vh;
  background: var(--panel-bg);
  box-shadow: -8px 0 40px rgba(0, 0, 0, 0.08);
  transition: right 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-panel.open {
  right: 0;
}

.chat-header {
  background: var(--header-bg);
  color: var(--header-text);
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.chat-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 0.3px;
}

.chat-close {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: var(--header-text);
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-close:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: rotate(90deg);
}

/* Floating Action Menu */
.floating-menu-container {
  position: relative;
  display: flex;
  align-items: center;
  margin-right: 12px; /* Adjusted margin */
}

.main-bubble {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.main-bubble:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
}

.main-bubble.active {
  transform: rotate(45deg);
  background: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);
}

.main-bubble svg {
  width: 26px; /* Slightly larger icon */
  height: 26px; /* Slightly larger icon */
  fill: #fff;
  transition: transform 0.3s;
}

.sub-bubbles {
  position: absolute;
  left: 0;
  bottom: 60px; /* Adjusted position */
  display: flex;
  flex-direction: column;
  gap: 10px; /* Slightly more space */
  animation: bubbleSlideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 5;
}

@keyframes bubbleSlideUp {
  from {
    opacity: 0;
    transform: translateY(15px); /* Adjusted starting position */
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.bubble-enter-active,
.bubble-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.bubble-enter-from,
.bubble-leave-to {
  opacity: 0;
  transform: translateY(15px);
}

.sub-bubble {
  height: 40px;
  padding: 0 18px;
  border-radius: 20px;
  background: #ffffff;
  border: 1.5px solid #e5e7eb;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.sub-bubble:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-color: transparent;
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.25);
}

.sub-bubble:hover .bubble-text {
  color: var(--button-text);
}

.sub-bubble.disabled {
  background: var(--button-disabled-bg);
  border-color: var(--button-disabled-border);
  cursor: not-allowed;
  opacity: 0.7; /* Slightly less opaque */
  box-shadow: none; /* No shadow when disabled */
}

.sub-bubble.disabled:hover {
  transform: none;
  background: var(--button-disabled-bg);
}

.sub-bubble.disabled .bubble-text {
  color: var(--button-disabled-text);
}

.sub-bubble.disabled:hover .bubble-text {
  color: var(--button-disabled-text);
}

.bubble-text {
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
  transition: color 0.25s ease-in-out;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  background: var(--chat-bg);
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

.message {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.bot {
  flex-direction: row;
}

.message-avatar {
  width: 44px; /* Slightly larger */
  height: 44px; /* Slightly larger */
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--header-bg); /* Color from header */
  font-weight: 700;
  font-size: 15px; /* Slightly larger font */
  flex-shrink: 0;
  box-shadow: 0 2px 10px var(--shadow-light); /* Softer shadow */
  padding: 4px;
  overflow: hidden;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 50%;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 75%;
}

.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 14px 18px;
  background: #ffffff;
  border-radius: 16px;
  width: fit-content;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-5px);
  }
}

.chat-input-area {
  padding: 20px;
  background: var(--panel-bg);
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.04);
}

.chat-input-wrapper {
  display: flex;
  gap: 10px;
  align-items: center;
  position: relative;
}

.chat-input {
  flex: 1;
  padding: 12px 18px;
  border: 2px solid #e5e7eb;
  border-radius: 24px;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  color: #1f2937;
  background: #f9fafb;
  transition: all 0.2s ease-in-out;
}

.chat-input:focus {
  border-color: #6366f1;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.chat-send {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: var(--button-text);
  border: none;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
}

.chat-send:hover:not(:disabled) {
  transform: scale(1.05) translateY(-1px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
}

.chat-send:disabled {
  background: #e5e7eb;
  cursor: not-allowed;
  opacity: 0.6;
  box-shadow: none;
}

.chat-send svg {
  width: 22px; /* Slightly larger icon */
  height: 22px; /* Slightly larger icon */
  fill: #fff;
}

/* 🔴 P0-9.8: 等待提示样式 */
.waiting-tip {
  padding: 12px 16px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #d97706;
  margin-top: 12px;
  animation: fadeIn 0.3s ease-in;
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.1);
}

.tip-icon {
  font-size: 18px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .chat-panel {
    width: 100%;
    right: -100%;
  }
}
</style>
