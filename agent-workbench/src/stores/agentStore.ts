import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LoginRequest, AgentRole } from '@/types'

export const useAgentStore = defineStore('agent', () => {
  const agentId = ref<string>('')
  const agentName = ref<string>('')
  const agentRole = ref<AgentRole>('agent')  // 新增：坐席角色
  const isLoggedIn = ref<boolean>(false)

  async function login(data: LoginRequest) {
    // 🔴 P0-11.2: 简化版登录（实际应该调用JWT认证接口）
    // 🔴 v3.1.3: 添加 role 支持（从 LoginRequest 或默认为 'agent'）
    agentId.value = data.agentId
    agentName.value = data.agentName
    agentRole.value = (data as any).role || 'agent'  // 获取角色，默认为 agent
    isLoggedIn.value = true

    // 保存到localStorage
    localStorage.setItem('agent_info', JSON.stringify({
      agentId: data.agentId,
      agentName: data.agentName,
      role: agentRole.value
    }))

    console.log('✅ 坐席登录成功:', { ...data, role: agentRole.value })
  }

  function logout() {
    agentId.value = ''
    agentName.value = ''
    agentRole.value = 'agent'
    isLoggedIn.value = false
    localStorage.removeItem('agent_info')
    localStorage.removeItem('access_token')  // 清除 JWT Token
    console.log('👋 坐席已登出')
  }

  function restoreSession() {
    const saved = localStorage.getItem('agent_info')
    if (saved) {
      try {
        const data = JSON.parse(saved)
        agentId.value = data.agentId
        agentName.value = data.agentName
        agentRole.value = data.role || 'agent'
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
    agentRole,  // 新增
    isLoggedIn,
    login,
    logout,
    restoreSession
  }
})
