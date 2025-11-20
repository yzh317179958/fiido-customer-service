import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, BotConfig } from '@/types'

export const useChatStore = defineStore('chat', () => {
  // State
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

  // Computed
  const hasMessages = computed(() => messages.value.length > 0)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])

  // Actions
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

  return {
    messages,
    isLoading,
    sessionId,
    conversationId,
    botConfig,
    isChatOpen,
    isFirstMessage,
    hasMessages,
    lastMessage,
    addMessage,
    updateLastMessage,
    clearMessages,
    setConversationId,
    setBotConfig,
    setLoading,
    toggleChat,
    openChat,
    closeChat,
    generateSessionId
  }
})


