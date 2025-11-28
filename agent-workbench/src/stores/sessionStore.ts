import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SessionSummary, SessionDetail, SessionStatus, QueueResponse, QueueSessionInfo } from '@/types'
import { getAccessToken } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const useSessionStore = defineStore('session', () => {
  // 会话列表
  const sessions = ref<SessionSummary[]>([])
  const total = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 当前选中的会话
  const currentSession = ref<SessionDetail | null>(null)
  const currentSessionName = ref<string>('')

  // 选中的会话（用于SSE监听）
  const selectedSession = computed(() => currentSession.value)

  // 统计信息
  const stats = ref({
    total_sessions: 0,
    by_status: {
      bot_active: 0,
      pending_manual: 0,
      manual_live: 0,
      closed: 0
    },
    active_sessions: 0,
    avg_waiting_time: 0,
    max_waiting_time: 0,
    avg_service_time: 0,
    active_agents: 0,
    by_escalation_reason: {} as Record<string, number>,
    today: {
      total_escalations: 0,
      pending: 0,
      serving: 0
    }
  })

  // 筛选条件
  const filterStatus = ref<SessionStatus | ''>('')

  // 【模块2】队列数据
  const queueData = ref<QueueSessionInfo[]>([])
  const queueStats = ref({
    total_count: 0,
    vip_count: 0,
    avg_wait_time: 0,
    max_wait_time: 0
  })

  // 计算属性
  const pendingCount = computed(() => stats.value.by_status.pending_manual || 0)
  const manualLiveCount = computed(() => stats.value.by_status.manual_live || 0)

  // 获取会话列表 (增强版 - 支持高级筛选)
  async function fetchSessions(status?: SessionStatus, limit: number = 50, offset: number = 0) {
    isLoading.value = true
    error.value = null

    try {
      let url = `${API_BASE}/api/sessions?limit=${limit}&offset=${offset}`
      if (status) {
        url += `&status=${status}`
      }

      const token = getAccessToken()
      const headers: HeadersInit = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(url, { headers })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        sessions.value = data.data.sessions
        total.value = data.data.total
        console.log(`✅ 获取会话列表成功: ${sessions.value.length} 个会话`)
      } else {
        throw new Error(data.error || '获取失败')
      }
    } catch (err: any) {
      error.value = err.message
      console.error('❌ 获取会话列表失败:', err)
    } finally {
      isLoading.value = false
    }
  }

  // 【L1-1-Part1-模块1】高级筛选与搜索
  async function fetchSessionsAdvanced(filters: {
    status?: SessionStatus | 'all',
    timeStart?: number,
    timeEnd?: number,
    agent?: 'all' | 'mine' | 'unassigned' | string,
    customerType?: 'all' | 'vip' | 'old' | 'new',
    keyword?: string,
    sort?: 'default' | 'newest' | 'oldest' | 'vip' | 'waitTime',
    limit?: number,
    offset?: number
  } = {}) {
    isLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()

      // 状态筛选
      if (filters.status && filters.status !== 'all') {
        params.append('status', filters.status)
      }

      // 时间范围筛选
      if (filters.timeStart) {
        params.append('time_start', filters.timeStart.toString())
      }
      if (filters.timeEnd) {
        params.append('time_end', filters.timeEnd.toString())
      }

      // 坐席筛选
      if (filters.agent && filters.agent !== 'all') {
        params.append('agent', filters.agent)
      }

      // 客户类型筛选
      if (filters.customerType && filters.customerType !== 'all') {
        params.append('customer_type', filters.customerType)
      }

      // 关键词搜索
      if (filters.keyword && filters.keyword.trim()) {
        params.append('keyword', filters.keyword.trim())
      }

      // 排序方式
      if (filters.sort) {
        params.append('sort', filters.sort)
      }

      // 分页参数
      params.append('limit', (filters.limit || 50).toString())
      params.append('offset', (filters.offset || 0).toString())

      const url = `${API_BASE}/api/sessions?${params.toString()}`

      const token = getAccessToken()
      const headers: HeadersInit = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(url, { headers })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        sessions.value = data.data.sessions
        total.value = data.data.total
        console.log(`✅ 高级筛选成功: 找到 ${total.value} 个会话，显示 ${sessions.value.length} 个`)
        return data.data
      } else {
        throw new Error(data.error || '筛选失败')
      }
    } catch (err: any) {
      error.value = err.message
      console.error('❌ 高级筛选失败:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 获取统计信息
  async function fetchStats() {
    try {
      const token = getAccessToken()
      const headers: HeadersInit = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${API_BASE}/api/sessions/stats`, { headers })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        stats.value = data.data
        console.log('✅ 获取统计信息成功:', stats.value)
      }
    } catch (err) {
      console.error('❌ 获取统计信息失败:', err)
    }
  }

  // 获取会话详情
  async function fetchSessionDetail(sessionName: string) {
    isLoading.value = true
    error.value = null
    currentSessionName.value = sessionName

    try {
      const token = getAccessToken()
      const headers: HeadersInit = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${API_BASE}/api/sessions/${sessionName}`, { headers })

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('会话不存在')
        }
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        currentSession.value = data.data.session
        console.log('✅ 获取会话详情成功:', sessionName)
      } else {
        throw new Error(data.error || '获取失败')
      }
    } catch (err: any) {
      error.value = err.message
      currentSession.value = null
      console.error('❌ 获取会话详情失败:', err)
    } finally {
      isLoading.value = false
    }
  }

  // 接入会话
  async function takeoverSession(sessionName: string, agentId: string, agentName: string) {
    try {
      const response = await fetch(`/api/sessions/${sessionName}/takeover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          agent_name: agentName
        })
      })

      const data = await response.json()

      if (!response.ok) {
        // 处理特定错误
        if (response.status === 409) {
          if (data.detail?.includes('ALREADY_TAKEN')) {
            throw new Error('该会话已被其他坐席接入')
          } else if (data.detail?.includes('INVALID_STATUS')) {
            throw new Error('当前会话状态不允许接入')
          }
        }
        throw new Error(data.detail || '接入失败')
      }

      if (data.success) {
        console.log('✅ 接入会话成功:', sessionName)
        // 刷新列表和详情
        await fetchSessions(filterStatus.value || undefined)
        await fetchStats()
        return true
      }

      return false
    } catch (err: any) {
      error.value = err.message
      console.error('❌ 接入会话失败:', err)
      throw err
    }
  }

  // 释放会话
  async function releaseSession(sessionName: string, agentId: string, reason: string = 'resolved') {
    try {
      const response = await fetch(`/api/sessions/${sessionName}/release`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          reason: reason
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || '释放失败')
      }

      if (data.success) {
        console.log('✅ 释放会话成功:', sessionName)
        // 刷新列表
        await fetchSessions(filterStatus.value || undefined)
        await fetchStats()
        return true
      }

      return false
    } catch (err: any) {
      error.value = err.message
      console.error('❌ 释放会话失败:', err)
      throw err
    }
  }

  // 转接会话
  async function transferSession(
    sessionName: string,
    fromAgentId: string,
    toAgentId: string,
    toAgentName: string,
    reason: string = '坐席转接',
    note?: string
  ) {
    try {
      const response = await fetch(`/api/sessions/${sessionName}/transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_agent_id: fromAgentId,
          to_agent_id: toAgentId,
          to_agent_name: toAgentName,
          reason: reason,
          note: note
        })
      })

      const data = await response.json()

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('只有当前服务的坐席才能转接会话')
        } else if (response.status === 409) {
          throw new Error('当前会话状态不允许转接')
        }
        throw new Error(data.detail || '转接失败')
      }

      if (data.success) {
        console.log('✅ 已发送转接请求:', sessionName, '->', toAgentName)
        return true
      }

      return false
    } catch (err: any) {
      error.value = err.message
      console.error('❌ 转接会话失败:', err)
      throw err
    }
  }

  // 发送消息
  async function sendMessage(sessionName: string, content: string, agentId: string, agentName: string) {
    try {
      const response = await fetch('/api/manual/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_name: sessionName,
          role: 'agent',
          content: content,
          agent_info: {
            agent_id: agentId,
            agent_name: agentName
          }
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || '发送失败')
      }

      if (data.success) {
        console.log('✅ 发送消息成功')
        // 刷新会话详情
        await fetchSessionDetail(sessionName)
        return true
      }

      return false
    } catch (err: any) {
      error.value = err.message
      console.error('❌ 发送消息失败:', err)
      throw err
    }
  }

  // 清空当前会话
  function clearCurrentSession() {
    currentSession.value = null
    currentSessionName.value = ''
  }

  // 设置筛选条件并刷新
  async function setFilter(status: SessionStatus | '') {
    filterStatus.value = status
    await fetchSessions(status || undefined)
  }

  // 【模块2】获取等待队列
  async function fetchQueue() {
    try {
      const token = getAccessToken()
      const headers: HeadersInit = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${API_BASE}/api/sessions/queue`, { headers })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: QueueResponse = await response.json()

      if (data.success) {
        queueData.value = data.data.queue
        queueStats.value = {
          total_count: data.data.total_count,
          vip_count: data.data.vip_count,
          avg_wait_time: data.data.avg_wait_time,
          max_wait_time: data.data.max_wait_time
        }
        console.log(`✅ 获取队列成功: 总数 ${queueStats.value.total_count}, VIP ${queueStats.value.vip_count}`)
      } else {
        throw new Error('获取队列失败')
      }
    } catch (err: any) {
      console.error('❌ 获取队列失败:', err)
      // 失败时清空队列数据
      queueData.value = []
      queueStats.value = {
        total_count: 0,
        vip_count: 0,
        avg_wait_time: 0,
        max_wait_time: 0
      }
    }
  }

  return {
    // 状态
    sessions,
    total,
    isLoading,
    error,
    currentSession,
    currentSessionName,
    stats,
    filterStatus,
    // 【模块2】队列相关状态
    queueData,
    queueStats,

    // 计算属性
    pendingCount,
    manualLiveCount,
    selectedSession,

    // 方法
    fetchSessions,
    fetchSessionsAdvanced, // 【L1-1-Part1-模块1】新增高级筛选方法
    fetchStats,
    fetchSessionDetail,
    takeoverSession,
    releaseSession,
    transferSession,
    sendMessage,
    clearCurrentSession,
    setFilter,
    // 【模块2】队列管理方法
    fetchQueue
  }
})
