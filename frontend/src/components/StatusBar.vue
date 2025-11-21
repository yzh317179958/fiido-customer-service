<template>
  <div class="status-bar" :class="statusColorClass">
    <div class="status-indicator">
      <div class="status-dot" :class="statusColorClass"></div>
      <span class="status-text">{{ statusText }}</span>
    </div>

    <!-- 显示坐席信息 (仅在 manual_live 状态下) -->
    <div v-if="agentInfo && sessionStatus === 'manual_live'" class="agent-info">
      <div class="agent-avatar">
        <img v-if="agentInfo.avatar" :src="agentInfo.avatar" :alt="agentInfo.name" />
        <span v-else class="agent-avatar-placeholder">{{ agentInfo.name[0] }}</span>
      </div>
    </div>

    <!-- 显示等待提示 (仅在 pending_manual 状态下) -->
    <div v-if="sessionStatus === 'pending_manual'" class="waiting-indicator">
      <div class="waiting-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

// 从 store 获取状态
const sessionStatus = computed(() => chatStore.sessionStatus)
const statusText = computed(() => chatStore.statusText)
const statusColorClass = computed(() => chatStore.statusColorClass)
const agentInfo = computed(() => chatStore.agentInfo)
</script>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
  transition: all 0.3s ease;
}

/* 状态指示器 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 状态点 */
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

/* AI 服务中 - 绿色 */
.status-ai .status-dot {
  background: #10b981;
}

.status-ai {
  background: linear-gradient(to right, #f0fdf4, #ffffff);
}

/* 等待人工 - 橙色 */
.status-pending .status-dot {
  background: #f59e0b;
}

.status-pending {
  background: linear-gradient(to right, #fffbeb, #ffffff);
}

/* 人工服务中 - 蓝色 */
.status-manual .status-dot {
  background: #3b82f6;
}

.status-manual {
  background: linear-gradient(to right, #eff6ff, #ffffff);
}

/* 非工作时间 - 灰色 */
.status-email .status-dot {
  background: #6b7280;
}

.status-email {
  background: linear-gradient(to right, #f9fafb, #ffffff);
}

/* 已关闭 - 红色 */
.status-closed .status-dot {
  background: #ef4444;
}

.status-closed {
  background: linear-gradient(to right, #fef2f2, #ffffff);
}

/* 状态文本 */
.status-text {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

/* 脉动动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

/* 坐席信息 */
.agent-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3b82f6;
  color: white;
  font-weight: 500;
  font-size: 14px;
}

.agent-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.agent-avatar-placeholder {
  text-transform: uppercase;
}

/* 等待指示器 */
.waiting-indicator {
  display: flex;
  align-items: center;
}

.waiting-dots {
  display: flex;
  gap: 4px;
}

.waiting-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f59e0b;
  animation: bounce 1.4s infinite ease-in-out both;
}

.waiting-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.waiting-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .status-bar {
    padding: 10px 12px;
  }

  .status-text {
    font-size: 13px;
  }

  .agent-avatar {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
}
</style>
