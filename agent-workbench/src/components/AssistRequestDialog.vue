<template>
  <div v-if="visible" class="dialog-overlay" @click.self="closeDialog">
    <div class="dialog-container">
      <div class="dialog-header">
        <h3>请求协助</h3>
        <button class="close-btn" @click="closeDialog">&times;</button>
      </div>

      <div class="dialog-body">
        <div class="form-group">
          <label>协助坐席 <span class="required">*</span></label>
          <select v-model="selectedAgent" class="select-input">
            <option value="">请选择坐席</option>
            <option
              v-for="agent in availableAgents"
              :key="agent.agent_id"
              :value="agent.username"
            >
              {{ agent.name }} ({{ agent.username }}) - {{ statusLabel(agent.status) }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>请求内容 <span class="required">*</span></label>
          <textarea
            v-model="question"
            class="textarea-input"
            placeholder="请描述需要协助的问题..."
            rows="5"
          ></textarea>
          <div class="char-count">{{ question.length }}/500</div>
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="closeDialog" class="secondary-btn">取消</button>
        <button
          @click="handleSubmit"
          class="primary-btn"
          :disabled="!canSubmit || isSubmitting"
        >
          {{ isSubmitting ? '发送中...' : '发送请求' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Props
defineProps<{
  visible: boolean
  sessionName: string
  availableAgents: Array<{
    agent_id: string
    username: string
    name: string
    status: string
  }>
}>()

// Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: { assistant: string; question: string }): void
}>()

// 状态
const selectedAgent = ref('')
const question = ref('')
const isSubmitting = ref(false)

const statusMap: Record<string, string> = {
  online: '在线',
  busy: '忙碌',
  break: '小休',
  lunch: '午休',
  training: '培训',
  offline: '离线'
}

// 计算属性
const canSubmit = computed(() => {
  return selectedAgent.value && question.value.trim().length > 0 && question.value.length <= 500
})

const statusLabel = (status: string) => statusMap[status] || status

// 方法
function closeDialog() {
  selectedAgent.value = ''
  question.value = ''
  isSubmitting.value = false
  emit('close')
}

async function handleSubmit() {
  if (!canSubmit.value || isSubmitting.value) return

  isSubmitting.value = true

  try {
    emit('submit', {
      assistant: selectedAgent.value,
      question: question.value.trim()
    })
    closeDialog()
  } catch (error) {
    console.error('发送协助请求失败:', error)
    isSubmitting.value = false
  }
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
  width: 500px;
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

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.required {
  color: #ef4444;
}

.select-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #1f2937;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.select-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.textarea-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #1f2937;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
  transition: border-color 0.2s;
}

.textarea-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
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

.primary-btn:hover:not(:disabled) {
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
