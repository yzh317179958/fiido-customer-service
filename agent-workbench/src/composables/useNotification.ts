/**
 * 消息提醒系统 Composable
 *
 * 功能需求: prd/04_任务拆解/L1-1-Part3_协作与工作台优化.md F6-2, F6-3, F6-4
 *
 * 支持的提醒类型:
 * - 会话提醒: 新会话、VIP会话、客户回复、会话超时
 * - 协作提醒: @提醒、协助请求、转接请求
 * - 系统提醒: 离线提醒、会话分配
 *
 * 功能:
 * - 浏览器通知 (Notification API)
 * - 标签页标题闪烁
 * - 声音提醒
 * - 提醒配置管理
 */

import { ref, computed } from 'vue'

// ==================== 类型定义 ====================

/**
 * 提醒类型
 */
export const NotificationTypes = {
  // 会话提醒
  NEW_SESSION: 'new_session',
  VIP_SESSION: 'vip_session',
  CUSTOMER_REPLY: 'customer_reply',
  SESSION_TIMEOUT: 'session_timeout',

  // 协作提醒
  MENTION: 'mention',
  ASSIST_REQUEST: 'assist_request',
  TRANSFER_REQUEST: 'transfer_request',

  // 系统提醒
  OFFLINE: 'offline',
  SESSION_ASSIGNED: 'session_assigned'
} as const

export type NotificationType = typeof NotificationTypes[keyof typeof NotificationTypes]

/**
 * 提醒配置
 */
export interface NotificationSettings {
  // 会话提醒开关
  new_session: boolean          // 新会话提醒
  vip_session: boolean          // VIP会话提醒
  customer_reply: boolean       // 客户回复提醒

  // 协作提醒开关
  mention: boolean              // @提醒
  assist_request: boolean       // 协助请求提醒
  transfer_request: boolean     // 转接请求提醒

  // 声音设置
  sound_enabled: boolean        // 声音开关
  sound_volume: number          // 音量 (0-100)
  sound_type: string            // 提示音类型
  quiet_mode_enabled: boolean   // 静音模式
  quiet_mode_start: string      // 静音开始时间 (HH:mm)
  quiet_mode_end: string        // 静音结束时间 (HH:mm)
}

/**
 * 通知选项
 */
export interface NotificationOptions {
  type: NotificationType
  title: string
  body: string
  icon?: string
  tag?: string                  // 用于替换旧通知
  requireInteraction?: boolean  // 是否需要用户交互才关闭
  actions?: Array<{             // 通知操作按钮（部分浏览器支持）
    action: string
    title: string
  }>
  data?: any                    // 附加数据
  playSound?: boolean           // 是否播放声音
  flash?: boolean               // 是否闪烁标题
}

// ==================== 状态管理 ====================

// 通知权限状态
const notificationPermission = ref<NotificationPermission>('default')

// 提醒配置（从 localStorage 加载）
const settings = ref<NotificationSettings>({
  new_session: true,
  vip_session: true,
  customer_reply: true,
  mention: true,
  assist_request: true,
  transfer_request: true,
  sound_enabled: true,
  sound_volume: 80,
  sound_type: 'default',
  quiet_mode_enabled: false,
  quiet_mode_start: '22:00',
  quiet_mode_end: '08:00'
})

// 未读通知计数
const unreadCount = ref(0)

// 标题闪烁定时器
let titleFlashInterval: number | null = null
const originalTitle = document.title
const isFlashing = ref(false)

// 音频对象缓存
const audioCache: { [key: string]: HTMLAudioElement } = {}

// ==================== 工具函数 ====================

/**
 * 检查是否在静音时段
 */
