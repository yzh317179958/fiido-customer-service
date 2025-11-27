<script setup lang="ts">
import { computed } from 'vue'
import { DEFAULT_SHORTCUTS_P0 } from '@/composables/useKeyboardShortcuts'

const emit = defineEmits<{
  (e: 'close'): void
}>()

interface ShortcutItem {
  key: string
  description: string
  category: string
}

// 按类别分组快捷键
const shortcutsByCategory = computed(() => {
  const categories = {
    navigation: [] as ShortcutItem[],
    action: [] as ShortcutItem[],
    function: [] as ShortcutItem[]
  }

  Object.entries(DEFAULT_SHORTCUTS_P0).forEach(([key, config]) => {
    const category = config.category || 'function'
    categories[category].push({
      key,
      description: config.description,
      category
    })
  })

  return categories
})

const categoryNames = {
  navigation: '导航',
  action: '操作',
  function: '功能'
}

// 格式化快捷键显示
const formatKey = (key: string): string => {
  return key
    .replace('Ctrl+', 'Ctrl + ')
    .replace('Alt+', 'Alt + ')
    .replace('Shift+', 'Shift + ')
    .replace('ArrowUp', '↑')
    .replace('ArrowDown', '↓')
    .replace('ArrowLeft', '←')
    .replace('ArrowRight', '→')
}

const handleClose = () => {
  emit('close')
}

// 点击背景关闭
const handleOverlayClick = (event: MouseEvent) => {
  if (event.target === event.currentTarget) {
    handleClose()
  }
}
</script>

<template>
  <div class="shortcuts-help-overlay" @click="handleOverlayClick">
    <div class="shortcuts-help-dialog">
      <div class="dialog-header">
        <h2>快捷键帮助</h2>
        <button class="close-btn" @click="handleClose" aria-label="关闭">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="dialog-body">
        <!-- 导航类 -->
        <div class="category-section" v-if="shortcutsByCategory.navigation.length > 0">
          <h3 class="category-title">{{ categoryNames.navigation }}</h3>
          <div class="shortcuts-list">
            <div
              v-for="shortcut in shortcutsByCategory.navigation"
              :key="shortcut.key"
              class="shortcut-item"
            >
              <kbd class="shortcut-key">{{ formatKey(shortcut.key) }}</kbd>
              <span class="shortcut-description">{{ shortcut.description }}</span>
            </div>
          </div>
        </div>

        <!-- 操作类 -->
        <div class="category-section" v-if="shortcutsByCategory.action.length > 0">
          <h3 class="category-title">{{ categoryNames.action }}</h3>
          <div class="shortcuts-list">
            <div
              v-for="shortcut in shortcutsByCategory.action"
              :key="shortcut.key"
              class="shortcut-item"
            >
              <kbd class="shortcut-key">{{ formatKey(shortcut.key) }}</kbd>
              <span class="shortcut-description">{{ shortcut.description }}</span>
            </div>
          </div>
        </div>

        <!-- 功能类 -->
        <div class="category-section" v-if="shortcutsByCategory.function.length > 0">
          <h3 class="category-title">{{ categoryNames.function }}</h3>
          <div class="shortcuts-list">
            <div
              v-for="shortcut in shortcutsByCategory.function"
              :key="shortcut.key"
              class="shortcut-item"
            >
              <kbd class="shortcut-key">{{ formatKey(shortcut.key) }}</kbd>
              <span class="shortcut-description">{{ shortcut.description }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <p class="hint">按 <kbd>Esc</kbd> 或 <kbd>?</kbd> 关闭此面板</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shortcuts-help-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.shortcuts-help-dialog {
  background: white;
  border-radius: 12px;
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
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
  padding: 24px;
}

.category-section {
  margin-bottom: 24px;
}

.category-section:last-child {
  margin-bottom: 0;
}

.category-title {
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 12px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
  transition: background 0.2s;
}

.shortcut-item:hover {
  background: #f3f4f6;
}

.shortcut-key {
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 13px;
  padding: 4px 8px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  color: #374151;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  min-width: 120px;
  text-align: center;
}

.shortcut-description {
  font-size: 14px;
  color: #4b5563;
  flex: 1;
  text-align: right;
  padding-left: 16px;
}

.dialog-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 0 0 12px 12px;
}

.hint {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.hint kbd {
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 12px;
  padding: 2px 6px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  color: #374151;
}
</style>
