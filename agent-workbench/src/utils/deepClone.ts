export function deepClone<T>(value: T): T {
  if (typeof structuredClone === 'function') {
    try {
      return structuredClone(value)
    } catch (error) {
      console.warn('structuredClone fallback triggered:', error)
    }
  }
  // Fallback for浏览器不支持或 structuredClone 失败的情况
  return JSON.parse(JSON.stringify(value))
}
