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

const isUser = computed(() => props.message.role === 'user')
const isDivider = computed(() => (props.message as any).isDivider === true)

const formattedTime = computed(() => {
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

const renderedContent = computed(() => {
  if (isUser.value) {
    return props.message.content
  }
  // Render markdown for bot messages
  return marked.parse(props.message.content)
})

const avatarContent = computed(() => {
  if (isUser.value) {
    return '我'
  }
  return chatStore.botConfig.name.charAt(0)
})

const senderName = computed(() => {
  if (isUser.value) {
    return '我'
  }
  return chatStore.botConfig.name
})
</script>

<template>
  <!-- Divider message -->
  <div v-if="isDivider" class="divider-message">
    <div class="divider-line"></div>
    <span class="divider-text">{{ message.content }}</span>
    <div class="divider-line"></div>
  </div>

  <!-- Normal message -->
  <div v-else class="message" :class="{ user: isUser, bot: !isUser }">
    <div class="message-avatar">
      <img
        v-if="!isUser && chatStore.botConfig.icon_url"
        :src="chatStore.botConfig.icon_url"
        :alt="chatStore.botConfig.name"
      >
      <template v-else>{{ avatarContent }}</template>
    </div>
    <div class="message-body">
      <div class="message-header">
        <span class="message-sender">{{ senderName }}</span>
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
/* Divider styles */
.divider-message {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
  padding: 0 10px;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, transparent, #d0d0d0, transparent);
}

.divider-text {
  color: #999;
  font-size: 12px;
  white-space: nowrap;
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

.message.user {
  flex-direction: row-reverse;
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
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.message-avatar:hover {
  transform: scale(1.15) rotate(5deg);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 50%;
  transition: transform 0.3s ease;
}

.message-avatar:hover img {
  transform: scale(1.1);
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 75%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.message.user .message-header {
  flex-direction: row-reverse;
}

.message-sender {
  font-weight: 600;
  color: #333;
}

.message-time {
  color: #999;
  font-size: 11px;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.6;
}

.message.user .message-content {
  background: #333;
  color: #fff;
  border-bottom-right-radius: 0;
}

.message.bot .message-content {
  background: #fff;
  color: #000;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 0;
}

/* Markdown styles */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin-top: 12px;
  margin-bottom: 8px;
  font-weight: 600;
}

.message-content :deep(h3) {
  font-size: 1.1em;
}

.message-content :deep(p) {
  margin: 6px 0;
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
  color: #1a1a1a;
}

.message-content :deep(a) {
  color: #1a1a1a;
  text-decoration: underline;
}

.message-content :deep(code) {
  background: #f0f0f0;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.9em;
}
</style>
