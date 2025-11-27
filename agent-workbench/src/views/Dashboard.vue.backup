<script setup lang="ts">
import { onMounted, onUnmounted, ref, nextTick, computed, watch } from 'vue'
import { useAgentStore } from '@/stores/agentStore'
import { useSessionStore } from '@/stores/sessionStore'
import { useRouter } from 'vue-router'
import SessionList from '@/components/SessionList.vue'
import QuickReplies from '@/components/QuickReplies.vue'
import CustomerProfile from '@/components/customer/CustomerProfile.vue'
import type { SessionStatus, CustomerProfile as CustomerProfileType } from '@/types'
import { useAgentWorkbenchSSE } from '@/composables/useAgentWorkbenchSSE'
import axios from 'axios'

const agentStore = useAgentStore()
const sessionStore = useSessionStore()
const router = useRouter()

// 客户信息相关状态
const customerProfile = ref<CustomerProfileType | null>(null)
const loadingCustomer = ref(false)
const currentTab = ref<'chat' | 'customer' | 'history'>('chat')  // 右侧 Tab 切换

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 【阶段2】使用 SSE 实时推送替代轮询
const { startMonitoring, stopMonitoring } = useAgentWorkbenchSSE()

// 当前筛选状态
const currentFilter = ref<SessionStatus | 'all'>('pending_manual')

// 搜索关键词
const searchKeyword = ref('')

// 过滤后的会话列表
const filteredSessions = computed(() => {
  if (!searchKeyword.value.trim()) {
    return sessionStore.sessions
  }

  const keyword = searchKeyword.value.toLowerCase().trim()
  return sessionStore.sessions.filter(session => {
    // 搜索会话ID
    if (session.session_name.toLowerCase().includes(keyword)) {
      return true
    }
    // 搜索用户昵称
    if (session.user_profile?.nickname?.toLowerCase().includes(keyword)) {
      return true
    }
    // 搜索最后消息内容
    if (session.last_message_preview?.content.toLowerCase().includes(keyword)) {
      return true
    }
    // 搜索坐席名称
    if (session.assigned_agent?.name.toLowerCase().includes(keyword)) {
      return true
    }
    return false
  })
})

// 聊天输入
const messageInput = ref('')
const chatHistoryRef = ref<HTMLElement | null>(null)
const isSending = ref(false)
const showQuickReplies = ref(false)

// 转接对话框
const showTransferDialog = ref(false)
const transferTargetId = ref('')
const transferTargetName = ref('')
const transferReason = ref('')

// 模拟可转接的坐席列表（实际项目应从API获取）
const availableAgents = ref([
  { id: 'agent_002', name: '技术支持-小李' },
  { id: 'agent_003', name: '售后服务-小王' },
  { id: 'agent_004', name: '高级客服-小张' }
])

// 处理快捷短语选择
const handleQuickReplySelect = (content: string) => {
  messageInput.value = content
  showQuickReplies.value = false
}

