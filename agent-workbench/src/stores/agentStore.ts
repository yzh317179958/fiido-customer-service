import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LoginRequest } from '@/types'

export const useAgentStore = defineStore('agent', () => {
  const agentId = ref<string>('')
  const agentName = ref<string>('')
  const isLoggedIn = ref<boolean>(false)

  async function login(data: LoginRequest) {
    // 🔴 P0-11.2: 简化版登录（实际应该调用JWT认证接口）
    agentId.value = data.agentId
    agentName.value = data.agentName
    isLoggedIn.value = true

    // 保存到localStorage
    localStorage.setItem('agent_info', JSON.stringify(data))

    console.log('✅ 坐席登录成功:', data)
  }

  function logout() {
    agentId.value = ''
    agentName.value = ''
    isLoggedIn.value = false
    localStorage.removeItem('agent_info')
    console.log('👋 坐席已登出')
  }

  function restoreSession() {
    const saved = localStorage.getItem('agent_info')
    if (saved) {
      try {
        const data = JSON.parse(saved)
        agentId.value = data.agentId
        agentName.value = data.agentName
        isLoggedIn.value = true
        console.log('✅ 恢复坐席会话:', data)
      } catch (error) {
        console.error('❌ 恢复会话失败:', error)
        localStorage.removeItem('agent_info')
      }
    }
  }

  return {
    agentId,
    agentName,
    isLoggedIn,
    login,
    logout,
    restoreSession
  }
})
