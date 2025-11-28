import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LoginRequest, AgentRole } from '@/types'
import {
  clearAccessToken,
  clearAgentInfo,
  getAccessToken,
  getAgentInfo,
  setAgentInfo
} from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const useAgentStore = defineStore('agent', () => {
  const agentId = ref<string>('')
  const agentName = ref<string>('')
  const agentRole = ref<AgentRole>('agent')  // 新增：坐席角色
  const isLoggedIn = ref<boolean>(false)
  let unloadHandler: (() => void) | null = null

  const sendOfflineBeacon = () => {
    if (!agentId.value) return
    const url = `${API_BASE}/api/agent/logout?username=${encodeURIComponent(agentId.value)}`
    if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
      const blob = new Blob([], { type: 'text/plain' })
      navigator.sendBeacon(url, blob)
    } else if (typeof fetch !== 'undefined') {
      fetch(url, { method: 'POST', keepalive: true }).catch(() => {})
    }
  }

  const updateStatusOffline = async () => {
    if (!agentId.value || typeof fetch === 'undefined') return
    const url = `${API_BASE}/api/agent/logout?username=${encodeURIComponent(agentId.value)}`
    const token = getAccessToken()
    const headers: HeadersInit = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    try {
      await fetch(url, {
        method: 'POST',
        headers: Object.keys(headers).length ? headers : undefined,
        keepalive: true
      })
    } catch (error) {
      console.warn('⚠️ 上报坐席离线失败:', error)
    }
  }

  const registerUnloadHandler = () => {
    if (typeof window === 'undefined' || unloadHandler) return
    unloadHandler = () => {
      sendOfflineBeacon()
    }
    window.addEventListener('beforeunload', unloadHandler)
  }

  const cleanupUnloadHandler = () => {
    if (typeof window === 'undefined' || !unloadHandler) return
    window.removeEventListener('beforeunload', unloadHandler)
    unloadHandler = null
  }

  async function login(data: LoginRequest) {
    // 🔴 P0-11.2: 简化版登录（实际应该调用JWT认证接口）
    // 🔴 v3.1.3: 添加 role 支持（从 LoginRequest 或默认为 'agent'）
    agentId.value = data.agentId
    agentName.value = data.agentName
    agentRole.value = (data as any).role || 'agent'  // 获取角色，默认为 agent
    isLoggedIn.value = true
    registerUnloadHandler()

    // 保存到当前标签的 sessionStorage
    setAgentInfo({
      agentId: data.agentId,
      agentName: data.agentName,
      role: agentRole.value
    })

    console.log('✅ 坐席登录成功:', { ...data, role: agentRole.value })
  }

  async function logout() {
    await updateStatusOffline()
    cleanupUnloadHandler()
    agentId.value = ''
    agentName.value = ''
    agentRole.value = 'agent'
    isLoggedIn.value = false
    clearAgentInfo()
    clearAccessToken()
    console.log('👋 坐席已登出')
  }

  function restoreSession() {
    const saved = getAgentInfo()
    if (saved) {
      agentId.value = saved.agentId
      agentName.value = saved.agentName
      agentRole.value = (saved.role as AgentRole) || 'agent'
      isLoggedIn.value = true
      registerUnloadHandler()
      console.log('✅ 恢复坐席会话:', saved)
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
