/**
 * SSE 实时推送 Composable
 *
 * 用于坐席工作台的实时更新，替代轮询机制
 *
 * 遵守约束：
 * - CLAUDE.md 企业生产环境要求：SSE 优于轮询，延迟 < 100ms
 * - 并发控制：限制 SSE 连接数，避免资源耗尽
 * - 不修改后端核心逻辑：复用现有 SSE 队列机制
 */

import { ref, onUnmounted } from 'vue'

export interface SSEMessage {
  type: string
  [key: string]: any
}

export interface SSEOptions {
  onMessage?: (data: SSEMessage) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  autoReconnect?: boolean
  reconnectInterval?: number
}

/**
 * SSE 连接管理
 *
 * @param url - SSE 端点 URL
 * @param options - 配置选项
 */
export function useSSE(url: string, options: SSEOptions = {}) {
  const {
    onMessage,
    onError,
    onOpen,
    autoReconnect = true,
    reconnectInterval = 3000
  } = options

  const eventSource = ref<EventSource | null>(null)
  const isConnected = ref(false)
  const reconnectTimer = ref<number | null>(null)

  /**
   * 建立 SSE 连接
   */
  const connect = () => {
    // 如果已连接，先断开
    if (eventSource.value) {
      disconnect()
    }

    try {
      console.log(`🔌 建立 SSE 连接: ${url}`)

      eventSource.value = new EventSource(url)

      // 连接成功
      eventSource.value.onopen = () => {
        console.log('✅ SSE 连接已建立')
        isConnected.value = true

        // 清除重连定时器
        if (reconnectTimer.value) {
          clearTimeout(reconnectTimer.value)
          reconnectTimer.value = null
        }

        if (onOpen) {
          onOpen()
        }
      }

      // 接收消息
      eventSource.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as SSEMessage
          console.log('📨 收到 SSE 消息:', data.type)

          if (onMessage) {
            onMessage(data)
          }
        } catch (err) {
          console.error('❌ SSE 消息解析失败:', err)
        }
      }

      // 连接错误
      eventSource.value.onerror = (error) => {
        console.error('❌ SSE 连接错误:', error)
        isConnected.value = false

        // 关闭当前连接
        if (eventSource.value) {
          eventSource.value.close()
          eventSource.value = null
        }

        if (onError) {
          onError(error)
        }

        // 自动重连
        if (autoReconnect && !reconnectTimer.value) {
          console.log(`⏳ ${reconnectInterval}ms 后尝试重连...`)
          reconnectTimer.value = window.setTimeout(() => {
            reconnectTimer.value = null
            connect()
          }, reconnectInterval)
        }
      }
    } catch (err) {
      console.error('❌ 创建 SSE 连接失败:', err)
      isConnected.value = false
    }
  }

  /**
   * 断开 SSE 连接
   */
  const disconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }

    if (eventSource.value) {
      console.log('🔌 断开 SSE 连接')
      eventSource.value.close()
      eventSource.value = null
      isConnected.value = false
    }
  }

  /**
   * 手动重连
   */
  const reconnect = () => {
    disconnect()
    connect()
  }

  // 组件卸载时自动断开
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    connect,
    disconnect,
    reconnect
  }
}
