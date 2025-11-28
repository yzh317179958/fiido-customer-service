<script setup lang="ts">
import { computed } from 'vue'
import type { SessionSummary } from '@/types'

const props = withDefaults(defineProps<{
  sessions: SessionSummary[]
  isLoading: boolean
  selectedSession?: string
  density?: 'compact' | 'standard' | 'comfortable'
  showPreview?: boolean
}>(), {
  density: 'standard',
  showPreview: true
})
const emit = defineEmits<{
  (e: 'select', sessionName: string): void
  (e: 'takeover', sessionName: string): void
}>()

const densityClass = computed(() => `density-${props.density || 'standard'}`)
const previewEnabled = computed(() => props.showPreview !== false)

// 格式化等待时间
const formatWaitingTime = (seconds: number) => {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}分钟`
  } else {
    return `${Math.floor(seconds / 3600)}小时`
  }
}

// 格式化时间戳
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}

// 获取状态配置
const getStatusConfig = (status: string) => {
  const configs: Record<string, { label: string; class: string; icon: string }> = {
    pending_manual: {
      label: '等待接入',
      class: 'status-pending',
      icon: '⏳'
    },
    manual_live: {
      label: '服务中',
      class: 'status-live',
      icon: '💬'
    },
    bot_active: {
      label: 'AI服务',
      class: 'status-bot',
      icon: '🤖'
    },
    closed: {
      label: '已关闭',
      class: 'status-closed',
      icon: '🔒'
    }
  }
  return configs[status] || { label: status, class: '', icon: '❓' }
}

// 截断消息内容
const truncateMessage = (content: string, maxLength: number = 50) => {
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}

// 【模块2】获取优先级配置
const getPriorityConfig = (level: string) => {
  const configs: Record<string, { icon: string; class: string; label: string }> = {
    urgent: {
      icon: '🔴',
      class: 'priority-urgent',
      label: '紧急'
    },
    high: {
      icon: '🟠',
      class: 'priority-high',
      label: '重要'
    }
  }
  return configs[level]
}
</script>

<template>
  <div class="session-list" :class="densityClass">
    <!-- 加载状态 -->
    <div v-if="props.isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="props.sessions.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无会话</p>
    </div>

    <!-- 会话列表 -->
    <div v-else class="sessions">
      <div
        v-for="session in props.sessions"
        :key="session.session_name"
        class="session-item"
        :class="{
          selected: props.selectedSession === session.session_name,
          pending: session.status === 'pending_manual'
        }"
        @click="emit('select', session.session_name)"
      >
        <!-- 会话头部 -->
        <div class="session-header">
          <div class="session-user">
            <span class="user-avatar">
              {{ session.user_profile?.nickname?.charAt(0) || '访' }}
            </span>
            <span class="user-name">
              {{ session.user_profile?.nickname || session.session_name.slice(-8) }}
            </span>
            <span v-if="session.user_profile?.vip" class="vip-badge">VIP</span>
            <!-- 【模块2】优先级标识 -->
            <span
              v-if="session.priority && getPriorityConfig(session.priority.level)"
              :class="['priority-badge', getPriorityConfig(session.priority.level)?.class]"
              :title="getPriorityConfig(session.priority.level)?.label"
            >
              {{ getPriorityConfig(session.priority.level)?.icon }}
            </span>
          </div>
          <div class="session-status" :class="getStatusConfig(session.status).class">
            <span class="status-icon">{{ getStatusConfig(session.status).icon }}</span>
            <span class="status-label">{{ getStatusConfig(session.status).label }}</span>
          </div>
        </div>

        <!-- 最后一条消息 -->
          <div v-if="previewEnabled && session.last_message_preview" class="session-preview">
          <span class="preview-role">
            {{ session.last_message_preview.role === 'user' ? '用户' : 'AI' }}:
          </span>
          <span class="preview-content">
            {{ truncateMessage(session.last_message_preview.content) }}
          </span>
        </div>

        <!-- 会话底部信息 -->
        <div class="session-footer">
          <div class="session-time">
            {{ formatTime(session.updated_at) }}
          </div>

          <!-- 等待时间 (pending_manual状态) -->
          <div v-if="session.status === 'pending_manual' && session.escalation" class="waiting-time">
            <span class="waiting-icon">⏱️</span>
            <span>等待 {{ formatWaitingTime(session.escalation.waiting_seconds) }}</span>
          </div>

          <!-- 已分配坐席 (manual_live状态) -->
          <div v-if="session.status === 'manual_live' && session.assigned_agent" class="assigned-agent">
            <span class="agent-icon">👤</span>
            <span>{{ session.assigned_agent.name }}</span>
          </div>
        </div>

        <!-- 快速操作按钮 -->
        <div
          v-if="session.status === 'pending_manual'"
          class="session-actions"
          @click.stop
        >
          <button
            class="takeover-btn"
            @click="emit('takeover', session.session_name)"
          >
            立即接入
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.session-list {
  height: 100%;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.sessions {
  padding: 8px;
}

.session-list.density-compact .sessions {
  padding: 4px;
}

.session-list.density-comfortable .sessions {
  padding: 12px;
}

.session-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.session-list.density-compact .session-item {
  padding: 8px 10px;
  margin-bottom: 6px;
}

.session-list.density-comfortable .session-item {
  padding: 16px 18px;
  margin-bottom: 12px;
}

.session-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.session-item.selected {
  border-color: #667eea;
  background: #f5f3ff;
}

.session-item.pending {
  border-left: 3px solid #f59e0b;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.session-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.vip-badge {
  background: #fef3c7;
  color: #d97706;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

/* 【模块2】优先级标识样式 */
.priority-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1;
  cursor: help;
}

.priority-urgent {
  background: #fee2e2;
  animation: pulse-urgent 2s ease-in-out infinite;
}

.priority-high {
  background: #fed7aa;
}

@keyframes pulse-urgent {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.session-status {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.status-icon {
  font-size: 12px;
}

.status-pending {
  background: #fef3c7;
  color: #d97706;
}

.status-live {
  background: #dbeafe;
  color: #2563eb;
}

.status-bot {
  background: #d1fae5;
  color: #059669;
}

.status-closed {
  background: #f3f4f6;
  color: #6b7280;
}

.session-preview {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
  line-height: 1.4;
}

.session-list.density-compact .session-preview {
  font-size: 12px;
}

.session-list.density-comfortable .session-preview {
  font-size: 14px;
}

.preview-role {
  color: #9ca3af;
}

.session-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #9ca3af;
}

.session-time {
  flex-shrink: 0;
}

.waiting-time,
.assigned-agent {
  display: flex;
  align-items: center;
  gap: 4px;
}

.waiting-time {
  color: #d97706;
}

.assigned-agent {
  color: #2563eb;
}

.waiting-icon,
.agent-icon {
  font-size: 12px;
}

.session-actions {
  position: absolute;
  right: 12px;
  bottom: 12px;
}

.takeover-btn {
  padding: 6px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.takeover-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
