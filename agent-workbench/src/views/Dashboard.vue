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
const currentTab = ref<'chat' | 'customer' | 'history' | 'notes'>('chat')  // 右侧 Tab 切换

// 【模块5】内部备注相关状态
const internalNotes = ref<any[]>([])
const loadingNotes = ref(false)
const newNoteContent = ref('')
const addingNote = ref(false)
const editingNoteId = ref<string | null>(null)
const editingNoteContent = ref('')

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 【阶段2】使用 SSE 实时推送替代轮询
const { startMonitoring, stopMonitoring } = useAgentWorkbenchSSE()

// 【L1-1-Part1-模块1】高级筛选状态
const currentFilter = ref<SessionStatus | 'all'>('pending_manual')
const timeRange = ref<'today' | 'last3days' | 'last7days' | 'thisMonth' | 'custom'>('today')
const customTimeStart = ref<Date | null>(null)
const customTimeEnd = ref<Date | null>(null)
const customerType = ref<'all' | 'vip' | 'old' | 'new'>('all')
const sortBy = ref<'default' | 'newest' | 'oldest' | 'vip' | 'waitTime'>('default')

// 搜索关键词
const searchKeyword = ref('')

// 【L1-1-Part1-模块1】应用高级筛选
const applyAdvancedFilter = async () => {
  // 计算时间范围
  let timeStart: number | undefined = undefined
  let timeEnd: number | undefined = undefined

  const now = Date.now() / 1000  // 转为秒级时间戳
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  if (timeRange.value === 'today') {
    timeStart = today.getTime() / 1000
  } else if (timeRange.value === 'last3days') {
    timeStart = now - (3 * 24 * 3600)
  } else if (timeRange.value === 'last7days') {
    timeStart = now - (7 * 24 * 3600)
  } else if (timeRange.value === 'thisMonth') {
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
    timeStart = firstDay.getTime() / 1000
  } else if (timeRange.value === 'custom') {
    if (customTimeStart.value) {
      timeStart = customTimeStart.value.getTime() / 1000
    }
    if (customTimeEnd.value) {
      timeEnd = customTimeEnd.value.getTime() / 1000
    }
  }

  // 调用高级筛选API
  await sessionStore.fetchSessionsAdvanced({
    status: currentFilter.value,
    timeStart,
    timeEnd,
    customerType: customerType.value,
    keyword: searchKeyword.value,
    sort: sortBy.value
  })
}

// 监听筛选条件变化
watch([currentFilter, timeRange, customerType, sortBy], () => {
  applyAdvancedFilter()
})

// 监听搜索关键词变化（防抖500ms）
let searchDebounce: NodeJS.Timeout | null = null
watch(searchKeyword, () => {
  if (searchDebounce) {
    clearTimeout(searchDebounce)
  }
  searchDebounce = setTimeout(() => {
    applyAdvancedFilter()
  }, 500)
})

// 过滤后的会话列表（已由store返回，直接使用）
const filteredSessions = computed(() => {
  return sessionStore.sessions
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

// 可转接的坐席列表（从API获取真实数据）
interface AvailableAgent {
  id: string
  username: string
  name: string
  status: string
  role: string
  max_sessions: number
}

const availableAgents = ref<AvailableAgent[]>([])
const loadingAgents = ref(false)

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

// 格式化坐席状态标签
const getStatusLabel = (status: string): string => {
  const statusMap: Record<string, string> = {
    'online': '在线',
    'offline': '离线',
    'busy': '忙碌',
    'break': '小休',
    'lunch': '午休',
    'training': '培训'
  }
  return statusMap[status] || status
}

// 格式化坐席角色标签
const getRoleLabel = (role: string): string => {
  const roleMap: Record<string, string> = {
    'admin': '管理员',
    'agent': '客服'
  }
  return roleMap[role] || role
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
  // 选中会话后自动加载客户信息和内部备注
  fetchCustomerProfile(sessionName)
  fetchInternalNotes(sessionName)
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
    fetchInternalNotes(newSession)
  } else {
    customerProfile.value = null
    internalNotes.value = []
  }
})

