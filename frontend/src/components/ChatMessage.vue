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
/* Premium Message Styles */
.system-message {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  margin: 16px 0;
}

.system-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
}

.system-text {
  color: #9ca3af;
  font-size: 12px;
  white-space: nowrap;
  font-weight: 500;
  padding: 4px 12px;
  background: #f9fafb;
  border-radius: 12px;
}

/* Message base styles */
.message {
  margin-bottom: 16px;
  display: flex;
  gap: 10px;
  animation: messageSlideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
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
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-weight: 600;
  font-size: 12px;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.message-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

/* Agent avatar */
.message-avatar.agent-avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 75%;
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
  font-weight: 500;
  color: #6b7280;
}

.message-sender.agent-name {
  font-weight: 600;
  color: #10b981;
}

.agent-badge {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(16, 185, 129, 0.3);
}

.message-time {
  color: #9ca3af;
  font-size: 11px;
  font-weight: 400;
}

.message-content {
  padding: 10px 14px;
  border-radius: 14px;
  word-wrap: break-word;
  line-height: 1.5;
  font-size: 14px;
  position: relative;
}

.message.user .message-content {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25), 0 1px 3px rgba(59, 130, 246, 0.15);
}

.message.user .message-content::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 100%);
  border-radius: inherit;
  pointer-events: none;
}

.message.bot .message-content {
  background: linear-gradient(to bottom, #f9fafb 0%, #f3f4f6 100%);
  color: #111827;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
}

.message.agent .message-content {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2), 0 1px 3px rgba(16, 185, 129, 0.1);
  border: 1px solid #a7f3d0;
}

/* Markdown styles */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin-top: 10px;
  margin-bottom: 6px;
  font-weight: 600;
  color: inherit;
}

.message-content :deep(h3) {
  font-size: 1em;
}

.message-content :deep(p) {
  margin: 4px 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 6px 0;
  padding-left: 18px;
}

.message-content :deep(li) {
  margin: 3px 0;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message.user .message-content :deep(strong) {
  color: #ffffff;
}

.message-content :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
  transition: color 0.2s;
}

.message-content :deep(a:hover) {
  color: #2563eb;
}

.message.user .message-content :deep(a) {
  color: #dbeafe;
}

.message.user .message-content :deep(a:hover) {
  color: #ffffff;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.message.user .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}
</style>