// 格式化时间（秒转为易读格式）
const formatTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}分`
  } else {
    return `${Math.round(seconds / 3600)}时`
  }
}

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    agentStore.logout()
    router.push('/login')
  }
}

// 处理会话选择
const handleSelectSession = async (sessionName: string) => {
  await sessionStore.fetchSessionDetail(sessionName)
  // 选中会话后自动加载客户信息
  fetchCustomerProfile(sessionName)
}

// 获取客户画像
const fetchCustomerProfile = async (customerId: string) => {
  try {
    loadingCustomer.value = true
    const token = localStorage.getItem('access_token')

    const response = await axios.get(
      `${API_BASE}/api/customers/${customerId}/profile`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    if (response.data.success) {
      customerProfile.value = response.data.data
    }
  } catch (error: any) {
    console.error('获取客户信息失败:', error)
    customerProfile.value = null
  } finally {
    loadingCustomer.value = false
  }
}

// 监听当前会话变化
watch(() => sessionStore.currentSessionName, (newSession) => {
  if (newSession) {
    fetchCustomerProfile(newSession)
  } else {
    customerProfile.value = null
  }
})

// 处理接入会话
const handleTakeover = async (sessionName: string) => {
  try {
    await sessionStore.takeoverSession(
      sessionName,
      agentStore.agentId,
      agentStore.agentName
    )
    alert(`✅ 已成功接入会话`)
    // 选中该会话
    await sessionStore.fetchSessionDetail(sessionName)
  } catch (err: any) {
    alert(`❌ 接入失败: ${err.message}`)
  }
}

// 切换筛选
const handleFilterChange = async (filter: SessionStatus | 'all') => {
  currentFilter.value = filter
  if (filter === 'all') {
    await sessionStore.fetchSessions()
  } else {
    await sessionStore.setFilter(filter)
  }
}

// 刷新数据 - 已由SSE替代，保留备用
// const refreshData = async () => {
//   const status = currentFilter.value === 'all' ? undefined : currentFilter.value
//   await Promise.all([
//     sessionStore.fetchSessions(status),
//     sessionStore.fetchStats()
//   ])
//
//   // 如果有选中的会话，也刷新会话详情（获取新消息）
//   if (sessionStore.currentSessionName) {
//     await sessionStore.fetchSessionDetail(sessionStore.currentSessionName)
//     // 自动滚动到底部
//     await scrollToBottom()
//   }
// }

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
  }
}

// 发送消息
const handleSendMessage = async () => {
  if (!messageInput.value.trim() || isSending.value) return
  if (!sessionStore.currentSession) return

  const content = messageInput.value.trim()
  messageInput.value = ''
  isSending.value = true

  try {
    await sessionStore.sendMessage(
      sessionStore.currentSession.session_name,
      content,
      agentStore.agentId,
      agentStore.agentName
    )
    await scrollToBottom()
  } catch (err: any) {
    alert(`❌ 发送失败: ${err.message}`)
  } finally {
    isSending.value = false
  }
}

// 释放会话
const handleRelease = async () => {
  if (!sessionStore.currentSession) return

  if (!confirm('确定要结束本次服务吗？会话将恢复为AI服务。')) {
    return
  }

  try {
    await sessionStore.releaseSession(
      sessionStore.currentSession.session_name,
      agentStore.agentId,
      'resolved'
    )
    alert('✅ 会话已释放，恢复AI服务')
    sessionStore.clearCurrentSession()
  } catch (err: any) {
    alert(`❌ 释放失败: ${err.message}`)
  }
}

// 处理回车发送
const handleKeyPress = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSendMessage()
  }
}

// 打开转接对话框
const openTransferDialog = () => {
  // 过滤掉当前坐席
  const filtered = availableAgents.value.filter(a => a.id !== agentStore.agentId)
  if (filtered.length === 0) {
    alert('暂无可转接的坐席')
    return
  }
  transferTargetId.value = ''
  transferTargetName.value = ''
  transferReason.value = ''
  showTransferDialog.value = true
}

// 处理转接
const handleTransfer = async () => {
  if (!transferTargetId.value || !sessionStore.currentSession) {
    alert('请选择要转接的坐席')
    return
  }

  const targetAgent = availableAgents.value.find(a => a.id === transferTargetId.value)
  if (!targetAgent) {
    alert('坐席信息无效')
    return
  }

  try {
    await sessionStore.transferSession(
      sessionStore.currentSession.session_name,
      agentStore.agentId,
      targetAgent.id,
      targetAgent.name,
      transferReason.value || '坐席转接'
    )
    alert(`✅ 会话已转接至【${targetAgent.name}】`)
    showTransferDialog.value = false
    sessionStore.clearCurrentSession()
  } catch (err: any) {
    alert(`❌ 转接失败: ${err.message}`)
  }
}

onMounted(async () => {
  // 【阶段2】使用 SSE 实时监听替代轮询
  // 优势：
  // 1. 实时性：< 100ms 推送延迟（之前轮询平均 2.5s）
  // 2. 资源节省：83% 减少网络请求（30s 轮询 vs 5s 轮询）
  // 3. 精准推送：只推送变化的会话，不需要全量刷新
  await startMonitoring()
})

onUnmounted(() => {
  // 【阶段2】停止 SSE 监听
  stopMonitoring()
})
</script>

<template>
  <div class="dashboard-container">
    <!-- 头部 -->
    <div class="dashboard-header">
      <div class="header-brand">
        <img src="/fiido2.png" alt="Fiido" class="brand-logo-img" />
        <div class="brand-text">
          <h1>客服工作台</h1>
          <span class="brand-subtitle">Customer Service</span>
        </div>
      </div>
      <div class="agent-info">
        <div class="agent-status">
          <span class="status-dot online"></span>
          <span class="status-text">在线服务中</span>
        </div>
        <div class="agent-details">
          <span class="agent-name">{{ agentStore.agentName }}</span>
          <span class="agent-id">{{ agentStore.agentId }}</span>
        </div>
        <!-- 管理员菜单 (v3.1.3+) -->
        <el-dropdown v-if="agentStore.agentRole === 'admin'" trigger="click" class="admin-dropdown">
          <button class="admin-menu-button">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/>
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
            </svg>
            管理
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/admin/agents')">
                <span>👥 坐席管理</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <button @click="handleLogout" class="logout-button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
          退出登录
        </button>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="dashboard-body">
      <!-- 左侧：会话列表 -->
      <div class="sessions-panel">
        <!-- 统计信息 -->
        <div class="stats-bar">
          <div class="stat-item pending" @click="handleFilterChange('pending_manual')">
            <span class="stat-value">{{ sessionStore.pendingCount }}</span>
            <span class="stat-label">待接入</span>
          </div>
          <div class="stat-item live" @click="handleFilterChange('manual_live')">
            <span class="stat-value">{{ sessionStore.manualLiveCount }}</span>
            <span class="stat-label">服务中</span>
          </div>
          <div class="stat-item all" @click="handleFilterChange('all')">
            <span class="stat-value">{{ sessionStore.stats.total_sessions }}</span>
            <span class="stat-label">全部</span>
          </div>
        </div>

        <!-- 详细统计 -->
        <div class="detailed-stats">
          <div class="detail-stat">
            <span class="detail-label">平均等待</span>
            <span class="detail-value">{{ formatTime(sessionStore.stats.avg_waiting_time) }}</span>
          </div>
          <div class="detail-stat">
            <span class="detail-label">在线坐席</span>
            <span class="detail-value">{{ sessionStore.stats.active_agents }}</span>
          </div>
        </div>

        <!-- 筛选标签 -->
        <div class="filter-tabs">
          <button
            class="filter-tab"
            :class="{ active: currentFilter === 'pending_manual' }"
            @click="handleFilterChange('pending_manual')"
          >
            待接入
          </button>
          <button
            class="filter-tab"
            :class="{ active: currentFilter === 'manual_live' }"
            @click="handleFilterChange('manual_live')"
          >
            服务中
          </button>
          <button
            class="filter-tab"
            :class="{ active: currentFilter === 'all' }"
            @click="handleFilterChange('all')"
          >
            全部
          </button>
        </div>

        <!-- 搜索框 -->
        <div class="search-box">
          <input
            v-model="searchKeyword"
            type="text"
            class="search-input"
            placeholder="搜索用户、会话ID、消息内容..."
          >
          <span v-if="searchKeyword" class="search-clear" @click="searchKeyword = ''">
            &times;
          </span>
        </div>

        <!-- 会话列表 -->
        <SessionList
          :sessions="filteredSessions"
          :is-loading="sessionStore.isLoading"
          :selected-session="sessionStore.currentSessionName"
          @select="handleSelectSession"
          @takeover="handleTakeover"
        />
      </div>

      <!-- 右侧：会话详情/聊天区域 -->
      <div class="chat-panel">
        <div v-if="!sessionStore.currentSession" class="no-session">
          <div class="no-session-icon">💬</div>
          <p>选择一个会话开始服务</p>
          <p class="hint">点击左侧会话列表中的会话查看详情</p>
        </div>

        <div v-else class="session-detail">
          <!-- 会话头部信息 -->
          <div class="detail-header">
            <div class="detail-user">
              <span class="user-avatar">
                {{ sessionStore.currentSession.user_profile?.nickname?.charAt(0) || '访' }}
              </span>
              <div class="user-info">
                <span class="user-name">
                  {{ sessionStore.currentSession.user_profile?.nickname || sessionStore.currentSession.session_name }}
                </span>
                <span class="session-status" :class="`status-${sessionStore.currentSession.status}`">
                  {{ sessionStore.currentSession.status }}
                </span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="detail-actions">
              <button
                v-if="sessionStore.currentSession.status === 'pending_manual'"
                class="action-btn primary"
                @click="handleTakeover(sessionStore.currentSession.session_name)"
              >
                接入会话
              </button>
              <button
                v-if="sessionStore.currentSession.status === 'manual_live'"
                class="action-btn secondary"
                @click="openTransferDialog"
              >
                转接
              </button>
              <button
                v-if="sessionStore.currentSession.status === 'manual_live'"
                class="action-btn danger"
                @click="handleRelease"
              >
                结束服务
              </button>
            </div>
          </div>

          <!-- 聊天历史 -->
          <div ref="chatHistoryRef" class="chat-history">
            <div
              v-for="message in sessionStore.currentSession.history"
              :key="message.id"
              class="message"
              :class="message.role"
            >
              <div v-if="message.role === 'system'" class="system-message">
                {{ message.content }}
              </div>
              <template v-else>
                <div class="message-avatar">
                  {{ message.role === 'user' ? '用' : message.role === 'agent' ? '客' : 'AI' }}
                </div>
                <div class="message-body">
                  <div class="message-header">
                    <span class="message-sender">
                      {{ message.role === 'user' ? '用户' : message.role === 'agent' ? message.agent_name || '客服' : 'AI' }}
                    </span>
                    <span class="message-time">
                      {{ new Date(message.timestamp * 1000).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
                    </span>
                  </div>
                  <div class="message-content">{{ message.content }}</div>
                </div>
              </template>
            </div>
          </div>

          <!-- 聊天输入区域 -->
          <div v-if="sessionStore.currentSession.status === 'manual_live'" class="chat-input-area">
            <!-- 快捷短语面板 -->
            <div v-if="showQuickReplies" class="quick-replies-panel">
              <QuickReplies @select="handleQuickReplySelect" />
            </div>

            <div class="input-wrapper">
              <button
                class="quick-reply-btn"
                @click="showQuickReplies = !showQuickReplies"
                :class="{ active: showQuickReplies }"
                title="快捷短语"
              >
                <span class="btn-icon">📝</span>
              </button>
              <textarea
                v-model="messageInput"
                class="message-input"
                placeholder="输入消息..."
                rows="1"
                @keypress="handleKeyPress"
              ></textarea>
              <button
                class="send-btn"
                :disabled="!messageInput.trim() || isSending"
                @click="handleSendMessage"
              >
                {{ isSending ? '发送中...' : '发送' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：客户信息侧边栏 (v3.2.0+) -->
      <div v-if="sessionStore.currentSession" class="customer-sidebar">
        <div class="sidebar-tabs">
          <button
            :class="['tab-button', { active: currentTab === 'customer' }]"
            @click="currentTab = 'customer'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            客户信息
          </button>
          <button
            :class="['tab-button', { active: currentTab === 'history' }]"
            @click="currentTab = 'history'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            对话历史
          </button>
        </div>

        <div class="sidebar-content">
          <CustomerProfile
            v-if="currentTab === 'customer'"
            :customer="customerProfile"
            :loading="loadingCustomer"
          />
          <div v-else-if="currentTab === 'history'" class="history-panel">
            <p style="padding: 20px; text-align: center; color: #718096;">
              对话历史功能开发中...
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 转接对话框 -->
    <div v-if="showTransferDialog" class="dialog-overlay">
      <div class="dialog">
        <div class="dialog-header">
          <h3>转接会话</h3>
          <button class="dialog-close" @click="showTransferDialog = false">&times;</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>选择坐席</label>
            <select v-model="transferTargetId" class="form-select">
              <option value="">请选择...</option>
              <option
                v-for="agent in availableAgents.filter(a => a.id !== agentStore.agentId)"
                :key="agent.id"
                :value="agent.id"
              >
                {{ agent.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>转接原因（选填）</label>
            <input
              v-model="transferReason"
              type="text"
              class="form-input"
              placeholder="如：专业问题需转接技术支持"
            >
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="showTransferDialog = false">取消</button>
          <button class="btn-confirm" @click="handleTransfer" :disabled="!transferTargetId">确认转接</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.dashboard-header {
  background: linear-gradient(135deg, #4ECDC4 0%, #52C7B8 100%);
  padding: 18px 32px;
  box-shadow: 0 2px 16px rgba(78, 205, 196, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-logo-img {
  height: 40px;
  width: auto;
  filter: brightness(0) invert(1) drop-shadow(0 2px 4px rgba(0,0,0,0.1));
  animation: fadeIn 0.6s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.brand-text h1 {
  font-size: 20px;
  font-weight: 700;
  color: white;
  margin: 0;
  line-height: 1.2;
  letter-spacing: -0.3px;
}

.brand-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  font-weight: 500;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.agent-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.25);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.status-dot.online {
  background: #10b981;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

.status-text {
  font-size: 13px;
  color: white;
  font-weight: 600;
}

.agent-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-name {
  font-size: 15px;
  font-weight: 700;
  color: white;
}

.agent-id {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
}

/* 管理员菜单按钮 (v3.1.3+) */
.admin-dropdown {
  margin-right: 12px;
}

.admin-menu-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 10px;
  font-size: 14px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.admin-menu-button:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.admin-menu-button:active {
  transform: translateY(0);
}

.logout-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 10px;
  font-size: 14px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dashboard-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧会话列表面板 */
.sessions-panel {
  width: 380px;
  background: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.stats-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  padding: 20px 16px 16px;
  gap: 12px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(to bottom, #f9fafb, white);
}

.stat-item {
  text-align: center;
  padding: 16px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: 2px solid transparent;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.4));
  opacity: 0;
  transition: opacity 0.3s;
}

.stat-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.stat-item:hover::before {
  opacity: 1;
}

.stat-item.pending {
  background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
  border-color: #ffa726;
}

.stat-item.pending:hover {
  box-shadow: 0 8px 20px rgba(255, 167, 38, 0.3);
}

.stat-item.live {
  background: linear-gradient(135deg, #e0f7f7 0%, #b2ebeb 100%);
  border-color: #4ECDC4;
}

.stat-item.live:hover {
  box-shadow: 0 8px 20px rgba(78, 205, 196, 0.4);
}

.stat-item.all {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border-color: #9ca3af;
}

.stat-item.all:hover {
  box-shadow: 0 8px 20px rgba(156, 163, 175, 0.3);
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: #1f2937;
  margin-bottom: 4px;
  position: relative;
  z-index: 1;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.stat-label {
  font-size: 11px;
  color: #6b7280;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  position: relative;
  z-index: 1;
}

/* 详细统计 */
.detailed-stats {
  display: flex;
  padding: 12px 16px;
  gap: 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #fafafa;
}

.detail-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-label {
  font-size: 11px;
  color: #9ca3af;
}

.detail-value {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.filter-tabs {
  display: flex;
  padding: 12px 16px;
  gap: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.filter-tab {
  flex: 1;
  padding: 8px;
  background: #f3f4f6;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tab.active {
  background: #4ECDC4;
  color: white;
}

.filter-tab:hover:not(.active) {
  background: #e5e7eb;
}

/* 搜索框 */
.search-box {
  padding: 0 16px 12px;
  position: relative;
}

.search-box .search-input {
  width: 100%;
  padding: 10px 36px 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.search-box .search-input:focus {
  border-color: #4ECDC4;
}

.search-clear {
  position: absolute;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.search-clear:hover {
  color: #6b7280;
}

/* 右侧聊天面板 */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
}

.no-session {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6b7280;
}

.no-session-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.no-session p {
  font-size: 16px;
  margin-bottom: 8px;
}

.no-session .hint {
  font-size: 13px;
  color: #9ca3af;
}

.session-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-user .user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4ECDC4 0%, #52C7B8 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-info .user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.session-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-pending_manual {
  background: #fef3c7;
  color: #d97706;
}

.status-manual_live {
  background: #dbeafe;
  color: #2563eb;
}

.status-bot_active {
  background: #d1fae5;
  color: #059669;
}

.action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.primary {
  background: linear-gradient(135deg, #4ECDC4 0%, #52C7B8 100%);
  color: white;
}

.action-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
}

.action-btn.danger {
  background: #ef4444;
  color: white;
}

.action-btn.danger:hover {
  background: #dc2626;
}

.action-btn.secondary {
  background: #6366f1;
  color: white;
}

.action-btn.secondary:hover {
  background: #4f46e5;
}

/* 转接对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 12px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.dialog-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.dialog-close:hover {
  color: #6b7280;
}

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.form-select,
.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-select:focus,
.form-input:focus {
  border-color: #667eea;
}

.dialog-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.btn-confirm {
  padding: 8px 16px;
  background: linear-gradient(135deg, #4ECDC4 0%, #52C7B8 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-confirm:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message.system {
  justify-content: center;
}

.system-message {
  padding: 8px 16px;
  background: #f3f4f6;
  border-radius: 16px;
  font-size: 12px;
  color: #6b7280;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #e5e7eb;
  color: #374151;
}

.message.assistant .message-avatar {
  background: #d1fae5;
  color: #059669;
}

.message.agent .message-avatar {
  background: #dbeafe;
  color: #2563eb;
}

.message-body {
  max-width: 70%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.message-sender {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}

.message-time {
  font-size: 11px;
  color: #9ca3af;
}

.message-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.message.user .message-content {
  background: #1f2937;
  color: white;
  border-radius: 12px 12px 4px 12px;
}

.message.assistant .message-content {
  background: #f3f4f6;
  color: #1f2937;
  border-radius: 12px 12px 12px 4px;
}

.message.agent .message-content {
  background: #eff6ff;
  color: #1e40af;
  border-left: 3px solid #3b82f6;
  border-radius: 12px 12px 12px 4px;
}

/* 聊天输入区域 */
.chat-input-area {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  position: relative;
}

/* 快捷短语面板 */
.quick-replies-panel {
  position: absolute;
  bottom: 100%;
  left: 24px;
  right: 24px;
  margin-bottom: 8px;
  z-index: 10;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  overflow: hidden;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

/* 快捷短语按钮 */
.quick-reply-btn {
  width: 44px;
  height: 44px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.quick-reply-btn:hover {
  border-color: #4ECDC4;
  background: #e0f7f7;
}

.quick-reply-btn.active {
  border-color: #4ECDC4;
  background: #4ECDC4;
}

.quick-reply-btn.active .btn-icon {
  filter: grayscale(1) brightness(10);
}

.btn-icon {
  font-size: 18px;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  font-family: inherit;
}

.message-input:focus {
  outline: none;
  border-color: #4ECDC4;
}

.send-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #4ECDC4 0%, #52C7B8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 右侧客户信息侧边栏 (v3.2.0+) */
.customer-sidebar {
  width: 320px;
  background: white;
  border-left: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.tab-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 16px;
  border: none;
  background: transparent;
  color: #718096;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.tab-button svg {
  transition: all 0.2s;
}

.tab-button:hover {
  background: rgba(78, 205, 196, 0.05);
  color: #4ECDC4;
}

.tab-button.active {
  color: #4ECDC4;
  background: white;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #4ECDC4;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  background: #fafafa;
}

.history-panel {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
