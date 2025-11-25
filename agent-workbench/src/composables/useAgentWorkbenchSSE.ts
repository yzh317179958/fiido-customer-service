/**
 * 坐席工作台 SSE 实时监听
 *
 * 使用 Fetch API + ReadableStream 实现 POST SSE
 * （因为 EventSource 只支持 GET 请求）
 *
 * 功能：
 * 1. 轮询会话列表，但使用 SSE 监听单个会话的实时消息
 * 2. 监听人工消息和状态变化
 * 3. 自动刷新相关数据
 *
 * 遵守约束：
 * - CLAUDE.md: 不修改后端核心逻辑
 * - CLAUDE.md: 实时性要求 < 100ms 推送延迟
 * - CLAUDE.md: 并发控制，限制 SSE 连接数
 */

import { ref, watch } from 'vue'
import { useSessionStore } from '../stores/sessionStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface SSEMessage {
  type: string
  [key: string]: any
}

/**
 * 使用 Fetch API 建立 SSE 连接（支持 POST）
 */
class FetchSSE {
  url: string
  options: {
    method?: string
    headers?: Record<string, string>
    body?: string
    onMessage?: (data: SSEMessage) => void
    onError?: (error: any) => void
    onOpen?: () => void
  }
  controller: AbortController | null = null
  reader: ReadableStreamDefaultReader<Uint8Array> | null = null

  constructor(
    url: string,
    options: {
      method?: string
      headers?: Record<string, string>
      body?: string
      onMessage?: (data: SSEMessage) => void
      onError?: (error: any) => void
      onOpen?: () => void
    }
  ) {
    this.url = url
    this.options = options
  }

  async connect() {
    try {
      this.controller = new AbortController()

      const response = await fetch(this.url, {
        method: this.options.method || 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.options.headers
        },
        body: this.options.body,
        signal: this.controller.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      if (!response.body) {
        throw new Error('响应体为空')
      }

      if (this.options.onOpen) {
        this.options.onOpen()
      }

      this.reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await this.reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 解析 SSE 消息（格式：data: {...}\n\n）
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6)) as SSEMessage
              if (this.options.onMessage) {
                this.options.onMessage(data)
              }
            } catch (err) {
              console.error('SSE 消息解析失败:', err)
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('SSE 连接错误:', error)
        if (this.options.onError) {
          this.options.onError(error)
        }
      }
    }
  }

  disconnect() {
    if (this.controller) {
      this.controller.abort()
      this.controller = null
    }

    if (this.reader) {
      this.reader.cancel()
      this.reader = null
    }
  }
}

/**
 * 坐席工作台实时监听
 *
 * 策略：
 * 1. 使用轻量级轮询（30秒）刷新会话列表（检测新会话）
 * 2. 对当前选中的会话建立 SSE 连接，实时接收消息
 * 3. 当收到状态变化或新消息时，立即刷新相关数据
 */
export function useAgentWorkbenchSSE() {
  const sessionStore = useSessionStore()

  // 当前监听的会话 SSE 连接
  const currentSessionSSE = ref<FetchSSE | null>(null)

  // 轮询定时器
  const pollTimer = ref<number | null>(null)

  // 监听状态
  const isMonitoring = ref(false)

  /**
   * 为当前选中的会话建立 SSE 监听
   */
  const monitorCurrentSession = () => {
    // 关闭之前的连接
    if (currentSessionSSE.value) {
      currentSessionSSE.value.disconnect()
      currentSessionSSE.value = null
    }

    const selectedSession = sessionStore.selectedSession
    if (!selectedSession) {
      return
    }

    const sessionName = selectedSession.session_name

    console.log(`🔌 建立 SSE 监听: ${sessionName}`)

    currentSessionSSE.value = new FetchSSE(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: '',  // 空消息，仅建立连接
        user_id: sessionName,
        conversation_id: selectedSession.conversation_id
      }),
      onOpen: () => {
        console.log(`✅ SSE 连接已建立: ${sessionName}`)
      },
      onMessage: (data) => {
        console.log(`📨 收到 SSE 消息:`, data.type)

        switch (data.type) {
          case 'status_change':
            // 状态变化：刷新会话列表和详情
            console.log(`🔄 状态变化: ${data.status}`)
            sessionStore.fetchSessions()
            sessionStore.fetchStats()
            if (sessionName === sessionStore.selectedSession?.session_name) {
              sessionStore.fetchSessionDetail(sessionName)
            }
            break

          case 'manual_message':
            // 人工消息：刷新会话详情
            console.log(`💬 新消息 from ${data.role}`)
            if (sessionName === sessionStore.selectedSession?.session_name) {
              sessionStore.fetchSessionDetail(sessionName)
            }
            break

          case 'message':
            // AI 消息（忽略，因为坐席工作台不关心 AI 对话）
            break

          case 'done':
            // 完成标记
            break

          case 'error':
            console.error(`❌ SSE 错误: ${data.content}`)
            break

          default:
            console.log(`ℹ️  未知事件: ${data.type}`)
        }
      },
      onError: (error) => {
        console.error(`❌ SSE 连接失败:`, error)

        // 3秒后尝试重连
        setTimeout(() => {
          if (isMonitoring.value && sessionStore.selectedSession?.session_name === sessionName) {
            monitorCurrentSession()
          }
        }, 3000)
      }
    })

    currentSessionSSE.value.connect()
  }

  /**
   * 启动实时监听
   *
   * 策略：
   * 1. 每30秒轮询会话列表（检测新会话和状态变化）
   * 2. 对当前选中的会话建立 SSE 连接（实时消息）
   * 3. 符合 CLAUDE.md 的并发性要求（轻量级轮询 + 单个 SSE）
   */
  const startMonitoring = async () => {
    if (isMonitoring.value) {
      console.log('⚠️  已在监听中')
      return
    }

    console.log('🚀 启动实时监听')
    isMonitoring.value = true

    // 初始加载
    await sessionStore.fetchSessions()
    await sessionStore.fetchStats()

    // 如果有选中的会话，建立 SSE
    if (sessionStore.selectedSession) {
      monitorCurrentSession()
    }

    // 轻量级轮询：30秒刷新一次会话列表
    // （比之前的 5秒轮询节省 83% 的资源）
    pollTimer.value = window.setInterval(async () => {
      console.log('🔄 轮询刷新会话列表 (30s)')
      await sessionStore.fetchSessions()
      await sessionStore.fetchStats()
    }, 30000) // 30秒
  }

  /**
   * 停止实时监听
   */
  const stopMonitoring = () => {
    console.log('⏹️  停止实时监听')
    isMonitoring.value = false

    // 清除轮询定时器
    if (pollTimer.value) {
      clearInterval(pollTimer.value)
      pollTimer.value = null
    }

    // 关闭 SSE 连接
    if (currentSessionSSE.value) {
      currentSessionSSE.value.disconnect()
      currentSessionSSE.value = null
    }
  }

  // 监听选中会话变化，自动切换 SSE 连接
  watch(
    () => sessionStore.selectedSession,
    (newSession, oldSession) => {
      if (!isMonitoring.value) return

      if (newSession?.session_name !== oldSession?.session_name) {
        console.log(`🔄 切换监听会话: ${oldSession?.session_name} -> ${newSession?.session_name}`)
        monitorCurrentSession()
      }
    }
  )

  return {
    isMonitoring,
    startMonitoring,
    stopMonitoring
  }
}
