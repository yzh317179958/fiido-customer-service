<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { Message } from '@/types'
import { useChatStore } from '@/stores/chatStore'

interface Props {
  message: Message
}

const props = defineProps<Props>()
const chatStore = useChatStore()

// Configure marked for rendering markdown
marked.setOptions({
  breaks: true,
  gfm: true,
})

// 判断消息类型
const isUser = computed(() => props.message.role === 'user')
const isAgent = computed(() => props.message.role === 'agent')
const isSystem = computed(() => props.message.role === 'system')
const isDivider = computed(() => (props.message as any).isDivider === true)

const formattedTime = computed(() => {
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

const renderedContent = computed(() => {
  if (isUser.value) {
    return props.message.content
  }
  // Render markdown for bot and agent messages
  return marked.parse(props.message.content)
})

// 头像内容
const avatarContent = computed(() => {
  if (isUser.value) {
    return '我'
  }
  if (isAgent.value) {
    return '👤'  // 人工客服图标
  }
  return chatStore.botConfig.name.charAt(0)
})

// 发送者名称
const senderName = computed(() => {
  if (isUser.value) {
    return '我'
  }
  if (isAgent.value) {
    return props.message.agent_info?.name || '客服'
  }
  return chatStore.botConfig.name
})
</script>

<template>
  <!-- System message (包括分隔线) -->
  <div v-if="isSystem || isDivider" class="system-message">
    <div class="system-divider"></div>
    <span class="system-text">{{ message.content }}</span>
    <div class="system-divider"></div>
  </div>

  <!-- Normal message (用户、AI、人工) -->
  <div v-else class="message" :class="{ user: isUser, bot: !isUser && !isAgent, agent: isAgent }">
    <div class="message-avatar" :class="{ 'agent-avatar': isAgent }">
      <img
        v-if="!isUser && !isAgent"
        src="/fiido2.png"
        :alt="chatStore.botConfig.name"
      >
      <template v-else>{{ avatarContent }}</template>
    </div>
    <div class="message-body">
      <div class="message-header">
        <span class="message-sender" :class="{ 'agent-name': isAgent }">{{ senderName }}</span>
        <span v-if="isAgent" class="agent-badge">人工</span>
        <span class="message-time">{{ formattedTime }}</span>
      </div>
      <div class="message-content" v-if="isUser">
        {{ renderedContent }}
      </div>
      <div class="message-content" v-else v-html="renderedContent"></div>
    </div>
  </div>
</template>

<style scoped>
/* System message styles */
.system-message {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  margin: 12px 0;
}

.system-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #d1d5db, transparent);
}

.system-text {
  color: #9ca3af;
  font-size: 12px;
  white-space: nowrap;
  font-weight: 500;
}

/* Message base styles */
.message {
  margin-bottom: 18px;
  display: flex;
  gap: 12px;
  animation: messageSlideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1f2937;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 2px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.message-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 50%;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);
  color: white;
}

/* Agent avatar - 渐变紫色 */
.message-avatar.agent-avatar {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  font-size: 18px;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding-left: 2px;
}

.message.user .message-header {
  flex-direction: row-reverse;
  padding-left: 0;
  padding-right: 2px;
}

.message-sender {
  font-weight: 600;
  color: #4b5563;
}

/* Agent name - 蓝色加粗 */
.message-sender.agent-name {
  font-weight: 600;
  color: #6366f1;
  font-size: 13px;
}

/* Agent badge - 人工标签 */
.agent-badge {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.message-time {
  color: #9ca3af;
  font-size: 11px;
  font-weight: 400;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.message.user .message-content {
  background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.message.bot .message-content {
  background: #ffffff;
  color: #1f2937;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

/* Agent message - 浅蓝色背景 + 左侧渐变边框 */
.message.agent .message-content {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #1f2937;
  border-left: 3px solid transparent;
  border-image: linear-gradient(180deg, #6366f1 0%, #8b5cf6 100%);
  border-image-slice: 1;
  border-radius: 16px 16px 16px 4px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.12);
}

/* Markdown styles */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin-top: 12px;
  margin-bottom: 8px;
  font-weight: 600;
  color: inherit;
}

.message-content :deep(h3) {
  font-size: 1.05em;
}

.message-content :deep(p) {
  margin: 4px 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message.user .message-content :deep(strong) {
  color: #ffffff;
}

.message-content :deep(a) {
  color: #6366f1;
  text-decoration: underline;
  transition: color 0.2s;
}

.message-content :deep(a:hover) {
  color: #8b5cf6;
}

.message.user .message-content :deep(a) {
  color: #93c5fd;
}

.message.user .message-content :deep(a:hover) {
  color: #bfdbfe;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.message.user .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.15);
}
</style>
