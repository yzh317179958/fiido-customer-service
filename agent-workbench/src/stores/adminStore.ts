/**
 * 管理员功能 Store
 * 用于管理坐席账号的 CRUD 操作
 *
 * @version v3.1.3
 * @author Claude Code
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { getAccessToken } from '@/utils/authStorage'
import type {
  Agent,
  CreateAgentRequest,
  UpdateAgentRequest,
  ResetPasswordRequest,
  ChangePasswordRequest,
  UpdateProfileRequest,
  AgentsListResponse,
  AgentResponse
} from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const useAdminStore = defineStore('admin', () => {
  // 状态
  const agents = ref<Agent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取 Authorization Header
  function getAuthHeader() {
    const token = getAccessToken()
    if (!token) {
      throw new Error('未登录或Token已过期')
    }
    return { Authorization: `Bearer ${token}` }
  }

  // ==================== 管理员 API（需要 admin 权限）====================

  /**
   * 获取坐席列表
   * @param params 查询参数（role, status, page, page_size）
   */
  async function fetchAgents(params?: {
    role?: string
    status?: string
    page?: number
    page_size?: number
  }) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get<AgentsListResponse>(`${API_BASE}/api/agents`, {
        headers: getAuthHeader(),
        params: {
          page: params?.page || 1,
          page_size: params?.page_size || 20,
          ...(params?.role && { role: params.role }),
          ...(params?.status && { status: params.status })
        }
      })

      if (response.data.success) {
        agents.value = response.data.data.items
      } else {
        throw new Error('获取坐席列表失败')
      }
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || e.message || '获取坐席列表失败'
      error.value = errorMsg
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建坐席
   * @param data 创建坐席请求数据
   */
  async function createAgent(data: CreateAgentRequest) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.post<AgentResponse>(
        `${API_BASE}/api/agents`,
        data,
        { headers: getAuthHeader() }
      )

      if (response.data.success) {
        // 刷新列表
        await fetchAgents()
      } else {
        throw new Error(response.data.message || '创建坐席失败')
      }
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || e.message || '创建坐席失败'
      error.value = errorMsg
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  /**
   * 修改坐席信息
   * @param username 坐席用户名
   * @param data 修改数据
   */
  async function updateAgent(username: string, data: UpdateAgentRequest) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.put<AgentResponse>(
        `${API_BASE}/api/agents/${username}`,
        data,
        { headers: getAuthHeader() }
      )

      if (response.data.success) {
        // 刷新列表
        await fetchAgents()
      } else {
        throw new Error(response.data.message || '修改坐席失败')
      }
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || e.message || '修改坐席失败'
      error.value = errorMsg
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除坐席
   * @param username 坐席用户名
   */
  async function deleteAgent(username: string) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.delete<AgentResponse>(
        `${API_BASE}/api/agents/${username}`,
        { headers: getAuthHeader() }
      )

      if (response.data.success) {
        // 刷新列表
        await fetchAgents()
      } else {
        throw new Error(response.data.message || '删除坐席失败')
      }
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || e.message || '删除坐席失败'
      error.value = errorMsg
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  /**
   * 重置坐席密码（管理员操作）
   * @param username 坐席用户名
   * @param newPassword 新密码
   */
  async function resetPassword(username: string, newPassword: string) {
    loading.value = true
    error.value = null
    try {
      const data: ResetPasswordRequest = { new_password: newPassword }
      const response = await axios.post<AgentResponse>(
        `${API_BASE}/api/agents/${username}/reset-password`,
        data,
        { headers: getAuthHeader() }
      )

      if (!response.data.success) {
        throw new Error(response.data.message || '重置密码失败')
      }
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || e.message || '重置密码失败'
      error.value = errorMsg
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  // ==================== 坐席自助 API（需要 agent 权限）====================

  /**
   * 修改自己的密码
   * @param oldPassword 旧密码
   * @param newPassword 新密码
   */
  async function changeOwnPassword(oldPassword: string, newPassword: string) {
    loading.value = true
    error.value = null
    try {
      const data: ChangePasswordRequest = {
        old_password: oldPassword,
        new_password: newPassword
      }
      const response = await axios.post<AgentResponse>(
        `${API_BASE}/api/agent/change-password`,
        data,
        { headers: getAuthHeader() }
      )

      if (!response.data.success) {
        throw new Error(response.data.message || '修改密码失败')
      }
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || e.message || '修改密码失败'
      error.value = errorMsg
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  /**
   * 修改个人资料
   * @param data 修改数据（name, avatar_url）
   */
  async function updateProfile(data: UpdateProfileRequest) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.put<AgentResponse>(
        `${API_BASE}/api/agent/profile`,
        data,
        { headers: getAuthHeader() }
      )

      if (!response.data.success) {
        throw new Error(response.data.message || '修改资料失败')
      }

      // 返回更新后的坐席信息
      return response.data.agent
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || e.message || '修改资料失败'
      error.value = errorMsg
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  // 返回 Store 接口
  return {
    // 状态
    agents,
    loading,
    error,

    // 管理员 API
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    resetPassword,

    // 坐席自助 API
    changeOwnPassword,
    updateProfile
  }
})
