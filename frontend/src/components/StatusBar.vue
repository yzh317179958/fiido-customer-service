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

    <!-- 非工作时间提示 -->
    <div v-if="sessionStatus === 'after_hours_email'" class="after-hours-notice">
      <span class="notice-icon">📧</span>
      <span class="notice-text">请留下邮箱，我们会回复您</span>
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
/* Premium Status Bar */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  position: relative;
}

.status-bar::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, var(--status-color) 50%, transparent 100%);
  opacity: 0.5;
  transition: opacity 0.3s ease;
}

/* Status indicator */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-radius: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.03);
  transition: all 0.3s ease;
}

.status-indicator:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
}

/* Status dot */
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  box-shadow: 0 0 8px currentColor;
  position: relative;
}

.status-dot::before {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid currentColor;
  opacity: 0;
  animation: ripple 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* AI 服务中 - 绿色 */
.status-ai .status-dot {
  background: #10b981;
  color: #10b981;
  --status-color: #10b981;
}

/* 等待人工 - 橙色 */
.status-pending .status-dot {
  background: #f59e0b;
  color: #f59e0b;
  --status-color: #f59e0b;
}

/* 人工服务中 - 蓝色 */
.status-manual .status-dot {
  background: #3b82f6;
  color: #3b82f6;
  --status-color: #3b82f6;
}

/* 非工作时间 - 灰色 */
.status-email .status-dot {
  background: #6b7280;
  color: #6b7280;
  --status-color: #6b7280;
}

/* 已关闭 - 红色 */
.status-closed .status-dot {
  background: #ef4444;
  color: #ef4444;
  --status-color: #ef4444;
}

/* 状态文本 */
.status-text {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  letter-spacing: -0.01em;
}

/* 脉动动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.15);
  }
}

@keyframes ripple {
  0% {
    opacity: 0.8;
    transform: scale(0.8);
  }
  100% {
    opacity: 0;
    transform: scale(1.5);
  }
}

/* 坐席信息 */
.agent-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 16px;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15);
  transition: all 0.3s ease;
}

.agent-info:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(59, 130, 246, 0.2);
}

.agent-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
  transition: all 0.3s ease;
}

.agent-avatar:hover {
  transform: scale(1.1);
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
  padding: 6px 12px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 16px;
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.15);
}

.waiting-dots {
  display: flex;
  gap: 5px;
}

.waiting-dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 1px 3px rgba(245, 158, 11, 0.3);
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
    opacity: 0.3;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 非工作时间提示 */
.after-hours-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 16px;
  font-size: 12px;
  box-shadow: 0 2px 6px rgba(217, 119, 6, 0.15);
  transition: all 0.3s ease;
}

.after-hours-notice:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(217, 119, 6, 0.2);
}

.notice-icon {
  font-size: 16px;
  animation: pulse 2s ease-in-out infinite;
}

.notice-text {
  color: #92400e;
  font-weight: 600;
  letter-spacing: -0.01em;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .status-bar {
    padding: 10px 12px;
  }

  .status-text {
    font-size: 12px;
  }

  .agent-avatar {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
}
</style>
