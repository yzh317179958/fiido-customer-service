const TOKEN_KEY = 'access_token'
const AGENT_INFO_KEY = 'agent_info'

type StorageType = 'session' | 'local'

const memoryStorage = new Map<string, string>()
const storageErrorLogged: Partial<Record<StorageType, boolean>> = {}

const logStorageWarning = (type: StorageType, error: unknown) => {
  if (storageErrorLogged[type]) return
  console.warn(`[storage] ${type}Storage 不可用，将退回内存存储`, error)
  storageErrorLogged[type] = true
}

const getBrowserStorage = (type: StorageType): Storage | null => {
  if (typeof window === 'undefined') {
    return null
  }
  try {
    return type === 'session' ? window.sessionStorage : window.localStorage
  } catch (error) {
    logStorageWarning(type, error)
    return null
  }
}

const safeGetItem = (storage: Storage | null, key: string, type: StorageType): string | null => {
  if (!storage) return null
  try {
    const value = storage.getItem(key)
    return value === null ? null : value
  } catch (error) {
    logStorageWarning(type, error)
    return null
  }
}

const safeSetItem = (storage: Storage | null, key: string, value: string, type: StorageType): boolean => {
  if (!storage) return false
  try {
    storage.setItem(key, value)
    return true
  } catch (error) {
    logStorageWarning(type, error)
    return false
  }
}

const safeRemoveItem = (storage: Storage | null, key: string, type: StorageType) => {
  if (!storage) return
  try {
    storage.removeItem(key)
  } catch (error) {
    logStorageWarning(type, error)
  }
}

const getValue = (key: string): string | null => {
  const sessionStorage = getBrowserStorage('session')
  const sessionValue = safeGetItem(sessionStorage, key, 'session')
  if (sessionValue) {
    return sessionValue
  }

  const localStorage = getBrowserStorage('local')
  const localValue = safeGetItem(localStorage, key, 'local')
  if (localValue) {
    // 尝试同步到 sessionStorage，若失败则存入内存
    if (!safeSetItem(sessionStorage, key, localValue, 'session')) {
      memoryStorage.set(key, localValue)
    }
    safeRemoveItem(localStorage, key, 'local')
    return localValue
  }

  return memoryStorage.get(key) ?? null
}

const setValue = (key: string, value: string) => {
  const sessionStorage = getBrowserStorage('session')
  const stored = safeSetItem(sessionStorage, key, value, 'session')

  if (!stored) {
    memoryStorage.set(key, value)
  } else {
    memoryStorage.delete(key)
  }

  // 为避免跨标签冲突，强制移除 localStorage 中的旧数据
  const localStorage = getBrowserStorage('local')
  safeRemoveItem(localStorage, key, 'local')
}

const clearValue = (key: string) => {
  const sessionStorage = getBrowserStorage('session')
  const localStorage = getBrowserStorage('local')
  safeRemoveItem(sessionStorage, key, 'session')
  safeRemoveItem(localStorage, key, 'local')
  memoryStorage.delete(key)
}

export const setAccessToken = (token: string) => {
  setValue(TOKEN_KEY, token)
}

export const getAccessToken = (): string | null => {
  return getValue(TOKEN_KEY)
}

export const clearAccessToken = () => {
  clearValue(TOKEN_KEY)
}

export interface StoredAgentInfo {
  agentId: string
  agentName: string
  role: string
}

export const setAgentInfo = (info: StoredAgentInfo) => {
  setValue(AGENT_INFO_KEY, JSON.stringify(info))
}

export const getAgentInfo = (): StoredAgentInfo | null => {
  const raw = getValue(AGENT_INFO_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (error) {
    console.error('解析 agent_info 失败:', error)
    clearValue(AGENT_INFO_KEY)
    return null
  }
}

export const clearAgentInfo = () => {
  clearValue(AGENT_INFO_KEY)
}
