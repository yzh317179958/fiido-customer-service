<template>
  <div v-if="visible" class="dialog-overlay" @click.self="closeDialog">
    <div class="dialog-container">
      <div class="dialog-header">
        <h3>个性化设置</h3>
        <button class="close-btn" @click="closeDialog">&times;</button>
      </div>

      <div class="dialog-body">
        <section class="settings-section">
          <h4>界面设置</h4>

          <div class="setting-group">
            <span class="setting-label">主题风格</span>
            <div class="options-row">
              <label v-for="option in themeOptions" :key="option.value" class="option-pill">
                <input
                  type="radio"
                  name="theme"
                  :value="option.value"
                  v-model="localSettings.appearance.theme"
                  @change="handleImmediateChange"
                />
                <span>{{ option.label }}</span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <span class="setting-label">字体大小</span>
            <div class="options-row">
              <label v-for="option in fontSizeOptions" :key="option.value" class="option-pill">
                <input
                  type="radio"
                  name="fontSize"
                  :value="option.value"
                  v-model="localSettings.appearance.fontSize"
                  @change="handleImmediateChange"
                />
                <span>{{ option.label }}</span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <span class="setting-label">会话列表密度</span>
            <div class="options-row">
              <label v-for="option in densityOptions" :key="option.value" class="option-pill">
                <input
                  type="radio"
                  name="density"
                  :value="option.value"
                  v-model="localSettings.appearance.listDensity"
                />
                <span>{{ option.label }}</span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <span class="setting-label">消息气泡样式</span>
            <div class="options-row">
              <label v-for="option in bubbleStyleOptions" :key="option.value" class="option-pill">
                <input
                  type="radio"
                  name="bubble"
                  :value="option.value"
                  v-model="localSettings.appearance.bubbleStyle"
                />
                <span>{{ option.label }}</span>
              </label>
            </div>
          </div>
        </section>

        <section class="settings-section">
          <h4>行为设置</h4>

          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">发送快捷键</span>
              <p class="setting-description">选择按键组合以发送消息</p>
            </div>
            <select v-model="localSettings.behavior.sendShortcut">
              <option value="enter">Enter 发送（Shift+Enter 换行）</option>
              <option value="ctrlenter">Ctrl + Enter 发送</option>
            </select>
          </div>

          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="localSettings.behavior.autoTakeover" />
              <span>自动接入等待中的会话</span>
            </label>
            <p class="setting-description">选中会话后自动发送接入请求</p>
          </div>

          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="localSettings.behavior.showMessagePreview" />
              <span>显示会话消息预览</span>
            </label>
            <p class="setting-description">在列表中展示最后一条消息</p>
          </div>

          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="localSettings.behavior.autoLoadHistory" />
              <span>自动加载历史消息</span>
            </label>
            <p class="setting-description">关闭后需要手动点击才能加载历史消息</p>
          </div>

          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">会话列表自动刷新</span>
              <p class="setting-description">定期刷新待接入/服务中列表</p>
            </div>
            <select v-model.number="localSettings.behavior.sessionRefreshInterval">
              <option v-for="option in refreshOptions" :key="option" :value="option">
                每 {{ option }} 秒
              </option>
            </select>
          </div>
        </section>
      </div>

      <div class="dialog-footer">
        <button class="secondary-btn" @click="closeDialog">取消</button>
        <button class="primary-btn" @click="handleSave">保存设置</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { useSettingsStore, type PersonalSettings } from '@/stores/settingsStore'
import { deepClone } from '@/utils/deepClone'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (event: 'close'): void
}>()

const settingsStore = useSettingsStore()

const localSettings = reactive<PersonalSettings>(deepClone(settingsStore.settings))

const themeOptions = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' }
]

const fontSizeOptions = [
  { value: 'small', label: '小' },
  { value: 'medium', label: '中' },
  { value: 'large', label: '大' }
]

const densityOptions = [
  { value: 'compact', label: '紧凑' },
  { value: 'standard', label: '标准' },
  { value: 'comfortable', label: '宽松' }
]

const bubbleStyleOptions = [
  { value: 'rounded', label: '圆角' },
  { value: 'flat', label: '直角' }
]

const refreshOptions: Array<10 | 30 | 60> = [10, 30, 60]

function syncSettings() {
  Object.assign(localSettings.appearance, settingsStore.settings.appearance)
  Object.assign(localSettings.behavior, settingsStore.settings.behavior)
}

function closeDialog() {
  emit('close')
}

function handleImmediateChange() {
  // 主题和字体大小需要即时生效，直接写回 store
  settingsStore.settings.appearance.theme = localSettings.appearance.theme
  settingsStore.settings.appearance.fontSize = localSettings.appearance.fontSize
}

function handleSave() {
  settingsStore.settings.appearance.listDensity = localSettings.appearance.listDensity
  settingsStore.settings.appearance.bubbleStyle = localSettings.appearance.bubbleStyle

  settingsStore.settings.behavior.sendShortcut = localSettings.behavior.sendShortcut
  settingsStore.settings.behavior.autoTakeover = localSettings.behavior.autoTakeover
  settingsStore.settings.behavior.showMessagePreview = localSettings.behavior.showMessagePreview
  settingsStore.settings.behavior.autoLoadHistory = localSettings.behavior.autoLoadHistory
  settingsStore.settings.behavior.sessionRefreshInterval = localSettings.behavior.sessionRefreshInterval

  emit('close')
}

watch(() => props.visible, (visible) => {
  if (visible) {
    syncSettings()
  }
})
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.dialog-container {
  width: min(720px, 90vw);
  max-height: 90vh;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

[data-agent-theme='dark'] .dialog-container {
  background: #0f172a;
  color: #f1f5f9;
}

.dialog-header {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

[data-agent-theme='dark'] .dialog-header {
  border-color: rgba(148, 163, 184, 0.3);
}

.dialog-body {
  padding: 24px 28px 12px;
  overflow-y: auto;
  gap: 24px;
  display: flex;
  flex-direction: column;
}

.dialog-footer {
  padding: 18px 28px;
  border-top: 1px solid rgba(226, 232, 240, 0.6);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

[data-agent-theme='dark'] .dialog-footer {
  border-color: rgba(148, 163, 184, 0.3);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: inherit;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.settings-section {
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 14px;
  padding: 16px 20px;
  background: rgba(248, 250, 252, 0.85);
}

[data-agent-theme='dark'] .settings-section {
  background: rgba(15, 23, 42, 0.6);
  border-color: rgba(59, 130, 246, 0.2);
}

.settings-section + .settings-section {
  margin-top: 16px;
}

.settings-section h4 {
  margin-bottom: 14px;
  font-size: 16px;
}

.setting-group {
  margin-bottom: 18px;
}

.setting-group:last-child {
  margin-bottom: 0;
}

.setting-label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
}

.options-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.7);
  cursor: pointer;
  font-size: 13px;
}

.option-pill input {
  margin: 0;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-info {
  flex: 1;
}

.setting-description {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}

[data-agent-theme='dark'] .setting-description {
  color: #94a3b8;
}

select {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.7);
  background: transparent;
  font-size: 13px;
}

button {
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
}

.secondary-btn {
  background: rgba(148, 163, 184, 0.2);
  color: inherit;
}
</style>
