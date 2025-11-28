import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TransferHistoryRecord, TransferRequest } from '@/types'
import { getAccessToken } from '@/utils/authStorage'

export const useTransferStore = defineStore('transfer', () => {
  const pendingRequests = ref<TransferRequest[]>([])
  const loadingPending = ref(false)
  const history = ref<TransferHistoryRecord[]>([])
  const loadingHistory = ref(false)

  async function fetchPendingRequests() {
    loadingPending.value = true
    try {
      const token = getAccessToken()
      if (!token) {
        pendingRequests.value = []
        throw new Error('UNAUTHORIZED')
      }
      const response = await fetch('/api/transfer-requests/pending', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = await response.json()
      if (data.success) {
        pendingRequests.value = data.data || []
      }
      return data.data || []
    } catch (error) {
      console.error('❌ 获取转接请求失败:', error)
      throw error
    } finally {
      loadingPending.value = false
    }
  }

  async function respondTransferRequest(requestId: string, action: 'accept' | 'decline', responseNote?: string) {
    try {
      const token = getAccessToken()
      if (!token) {
        throw new Error('UNAUTHORIZED')
      }
      const response = await fetch(`/api/transfer-requests/${requestId}/respond`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          action,
          response_note: responseNote || ''
        })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || '处理失败')
      }

      // 刷新 pending 列表
      await fetchPendingRequests()
      return data
    } catch (error) {
      console.error('❌ 处理转接请求失败:', error)
      throw error
    }
  }

  async function fetchTransferHistory(sessionName: string) {
    if (!sessionName) {
      history.value = []
      return []
    }

    loadingHistory.value = true
    try {
      const token = getAccessToken()
      if (!token) {
        history.value = []
        throw new Error('UNAUTHORIZED')
      }
      const response = await fetch(`/api/sessions/${sessionName}/transfer-history`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = await response.json()
      if (data.success) {
        history.value = data.data || []
      }
      return history.value
    } catch (error) {
      console.error('❌ 获取转接历史失败:', error)
      history.value = []
      throw error
    } finally {
      loadingHistory.value = false
    }
  }

  function clearHistory() {
    history.value = []
  }

  return {
    pendingRequests,
    loadingPending,
    history,
    loadingHistory,
    fetchPendingRequests,
    respondTransferRequest,
    fetchTransferHistory,
    clearHistory
  }
})