// 【模块5】获取内部备注列表
const fetchInternalNotes = async (sessionName: string) => {
  try {
    loadingNotes.value = true
    const token = localStorage.getItem('access_token')

    const response = await axios.get(
      `${API_BASE}/api/sessions/${sessionName}/notes`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    if (response.data.success) {
      internalNotes.value = response.data.data || []
    }
  } catch (error: any) {
    console.error('获取内部备注失败:', error)
    internalNotes.value = []
  } finally {
    loadingNotes.value = false
  }
}

// 【模块5】添加内部备注
const handleAddNote = async () => {
  if (!newNoteContent.value.trim() || !sessionStore.currentSession) return

  try {
    addingNote.value = true
    const token = localStorage.getItem('access_token')

    const response = await axios.post(
      `${API_BASE}/api/sessions/${sessionStore.currentSession.session_name}/notes`,
      {
        content: newNoteContent.value.trim(),
        mentions: []  // TODO: @提醒功能
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    if (response.data.success) {
      newNoteContent.value = ''
      // 重新加载备注列表
      await fetchInternalNotes(sessionStore.currentSession.session_name)
    }
  } catch (error: any) {
    console.error('添加内部备注失败:', error)
    alert(`添加备注失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    addingNote.value = false
  }
}

// 【模块5】编辑内部备注
const handleEditNote = (noteId: string, content: string) => {
  editingNoteId.value = noteId
  editingNoteContent.value = content
}

// 【模块5】保存编辑的备注
const handleSaveEditNote = async (noteId: string) => {
  if (!editingNoteContent.value.trim() || !sessionStore.currentSession) return

  try {
    const token = localStorage.getItem('access_token')

    const response = await axios.put(
      `${API_BASE}/api/sessions/${sessionStore.currentSession.session_name}/notes/${noteId}`,
      {
        content: editingNoteContent.value.trim(),
        mentions: []
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    if (response.data.success) {
      editingNoteId.value = null
      editingNoteContent.value = ''
      // 重新加载备注列表
      await fetchInternalNotes(sessionStore.currentSession.session_name)
    }
  } catch (error: any) {
    console.error('更新内部备注失败:', error)
    alert(`更新备注失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 【模块5】取消编辑
const handleCancelEdit = () => {
  editingNoteId.value = null
  editingNoteContent.value = ''
}

// 【模块5】删除内部备注
const handleDeleteNote = async (noteId: string) => {
  if (!confirm('确定要删除这条备注吗？')) return

  if (!sessionStore.currentSession) return

  try {
    const token = localStorage.getItem('access_token')

    await axios.delete(
      `${API_BASE}/api/sessions/${sessionStore.currentSession.session_name}/notes/${noteId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    // 重新加载备注列表
    await fetchInternalNotes(sessionStore.currentSession.session_name)
  } catch (error: any) {
    console.error('删除内部备注失败:', error)
    alert(`删除备注失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 【模块5】格式化时间
const formatNoteTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 1分钟内
  if (diff < 60000) {
    return '刚刚'
  }
  // 1小时内
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes}分钟前`
  }
  // 今天
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  // 其他
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

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
const handleFilterChange = (filter: SessionStatus | 'all') => {
  currentFilter.value = filter
  // watch会自动触发applyAdvancedFilter()
}

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

// 获取可转接的坐席列表
const fetchAvailableAgents = async () => {
  try {
    loadingAgents.value = true
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${API_BASE}/api/agents/available`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('获取坐席列表失败')
    }

    const data = await response.json()
    if (data.success) {
      availableAgents.value = data.data.items
      console.log('✅ 获取到可转接坐席:', availableAgents.value.length, '个')
    }
  } catch (error) {
    console.error('❌ 获取坐席列表失败:', error)
    alert('获取坐席列表失败，请稍后重试')
  } finally {
    loadingAgents.value = false
  }
}

// 打开转接对话框
const openTransferDialog = async () => {
  // 先获取最新的坐席列表
  await fetchAvailableAgents()

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

  // 【L1-1-Part1-模块1】初始加载：应用高级筛选
  await applyAdvancedFilter()

  // 【模块2】加载队列数据
  await sessionStore.fetchQueue()

  // 【模块2】每30秒刷新队列数据
  setInterval(async () => {
    await sessionStore.fetchQueue()
  }, 30000)
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
        <!-- 快捷回复按钮 (v3.7.0+) -->
        <button @click="router.push('/quick-replies')" class="quick-reply-nav-button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            <line x1="9" y1="10" x2="15" y2="10"></line>
            <line x1="9" y1="14" x2="13" y2="14"></line>
          </svg>
          快捷回复
        </button>
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

        <!-- 【模块2】队列统计信息 -->
        <div v-if="sessionStore.queueStats.total_count > 0" class="queue-stats">
          <div class="queue-header">
            <span class="queue-icon">📋</span>
            <span class="queue-title">等待队列</span>
            <span class="queue-count">{{ sessionStore.queueStats.total_count }}人</span>
          </div>
          <div class="queue-metrics">
            <div class="queue-metric">
              <span class="metric-icon">🔴</span>
              <span class="metric-label">VIP客户</span>
              <span class="metric-value">{{ sessionStore.queueStats.vip_count }}</span>
            </div>
            <div class="queue-metric">
              <span class="metric-icon">⏱️</span>
              <span class="metric-label">平均等待</span>
              <span class="metric-value">{{ formatTime(sessionStore.queueStats.avg_wait_time) }}</span>
            </div>
            <div class="queue-metric">
              <span class="metric-icon">⚠️</span>
              <span class="metric-label">最长等待</span>
              <span class="metric-value">{{ formatTime(sessionStore.queueStats.max_wait_time) }}</span>
            </div>
          </div>
        </div>

        <!-- 筛选标签 -->
        <div class="filter-tabs">
          <button
            class="filter-tab"
            :class="{ active: currentFilter === 'pending_manual' }"
            @click="currentFilter = 'pending_manual'"
          >
            待接入
          </button>
          <button
            class="filter-tab"
            :class="{ active: currentFilter === 'manual_live' }"
            @click="currentFilter = 'manual_live'"
          >
            服务中
          </button>
          <button
            class="filter-tab"
            :class="{ active: currentFilter === 'all' }"
            @click="currentFilter = 'all'"
          >
            全部
          </button>
        </div>

        <!-- 【L1-1-Part1-模块1】高级筛选栏 -->
        <div class="advanced-filters">
          <!-- 时间范围筛选 -->
          <div class="filter-group">
            <select v-model="timeRange" class="filter-select">
              <option value="today">今天</option>
              <option value="last3days">最近3天</option>
              <option value="last7days">最近7天</option>
              <option value="thisMonth">本月</option>
            </select>
          </div>

          <!-- 客户类型筛选 -->
          <div class="filter-group">
            <select v-model="customerType" class="filter-select">
              <option value="all">全部客户</option>
              <option value="vip">VIP客户</option>
              <option value="old">老客户</option>
              <option value="new">新客户</option>
            </select>
          </div>

          <!-- 排序方式 -->
          <div class="filter-group">
            <select v-model="sortBy" class="filter-select">
              <option value="default">默认排序</option>
              <option value="newest">最新优先</option>
              <option value="oldest">最早优先</option>
              <option value="vip">VIP优先</option>
              <option value="waitTime">等待时长</option>
            </select>
          </div>
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
            :class="['tab-button', { active: currentTab === 'notes' }]"
            @click="currentTab = 'notes'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"></path>
            </svg>
            内部备注
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
          <!-- 【模块5】内部备注面板 -->
          <div v-else-if="currentTab === 'notes'" class="notes-panel">
            <div v-if="loadingNotes" class="notes-loading">
              <div class="spinner"></div>
              <p>加载中...</p>
            </div>
            <div v-else class="notes-content">
              <!-- 备注列表 -->
              <div class="notes-list">
                <div v-if="internalNotes.length === 0" class="no-notes">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#cbd5e0" stroke-width="1.5">
                    <path d="M12 20h9"></path>
                    <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"></path>
                  </svg>
                  <p>暂无内部备注</p>
                  <p class="hint">记录客户问题关键点和处理过程</p>
                </div>
                <div v-else>
                  <div
                    v-for="note in internalNotes"
                    :key="note.id"
                    class="note-item"
                  >
                    <div class="note-header">
                      <div class="note-author">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        {{ note.created_by_name }}
                      </div>
                      <div class="note-time">{{ formatNoteTime(note.created_at) }}</div>
                    </div>
                    <div class="note-content" v-if="editingNoteId !== note.id">
                      {{ note.content }}
                    </div>
                    <div class="note-edit" v-else>
                      <textarea
                        v-model="editingNoteContent"
                        class="note-textarea"
                        rows="3"
                        placeholder="编辑备注内容..."
                      ></textarea>
                      <div class="note-edit-actions">
                        <button @click="handleCancelEdit" class="btn btn-cancel">取消</button>
                        <button @click="handleSaveEditNote(note.id)" class="btn btn-confirm">保存</button>
                      </div>
                    </div>
                    <div class="note-actions" v-if="editingNoteId !== note.id">
                      <button @click="handleEditNote(note.id, note.content)" class="btn-text">编辑</button>
                      <button @click="handleDeleteNote(note.id)" class="btn-text text-danger">删除</button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 添加备注 -->
              <div class="add-note">
                <textarea
                  v-model="newNoteContent"
                  class="note-textarea"
                  rows="3"
                  placeholder="添加内部备注（仅坐席可见）..."
                  :disabled="addingNote"
                ></textarea>
                <div class="add-note-actions">
                  <button
                    @click="handleAddNote"
                    :disabled="!newNoteContent.trim() || addingNote"
                    class="btn btn-primary"
                  >
                    {{ addingNote ? '添加中...' : '添加备注' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
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
            <div v-if="loadingAgents" class="loading-hint">
              正在加载坐席列表...
            </div>
            <select v-else v-model="transferTargetId" class="form-select">
              <option value="">请选择...</option>
              <option
                v-for="agent in availableAgents.filter(a => a.id !== agentStore.agentId)"
                :key="agent.id"
                :value="agent.id"
              >
                {{ agent.name }} - {{ getStatusLabel(agent.status) }} ({{ getRoleLabel(agent.role) }})
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
  background: #2C3E50;
  padding: 12px 24px;
  border-bottom: 1px solid #34495E;
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
  height: 32px;
  width: auto;
  filter: brightness(0) invert(1);
}

.brand-text h1 {
  font-size: 16px;
  font-weight: 600;
  color: white;
  margin: 0;
  line-height: 1.2;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.brand-subtitle {
  display: none;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.agent-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.online {
  background: #27AE60;
}

.status-text {
  font-size: 12px;
  color: white;
  font-weight: 500;
}

.agent-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.agent-id {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.65);
}

/* 管理员菜单按钮 (v3.1.3+) */
.admin-dropdown {
  margin-right: 12px;
}

.admin-menu-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  font-size: 13px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.admin-menu-button:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.25);
}

/* 快捷回复按钮 (v3.7.0+) */
.quick-reply-nav-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: rgba(52, 152, 219, 0.15);
  border: 1px solid rgba(52, 152, 219, 0.3);
  border-radius: 4px;
  font-size: 13px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-right: 12px;
}

.quick-reply-nav-button:hover {
  background: rgba(52, 152, 219, 0.25);
  border-color: rgba(52, 152, 219, 0.4);
}

.logout-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: rgba(231, 76, 60, 0.15);
  border: 1px solid rgba(231, 76, 60, 0.3);
  border-radius: 4px;
  font-size: 13px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-button:hover {
  background: rgba(231, 76, 60, 0.25);
  border-color: rgba(231, 76, 60, 0.4);
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
  padding: 14px 16px;
  gap: 10px;
  border-bottom: 1px solid #E5E7EB;
  background: #FAFAFA;
}

.stat-item {
  text-align: center;
  padding: 12px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #E5E7EB;
  background: white;
}

.stat-item:hover {
  border-color: #3498DB;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}

.stat-item.pending {
  background: #FFF8E1;
  border-color: #FFA726;
}

.stat-item.live {
  background: #E8F5E9;
  border-color: #27AE60;
}

.stat-item.all {
  background: #F5F5F5;
  border-color: #9E9E9E;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #2C3E50;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 11px;
  color: #7F8C8D;
  font-weight: 500;
}

/* 详细统计 */
.detailed-stats {
  display: flex;
  padding: 10px 16px;
  gap: 16px;
  border-bottom: 1px solid #E5E7EB;
  background: white;
}

.detail-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-label {
  font-size: 11px;
  color: #95A5A6;
}

.detail-value {
  font-size: 13px;
  font-weight: 600;
  color: #2C3E50;
}

/* 【模块2】队列统计样式 */
.queue-stats {
  padding: 12px 16px;
  border-bottom: 1px solid #E5E7EB;
  background: linear-gradient(135deg, #FEF3C7 0%, #FED7AA 100%);
}

.queue-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.queue-icon {
  font-size: 16px;
}

.queue-title {
  font-size: 13px;
  font-weight: 600;
  color: #92400E;
}

.queue-count {
  margin-left: auto;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  color: #D97706;
}

.queue-metrics {
  display: flex;
  gap: 12px;
}

.queue-metric {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 6px;
}

.metric-icon {
  font-size: 16px;
  margin-bottom: 2px;
}

.metric-label {
  font-size: 10px;
  color: #92400E;
  margin-bottom: 2px;
}

.metric-value {
  font-size: 14px;
  font-weight: 700;
  color: #B45309;
}

.filter-tabs {
  display: flex;
  padding: 10px 16px;
  gap: 8px;
  border-bottom: 1px solid #E5E7EB;
  background: white;
}

.filter-tab {
  flex: 1;
  padding: 7px 0;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 13px;
  color: #7F8C8D;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tab.active {
  color: #3498DB;
  border-bottom-color: #3498DB;
}

.filter-tab:hover:not(.active) {
  color: #5DADE2;
}

/* 【L1-1-Part1-模块1】高级筛选栏样式 */
.advanced-filters {
  display: flex;
  padding: 10px 16px;
  gap: 8px;
  border-bottom: 1px solid #E5E7EB;
  background: white;
}

.filter-group {
  flex: 1;
}

.filter-select {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #E5E7EB;
  border-radius: 4px;
  font-size: 12px;
  color: #2C3E50;
  background: #FAFAFA;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-select:hover {
  border-color: #3498DB;
  background: white;
}

.filter-select:focus {
  outline: none;
  border-color: #3498DB;
  background: white;
}

/* 搜索框 */
.search-box {
  padding: 10px 16px;
  position: relative;
  background: white;
}

.search-box .search-input {
  width: 100%;
  padding: 8px 36px 8px 12px;
  border: 1px solid #E5E7EB;
  border-radius: 4px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s ease;
  background: #FAFAFA;
}

.search-box .search-input:focus {
  border-color: #3498DB;
  background: white;
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
  padding: 7px 14px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.primary {
  background: #3498DB;
  color: white;
}

.action-btn.primary:hover {
  background: #2980B9;
}

.action-btn.danger {
  background: #E74C3C;
  color: white;
}

.action-btn.danger:hover {
  background: #C0392B;
}

.action-btn.secondary {
  background: #95A5A6;
  color: white;
}

.action-btn.secondary:hover {
  background: #7F8C8D;
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
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
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
  padding: 7px 14px;
  background: #ECF0F1;
  border: 1px solid #BDC3C7;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  background: #BDC3C7;
}

.btn-confirm {
  padding: 7px 14px;
  background: #3498DB;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-confirm:hover:not(:disabled) {
  background: #2980B9;
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
  border-color: #3498DB;
}

.send-btn {
  padding: 10px 20px;
  background: #3498DB;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  background: #2980B9;
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
  border-bottom: 1px solid #E5E7EB;
  background: #FAFAFA;
}

.tab-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 16px;
  border: none;
  background: transparent;
  color: #7F8C8D;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.tab-button svg {
  transition: all 0.2s ease;
}

.tab-button:hover {
  background: white;
  color: #3498DB;
}

.tab-button.active {
  color: #3498DB;
  background: white;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #3498DB;
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

/* 【模块5】内部备注面板样式 */
.notes-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.notes-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #718096;
}

.notes-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.notes-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.no-notes {
  text-align: center;
  padding: 40px 20px;
  color: #a0aec0;
}

.no-notes svg {
  margin-bottom: 16px;
}

.no-notes p {
  margin: 8px 0;
  font-size: 14px;
}

.no-notes .hint {
  font-size: 12px;
  color: #cbd5e0;
}

.note-item {
  background: #f7fafc;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.note-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.note-author {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #2d3748;
}

.note-time {
  font-size: 11px;
  color: #a0aec0;
}

.note-content {
  font-size: 13px;
  line-height: 1.6;
  color: #4a5568;
  white-space: pre-wrap;
  word-break: break-word;
}

.note-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.note-edit {
  margin-top: 8px;
}

.note-edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: flex-end;
}

.add-note {
  border-top: 1px solid #e5e7eb;
  padding: 16px;
  background: white;
}

.note-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
  font-family: inherit;
  transition: border-color 0.2s;
}

.note-textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.note-textarea:disabled {
  background: #f7fafc;
  cursor: not-allowed;
}

.add-note-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.btn-text {
  background: none;
  border: none;
  padding: 4px 8px;
  font-size: 12px;
  color: #3b82f6;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-text:hover {
  background: #eff6ff;
}

.btn-text.text-danger {
  color: #ef4444;
}

.btn-text.text-danger:hover {
  background: #fef2f2;
}

.btn-cancel {
  padding: 6px 16px;
  font-size: 13px;
  border: 1px solid #e2e8f0;
  background: white;
  color: #4a5568;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #f7fafc;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