function isInQuietMode(): boolean {
  if (!settings.value.quiet_mode_enabled) {
    return false
  }

  const now = new Date()
  const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`

  const start = settings.value.quiet_mode_start
  const end = settings.value.quiet_mode_end

  // 处理跨日情况（如 22:00 - 08:00）
  if (start > end) {
    return currentTime >= start || currentTime < end
  } else {
    return currentTime >= start && currentTime < end
  }
}

/**
 * 检查是否应该发送通知
 */
function shouldNotify(type: NotificationType): boolean {
  // 检查提醒开关
  const typeSettingMap: { [key: string]: keyof NotificationSettings } = {
    [NotificationTypes.NEW_SESSION]: 'new_session',
    [NotificationTypes.VIP_SESSION]: 'vip_session',
    [NotificationTypes.CUSTOMER_REPLY]: 'customer_reply',
    [NotificationTypes.MENTION]: 'mention',
    [NotificationTypes.ASSIST_REQUEST]: 'assist_request',
    [NotificationTypes.TRANSFER_REQUEST]: 'transfer_request'
  }

  const settingKey = typeSettingMap[type]
  if (settingKey && !settings.value[settingKey]) {
    return false
  }

  // 检查通知权限
  if (notificationPermission.value !== 'granted') {
    return false
  }

  return true
}

/**
 * 检查是否应该播放声音
 */
function shouldPlaySound(type: NotificationType): boolean {
  if (!settings.value.sound_enabled) {
    return false
  }

  if (isInQuietMode()) {
    return false
  }

  // 某些提醒类型默认不播放声音（如客户回复）
  const soundTypes: NotificationType[] = [
    NotificationTypes.NEW_SESSION,
    NotificationTypes.VIP_SESSION,
    NotificationTypes.SESSION_TIMEOUT,
    NotificationTypes.TRANSFER_REQUEST
  ]

  return soundTypes.includes(type)
}

// ==================== 核心功能 ====================

/**
 * 请求通知权限
 */
async function requestPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.warn('浏览器不支持通知功能')
    return 'denied'
  }

  if (!window.isSecureContext) {
    console.warn('通知权限申请需要在 HTTPS 或 localhost 环境下进行')
    notificationPermission.value = 'denied'
    return 'denied'
  }

  try {
    const permission = await Notification.requestPermission()
    notificationPermission.value = permission
    return permission
  } catch (error) {
    console.error('请求通知权限失败:', error)
    notificationPermission.value = 'denied'
    return 'denied'
  }
}

/**
 * 显示浏览器通知
 */
function showNotification(options: NotificationOptions): Notification | null {
  if (!shouldNotify(options.type)) {
    console.log('通知已禁用或权限不足:', options.type)
    return null
  }

  try {
    const notification = new Notification(options.title, {
      body: options.body,
      icon: options.icon || '/favicon.ico',
      tag: options.tag || `${options.type}_${Date.now()}`,
      requireInteraction: options.requireInteraction || false,
      data: options.data
    })

    // 点击通知时的处理
    notification.onclick = () => {
      window.focus()
      notification.close()

      // 触发自定义事件，由外部处理（如跳转到会话）
      if (options.data) {
        window.dispatchEvent(new CustomEvent('notification-click', {
          detail: options.data
        }))
      }
    }

    // 增加未读计数
    unreadCount.value++

    // 播放声音
    if (options.playSound !== false && shouldPlaySound(options.type)) {
      playSound(options.type)
    }

    // 闪烁标题
    if (options.flash !== false) {
      startTitleFlash()
    }

    return notification
  } catch (error) {
    console.error('显示通知失败:', error)
    return null
  }
}

/**
 * 播放提示音
 */
function playSound(type: NotificationType) {
  try {
    const soundFile = getSoundFile(type)

    // 从缓存获取或创建新的音频对象
    if (!audioCache[soundFile]) {
      audioCache[soundFile] = new Audio(soundFile)
    }

    const audio = audioCache[soundFile]
    audio.volume = settings.value.sound_volume / 100
    audio.play().catch(err => {
      console.warn('播放声音失败（可能需要用户交互）:', err)
    })
  } catch (error) {
    console.error('播放声音失败:', error)
  }
}

/**
 * 获取声音文件路径
 */
function getSoundFile(type: NotificationType): string {
  // VIP会话使用特殊提示音
  if (type === NotificationTypes.VIP_SESSION) {
    return '/sounds/vip-notification.mp3'
  }

  // 其他使用默认提示音
  return '/sounds/notification.mp3'
}

/**
 * 开始标题闪烁
 */
function startTitleFlash() {
  if (isFlashing.value) {
    return // 已经在闪烁
  }

  isFlashing.value = true
  let toggle = false

  titleFlashInterval = window.setInterval(() => {
    if (toggle) {
      document.title = originalTitle
    } else {
      document.title = `🔴 (${unreadCount.value}) 新消息 - Fiido`
    }
    toggle = !toggle
  }, 1000)
}

/**
 * 停止标题闪烁
 */
function stopTitleFlash() {
  if (titleFlashInterval) {
    clearInterval(titleFlashInterval)
    titleFlashInterval = null
  }
  isFlashing.value = false
  document.title = originalTitle
}

/**
 * 清除未读计数
 */
function clearUnreadCount() {
  unreadCount.value = 0
  stopTitleFlash()
}

/**
 * 加载配置
 */
function loadSettings() {
  try {
    const saved = localStorage.getItem('notification_settings')
    if (saved) {
      settings.value = { ...settings.value, ...JSON.parse(saved) }
    }
  } catch (error) {
    console.error('加载通知配置失败:', error)
  }
}

/**
 * 保存配置
 */
function saveSettings() {
  try {
    localStorage.setItem('notification_settings', JSON.stringify(settings.value))
  } catch (error) {
    console.error('保存通知配置失败:', error)
  }
}

/**
 * 更新配置
 */
function updateSettings(newSettings: Partial<NotificationSettings>) {
  settings.value = { ...settings.value, ...newSettings }
  saveSettings()
}

// ==================== 便捷方法 ====================

/**
 * 新会话通知
 */
function notifyNewSession(sessionName: string, customerName?: string) {
  showNotification({
    type: NotificationTypes.NEW_SESSION,
    title: '🔔 新会话',
    body: customerName ? `客户 ${customerName} 请求人工服务` : '有新会话进入队列',
    tag: 'new_session',
    data: { sessionName }
  })
}

/**
 * VIP会话通知
 */
function notifyVIPSession(sessionName: string, customerName: string, issue?: string) {
  showNotification({
    type: NotificationTypes.VIP_SESSION,
    title: '⭐ VIP客户',
    body: issue ? `VIP客户 ${customerName} 咨询${issue}` : `VIP客户 ${customerName} 请求服务`,
    tag: 'vip_session',
    requireInteraction: true,
    data: { sessionName }
  })
}

/**
 * 客户回复通知
 */
function notifyCustomerReply(sessionName: string, message: string) {
  showNotification({
    type: NotificationTypes.CUSTOMER_REPLY,
    title: '💬 客户回复',
    body: message.length > 50 ? message.substring(0, 50) + '...' : message,
    tag: `customer_reply_${sessionName}`,
    playSound: false, // 客户回复不播放声音
    data: { sessionName }
  })
}

/**
 * 协助请求通知
 */
function notifyAssistRequest(requester: string, question: string, requestId: string) {
  showNotification({
    type: NotificationTypes.ASSIST_REQUEST,
    title: '🤝 协助请求',
    body: `${requester} 请求协助: ${question.substring(0, 50)}${question.length > 50 ? '...' : ''}`,
    tag: 'assist_request',
    data: { requestId }
  })
}

/**
 * 转接请求通知
 */
function notifyTransferRequest(fromAgent: string, sessionName: string, reason?: string) {
  showNotification({
    type: NotificationTypes.TRANSFER_REQUEST,
    title: '🔀 转接请求',
    body: reason ? `${fromAgent} 转接会话: ${reason}` : `${fromAgent} 转接会话给你`,
    tag: 'transfer_request',
    data: { sessionName }
  })
}

/**
 * @提醒通知
 */
function notifyMention(fromAgent: string, sessionName: string, content: string) {
  showNotification({
    type: NotificationTypes.MENTION,
    title: '@ 有人提到你',
    body: `${fromAgent} 在会话中@了你: ${content.substring(0, 50)}${content.length > 50 ? '...' : ''}`,
    tag: 'mention',
    data: { sessionName }
  })
}

/**
 * 离线提醒（Toast，不使用浏览器通知）
 */
function notifyOffline() {
  // 这个应该使用 Toast 组件，而不是浏览器通知
  window.dispatchEvent(new CustomEvent('show-toast', {
    detail: {
      type: 'warning',
      message: '⚠️ 网络已断开，正在尝试重新连接...'
    }
  }))
}

// ==================== 初始化 ====================

// 页面加载时检查权限
if ('Notification' in window) {
  notificationPermission.value = Notification.permission
}

// 加载配置
loadSettings()

// 页面获得焦点时清除未读计数
window.addEventListener('focus', () => {
  clearUnreadCount()
})

// ==================== 导出 ====================

export function useNotification() {
  return {
    // 状态
    notificationPermission: computed(() => notificationPermission.value),
    settings: computed(() => settings.value),
    unreadCount: computed(() => unreadCount.value),
    isFlashing: computed(() => isFlashing.value),

    // 方法
    requestPermission,
    showNotification,
    updateSettings,
    clearUnreadCount,

    // 便捷方法
    notifyNewSession,
    notifyVIPSession,
    notifyCustomerReply,
    notifyAssistRequest,
    notifyTransferRequest,
    notifyMention,
    notifyOffline
  }
}
