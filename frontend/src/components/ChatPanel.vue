<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import { clearConversationHistory } from '@/api/chat'
import ChatMessage from './ChatMessage.vue'
import WelcomeScreen from './WelcomeScreen.vue'

const chatStore = useChatStore()
const chatInput = ref('')
const chatMessagesRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const showMenu = ref(false)

const API_BASE_URL = computed(() => `http://${window.location.hostname}:8000`)

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

const sendMessage = async () => {
  if (chatStore.isLoading || !chatInput.value.trim()) return

  const message = chatInput.value.trim()
  chatInput.value = ''

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

            if (data.type === 'message') {
              chatStore.updateLastMessage(data.content)
              scrollToBottom()
            } else if (data.type === 'error') {
              chatStore.updateLastMessage('抱歉，发生了错误：' + data.content)
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
      id: (Date.now() + 2).toString(),
      content: '抱歉，连接服务器失败，请稍后重试。',
      role: 'assistant',
      timestamp: new Date(),
      sender: chatStore.botConfig.name
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

// Handle product inquiry from other components
onMounted(() => {
  window.addEventListener('ask-product', ((e: CustomEvent) => {
    chatInput.value = `请介绍一下 ${e.detail} 的详细信息`
    sendMessage()
  }) as EventListener)

  // Load bot config
  loadBotConfig()

  // Initialize conversation immediately
  initializeConversation()
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
            <img v-if="chatStore.botConfig.icon_url" :src="chatStore.botConfig.icon_url" :alt="chatStore.botConfig.name">
            <template v-else>{{ chatStore.botConfig.name.charAt(0) }}</template>
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
            placeholder="请输入您的问题..."
            @keypress="handleKeyPress"
            :disabled="chatStore.isLoading"
          >
          <button
            class="chat-send"
            @click="sendMessage"
            :disabled="chatStore.isLoading || !chatInput.trim()"
          >
            <svg viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s;
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
  background: #fff;
  box-shadow: -5px 0 20px rgba(0,0,0,0.2);
  transition: right 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.chat-panel.open {
  right: 0;
}

.chat-header {
  background: #1a1a1a;
  color: #fff;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.chat-close {
  background: none;
  border: none;
  color: #fff;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.chat-close:hover {
  opacity: 0.8;
}

/* Floating Action Menu */
.floating-menu-container {
  position: relative;
  display: flex;
  align-items: center;
  margin-right: 10px;
}

.main-bubble {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.main-bubble:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
}

.main-bubble.active {
  transform: rotate(45deg);
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.main-bubble svg {
  width: 24px;
  height: 24px;
  fill: #fff;
  transition: transform 0.3s;
}

.sub-bubbles {
  position: absolute;
  left: 0;
  bottom: 55px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  animation: bubbleSlideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes bubbleSlideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
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
  transform: translateY(10px);
}

.sub-bubble {
  height: 40px;
  padding: 0 16px;
  border-radius: 20px;
  background: #fff;
  border: 2px solid #667eea;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s;
  white-space: nowrap;
}

.sub-bubble:hover {
  transform: scale(1.05);
  background: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.sub-bubble:hover .bubble-text {
  color: #fff;
}

.bubble-text {
  font-size: 14px;
  font-weight: 500;
  color: #667eea;
  transition: color 0.3s;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f9f9f9;
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
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1a1a1a;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  width: fit-content;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: #333;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-5px); }
}

.chat-input-area {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  background: #fff;
}

.chat-input-wrapper {
  display: flex;
  gap: 10px;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 25px;
  font-family: 'Montserrat', sans-serif;
  font-size: 14px;
  outline: none;
}

.chat-input:focus {
  border-color: #1a1a1a;
}

.chat-send {
  background: #1a1a1a;
  color: #fff;
  border: none;
  width: 45px;
  height: 45px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.chat-send:hover:not(:disabled) {
  background: #333;
  transform: scale(1.05);
}

.chat-send:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.chat-send svg {
  width: 20px;
  height: 20px;
  fill: #fff;
}

/* Responsive */
@media (max-width: 768px) {
  .chat-panel {
    width: 100%;
    right: -100%;
  }
}
</style>
