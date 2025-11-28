<template>
  <div v-if="visible" class="dialog-overlay" @click.self="closeDialog">
    <!-- Debug: 对话框已渲染 -->
    <div class="dialog-container">
      <div class="dialog-header">
        <h3>提醒设置</h3>
        <button class="close-btn" @click="closeDialog">&times;</button>
      </div>

      <div class="dialog-body">
        <!-- 通知权限状态 -->
        <div class="permission-section">
          <div class="permission-status">
            <span class="status-label">浏览器通知权限:</span>
            <span :class="['status-badge', permissionClass]">
              {{ permissionText }}
            </span>
          </div>

          <div class="permission-actions">
            <p v-if="!supportsNotification" class="permission-help">
              ⚠️ 当前浏览器不支持 Notification API，请使用最新的 Chrome、Edge 或 Safari。
            </p>
            <p v-else-if="!isSecureContext" class="permission-help">
              ⚠️ 需要在 HTTPS 或 http://localhost 环境下才能申请通知权限。
            </p>
            <template v-else>
              <button
                v-if="notificationPermission !== 'granted'"
                @click="handleRequestPermission"
                class="primary-btn"
                :disabled="!canRequestPermission"
              >
                {{ permissionButtonText }}
              </button>
              <p v-else class="permission-help success">✅ 已获得通知权限</p>
            </template>
          </div>

          <div
            v-if="supportsNotification && isSecureContext && notificationPermission === 'denied'"
            class="permission-help"
          >
            <p>⚠️ 通知权限已被浏览器拒绝。请按以下步骤手动开启：</p>
            <ol>
              <li>点击地址栏左侧的 🔒/ⓘ 图标</li>
              <li>找到「通知」或「Notifications」设置，选择「允许」</li>
              <li>刷新页面，再次点击上方按钮验证权限状态</li>
            </ol>
          </div>
        </div>

        <!-- 会话提醒 -->
        <div class="settings-section">
          <h4>会话提醒</h4>

          <div class="setting-item">
            <label>
              <input
                type="checkbox"
                v-model="localSettings.new_session"
                @change="handleSettingsChange"
              />
              <span>新会话提醒（声音 + 通知）</span>
            </label>
            <p class="setting-description">有新会话进入队列时提醒</p>
          </div>

          <div class="setting-item">
            <label>
              <input
                type="checkbox"
                v-model="localSettings.vip_session"
                @change="handleSettingsChange"
              />
              <span>VIP会话提醒（声音 + 通知）</span>
            </label>
            <p class="setting-description">VIP客户请求服务时提醒</p>
          </div>

          <div class="setting-item">
            <label>
              <input
                type="checkbox"
                v-model="localSettings.customer_reply"
                @change="handleSettingsChange"
              />
              <span>客户回复提醒（仅通知）</span>
            </label>
            <p class="setting-description">客户发送新消息时提醒</p>
          </div>
        </div>

        <!-- 协作提醒 -->
        <div class="settings-section">
          <h4>协作提醒</h4>

          <div class="setting-item">
            <label>
              <input
                type="checkbox"
                v-model="localSettings.mention"
                @change="handleSettingsChange"
              />
              <span>@提醒（通知 + 红点）</span>
            </label>
            <p class="setting-description">被其他坐席@时提醒</p>
          </div>

          <div class="setting-item">
            <label>
              <input
                type="checkbox"
                v-model="localSettings.assist_request"
                @change="handleSettingsChange"
              />
              <span>协助请求（通知 + 红点）</span>
            </label>
            <p class="setting-description">收到协助请求时提醒</p>
          </div>

          <div class="setting-item">
            <label>
              <input
                type="checkbox"
                v-model="localSettings.transfer_request"
                @change="handleSettingsChange"
              />
              <span>转接请求（通知 + 声音）</span>
            </label>
            <p class="setting-description">收到转接请求时提醒</p>
          </div>
        </div>

        <!-- 声音设置 -->
        <div class="settings-section">
          <h4>声音设置</h4>

          <div class="setting-item">
            <label>
              <input
                type="checkbox"
                v-model="localSettings.sound_enabled"
                @change="handleSettingsChange"
              />
              <span>启用声音提醒</span>
            </label>
          </div>

          <div v-if="localSettings.sound_enabled" class="setting-item">
            <label>
              <span>音量: {{ localSettings.sound_volume }}%</span>
            </label>
            <input
              type="range"
              min="0"
              max="100"
              v-model.number="localSettings.sound_volume"
              @change="handleSettingsChange"
              class="volume-slider"
            />
            <button @click="testSound" class="test-sound-btn">🔊 测试声音</button>
          </div>

          <div class="setting-item">
            <label>
              <input
                type="checkbox"
                v-model="localSettings.quiet_mode_enabled"
                @change="handleSettingsChange"
              />
              <span>静音模式</span>
            </label>
            <p class="setting-description">在指定时段内不播放声音</p>
          </div>

          <div v-if="localSettings.quiet_mode_enabled" class="quiet-mode-time">
            <label>
              <span>静音时段:</span>
              <input
                type="time"
                v-model="localSettings.quiet_mode_start"
                @change="handleSettingsChange"
              />
              <span>至</span>
              <input
                type="time"
                v-model="localSettings.quiet_mode_end"
                @change="handleSettingsChange"
              />
            </label>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="closeDialog" class="secondary-btn">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useNotification, type NotificationSettings } from '../composables/useNotification'

