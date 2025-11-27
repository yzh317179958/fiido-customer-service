/**
 * 快捷键系统 Composable
 *
 * 功能：
 * - 注册全局快捷键
 * - 避免与浏览器原生快捷键冲突
 * - 在输入框聚焦时禁用可能干扰输入的快捷键
 *
 * @module useKeyboardShortcuts
 * @version v3.9.0
 * @date 2025-01-27
 */

import { onMounted, onUnmounted, ref } from 'vue'

export interface KeyboardShortcutHandler {
  handler: () => void
  description: string
  category?: 'navigation' | 'action' | 'function'
  allowInInput?: boolean  // 是否允许在输入框中触发
}

export interface KeyboardShortcuts {
  [key: string]: KeyboardShortcutHandler
}

/**
 * 检测当前焦点是否在输入框中
 */
function isInputFocused(): boolean {
  const activeElement = document.activeElement
  if (!activeElement) return false

  const tagName = activeElement.tagName.toLowerCase()
  const isContentEditable = (activeElement as HTMLElement).contentEditable === 'true'

  return (
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'select' ||
    isContentEditable
  )
}

/**
 * 格式化按键组合
 * 例如: Ctrl + f → "Ctrl+f"
 */
function formatKeyCombo(event: KeyboardEvent): string {
  const parts: string[] = []

  if (event.ctrlKey || event.metaKey) parts.push('Ctrl')
  if (event.altKey) parts.push('Alt')
  if (event.shiftKey) parts.push('Shift')

  // 标准化按键名称
  let key = event.key
  if (key === ' ') key = 'Space'
  if (key.length === 1) key = key.toLowerCase()

  // 特殊按键保持大小写
  if (['Enter', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
    // 保持原样
  }

  parts.push(key)

  return parts.join('+')
}

/**
 * 快捷键系统
 *
 * @param shortcuts - 快捷键配置
 * @returns 控制函数
 *
 * @example
 * ```ts
 * const { enable, disable, isEnabled } = useKeyboardShortcuts({
 *   'Ctrl+f': {
 *     handler: () => focusSearch(),
 *     description: '搜索会话',
 *     category: 'navigation'
 *   },
 *   'Ctrl+t': {
 *     handler: () => openTransferDialog(),
 *     description: '转接会话',
 *     category: 'action',
 *     allowInInput: false
 *   }
 * })
 * ```
 */
export function useKeyboardShortcuts(shortcuts: KeyboardShortcuts) {
  const enabled = ref(true)

  const handleKeyDown = (event: KeyboardEvent) => {
    if (!enabled.value) return

    const combo = formatKeyCombo(event)
    const shortcut = shortcuts[combo]

    if (!shortcut) return

    // 检查是否在输入框中
    const inInput = isInputFocused()

    // 如果在输入框中且快捷键不允许在输入框触发，则跳过
    if (inInput && !shortcut.allowInInput) {
      return
    }

    // 阻止默认行为并触发处理函数
    event.preventDefault()
    event.stopPropagation()
    shortcut.handler()
  }

  const enable = () => {
    enabled.value = true
  }

  const disable = () => {
    enabled.value = false
  }

  const isEnabled = () => enabled.value

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown, { capture: true })
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown, { capture: true })
  })

  return {
    enable,
    disable,
    isEnabled,
    shortcuts
  }
}

/**
 * 预定义的快捷键配置（P0 基础快捷键）
 *
 * 策略：使用 Ctrl+Shift 双修饰键避免与浏览器原生快捷键冲突
 *
 * 浏览器原生快捷键（需避免）：
 * - Ctrl+T: 新标签页
 * - Ctrl+N: 新窗口
 * - Ctrl+H: 历史记录
 * - Ctrl+L: 地址栏
 * - Ctrl+S: 保存页面
 * - Ctrl+R: 刷新页面
 * - Ctrl+F: 查找
 *
 * 安全方案：
 * - Ctrl+Shift+字母: 安全，不与浏览器冲突
 * - Ctrl+方向键: 安全，不与浏览器冲突
 */
export const DEFAULT_SHORTCUTS_P0 = {
  // 导航类
  'Ctrl+Shift+f': {
    description: '搜索会话',
    category: 'navigation' as const,
    allowInInput: false
  },
  'Ctrl+ArrowUp': {
    description: '上一个会话',
    category: 'navigation' as const,
    allowInInput: false
  },
  'Ctrl+ArrowDown': {
    description: '下一个会话',
    category: 'navigation' as const,
    allowInInput: false
  },
  'Escape': {
    description: '关闭面板',
    category: 'navigation' as const,
    allowInInput: true
  },

  // 操作类
  'Ctrl+Shift+t': {
    description: '转接会话',
    category: 'action' as const,
    allowInInput: false
  },
  'Ctrl+Shift+r': {
    description: '释放会话',
    category: 'action' as const,
    allowInInput: false
  },

  // 功能类
  'Ctrl+Shift+b': {
    description: '内部备注',
    category: 'function' as const,
    allowInInput: false
  },
  '?': {
    description: '快捷键帮助',
    category: 'function' as const,
    allowInInput: false
  }
}
