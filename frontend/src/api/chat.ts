import type { ConversationResponse, BotConfig } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function loadBotConfig(): Promise<{ success: boolean; bot?: BotConfig }> {
  try {
    const response = await fetch(`${API_BASE}/api/bot/info`)
    return await response.json()
  } catch (error) {
    console.error('加载 Bot 配置失败:', error)
    return { success: false }
  }
}

export async function createNewConversation(sessionId: string): Promise<ConversationResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/conversation/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    })
    return await response.json()
  } catch (error) {
    console.error('创建对话失败:', error)
    return { success: false, error: String(error) }
  }
}

export async function clearConversationHistory(sessionId: string): Promise<ConversationResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/conversation/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    })
    return await response.json()
  } catch (error) {
    console.error('清除历史失败:', error)
    return { success: false, error: String(error) }
  }
}

export async function* streamChat(
  message: string,
  sessionId: string,
  conversationId?: string
): AsyncGenerator<{ type: string; content: string }> {
  const requestBody: any = {
    message,
    user_id: sessionId
  }

  if (conversationId) {
    requestBody.conversation_id = conversationId
  }

  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          yield data
        } catch (e) {
          console.error('解析 SSE 数据失败:', e)
        }
      }
    }
  }
}