// Props
const { visible } = defineProps<{
  visible: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'close'): void
}>()

// 使用通知系统
const {
  notificationPermission,
  settings,
  requestPermission,
  updateSettings
} = useNotification()

const supportsNotification = typeof window !== 'undefined' && 'Notification' in window
const isSecureContext = typeof window !== 'undefined' ? window.isSecureContext : true

// 本地设置副本（用于编辑）
const localSettings = ref<NotificationSettings>({ ...settings.value })

// 监听 settings 变化，同步到本地副本
watch(() => settings.value, (newSettings) => {
  localSettings.value = { ...newSettings }
}, { deep: true })

// 是否可主动申请权限
const canRequestPermission = computed(() => {
  return supportsNotification &&
    isSecureContext &&
    notificationPermission.value === 'default'
})

const permissionButtonText = computed(() => {
  if (!supportsNotification) {
    return '浏览器不支持通知'
  }
  if (!isSecureContext) {
    return '仅HTTPS/localhost可用'
  }
  if (notificationPermission.value === 'denied') {
    return '❌ 权限已拒绝'
  }
  if (notificationPermission.value === 'granted') {
    return '✅ 已授权'
  }
  return '申请通知权限'
})

// 权限状态样式
const permissionClass = computed(() => {
  switch (notificationPermission.value) {
    case 'granted':
      return 'status-granted'
    case 'denied':
      return 'status-denied'
    default:
      return 'status-default'
  }
})

// 权限状态文本
const permissionText = computed(() => {
  switch (notificationPermission.value) {
    case 'granted':
      return '✅ 已授权'
    case 'denied':
      return '❌ 已拒绝'
    default:
      return '⚠️ 未授权'
  }
})

// 请求通知权限
async function handleRequestPermission() {
  if (!supportsNotification) {
    alert('当前浏览器不支持通知，请使用最新版本的 Chrome / Edge 等现代浏览器。')
    return
  }
  if (!isSecureContext) {
    alert('通知权限需要在 HTTPS 或 http://localhost 环境下申请，请切换到安全连接后重试。')
    return
  }

  const permission = await requestPermission()
  if (permission === 'granted') {
    alert('通知权限已授权！您将收到实时提醒。')
  } else if (permission === 'denied') {
    alert('浏览器已拒绝通知权限，请在地址栏左侧的站点设置中手动开启通知权限后重载页面。')
  }
}

// 设置变更处理
function handleSettingsChange() {
  updateSettings(localSettings.value)
}

// 测试声音
function testSound() {
  const audio = new Audio('/sounds/notification.mp3')
  audio.volume = localSettings.value.sound_volume / 100
  audio.play().catch(err => {
    alert('播放失败：' + err.message)
  })
}

// 关闭对话框
function closeDialog() {
  emit('close')
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-container {
  background: white;
  border-radius: 8px;
  width: 600px;
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #6b7280;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.permission-section {
  background: #f9fafb;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 24px;
}

.permission-status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.status-label {
  font-weight: 500;
  color: #374151;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.status-granted {
  background: #d1fae5;
  color: #065f46;
}

.status-denied {
  background: #fee2e2;
  color: #991b1b;
}

.status-default {
  background: #fef3c7;
  color: #92400e;
}

.permission-help {
  margin-top: 16px;
  padding: 12px;
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  border-radius: 4px;
}

.permission-help p {
  margin: 0 0 8px 0;
  font-weight: 600;
  color: #92400e;
}

.permission-help ol {
  margin: 0;
  padding-left: 20px;
  color: #78350f;
}

.permission-help li {
  margin: 4px 0;
  font-size: 14px;
}

.settings-section {
  margin-bottom: 24px;
}

.settings-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 8px;
}

.setting-item {
  margin-bottom: 16px;
}

.setting-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 500;
  color: #374151;
}

.setting-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.setting-description {
  margin: 4px 0 0 26px;
  font-size: 13px;
  color: #6b7280;
}

.volume-slider {
  width: 100%;
  margin: 8px 0;
}

.test-sound-btn {
  margin-top: 8px;
  padding: 6px 12px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.test-sound-btn:hover {
  background: #e5e7eb;
}

.quiet-mode-time {
  margin-left: 26px;
  margin-top: 8px;
}

.quiet-mode-time label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quiet-mode-time input[type="time"] {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}

.primary-btn,
.secondary-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.primary-btn {
  background: #3b82f6;
  color: white;
}

.primary-btn:hover {
  background: #2563eb;
}

.primary-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.secondary-btn {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.secondary-btn:hover {
  background: #f9fafb;
}
</style>
