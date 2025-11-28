<template>
  <div class="quick-reply-management">
    <div class="header">
      <h2>快捷回复管理</h2>
      <button class="btn-primary" @click="showCreateDialog">
        <span class="icon">➕</span>
        新建快捷回复
      </button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <label>分类:</label>
        <select v-model="filters.category" @change="loadQuickReplies">
          <option value="">全部</option>
          <option v-for="(cat, key) in categories" :key="key" :value="key">
            {{ cat.name }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label>搜索:</label>
        <input
          v-model="filters.keyword"
          @input="debounceSearch"
          placeholder="搜索标题或内容..."
          type="text"
        />
      </div>

      <div class="filter-group">
        <label>
          <input type="checkbox" v-model="filters.onlyMine" @change="loadQuickReplies" />
          只看我的
        </label>
      </div>
    </div>

    <!-- 快捷回复列表 -->
    <div class="reply-list" v-if="quickReplies.length > 0">
      <div
        v-for="reply in quickReplies"
        :key="reply.id"
        class="reply-card"
        :class="{ shared: reply.is_shared }"
      >
        <div class="reply-header">
          <div class="reply-title">
            <span class="category-badge" :class="`category-${reply.category}`">
              {{ getCategoryName(reply.category) }}
            </span>
            <h3>{{ reply.title }}</h3>
            <span v-if="reply.is_shared" class="shared-badge">🌐 团队共享</span>
          </div>
          <div class="reply-actions">
            <button class="btn-icon" @click="useReply(reply)" title="使用">
              ▶️
            </button>
            <button class="btn-icon" @click="editReply(reply)" title="编辑">
              ✏️
            </button>
            <button
              class="btn-icon btn-danger"
              @click="deleteReply(reply)"
              :disabled="!canModify(reply)"
              title="删除"
            >
              🗑️
            </button>
          </div>
        </div>

        <div class="reply-content">
          {{ reply.content }}
        </div>

        <div class="reply-meta">
          <span v-if="reply.shortcut_key" class="shortcut-hint">
            快捷键: Ctrl+{{ reply.shortcut_key }}
          </span>
          <span class="usage-count">
            使用 {{ reply.usage_count }} 次
          </span>
          <span class="variables" v-if="reply.variables && reply.variables.length > 0">
            变量: {{ reply.variables.join(', ') }}
          </span>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>暂无快捷回复</p>
      <button class="btn-primary" @click="showCreateDialog">
        创建第一个快捷回复
      </button>
    </div>

    <!-- 创建/编辑对话框 -->
    <div v-if="showDialog" class="dialog-overlay" @click.self="closeDialog">
      <div class="dialog">
        <div class="dialog-header">
          <h3>{{ editingReply ? '编辑快捷回复' : '新建快捷回复' }}</h3>
          <button class="btn-close" @click="closeDialog">×</button>
        </div>

        <div class="dialog-body">
          <div class="form-group">
            <label>标题 *</label>
            <input
              v-model="formData.title"
              placeholder="例如: 欢迎语"
              maxlength="50"
            />
          </div>

          <div class="form-group">
            <label>内容 *</label>
            <textarea
              v-model="formData.content"
              placeholder="支持变量: {customer_name}, {agent_name}, {order_id} 等"
              rows="4"
              maxlength="500"
            ></textarea>
            <div class="char-count">{{ formData.content.length }}/500</div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>分类 *</label>
              <select v-model="formData.category">
                <option v-for="(cat, key) in categories" :key="key" :value="key">
                  {{ cat.name }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>快捷键</label>
              <input
                v-model="formData.shortcut_key"
                placeholder="1-9"
                maxlength="1"
              />
            </div>
          </div>

          <div class="form-group">
            <label>
              <input type="checkbox" v-model="formData.is_shared" />
              团队共享 (其他坐席可见)
            </label>
          </div>

          <div class="variable-hint" v-if="extractedVariables.length > 0">
            <strong>检测到变量:</strong> {{ extractedVariables.join(', ') }}
          </div>
        </div>

        <div class="dialog-footer">
          <button class="btn-secondary" @click="closeDialog">取消</button>
          <button
            class="btn-primary"
            @click="saveReply"
            :disabled="!formData.title || !formData.content"
          >
            {{ editingReply ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 使用对话框 -->
    <div v-if="showUseDialog" class="dialog-overlay" @click.self="closeUseDialog">
      <div class="dialog">
        <div class="dialog-header">
          <h3>使用快捷回复: {{ usingReply?.title }}</h3>
          <button class="btn-close" @click="closeUseDialog">×</button>
        </div>

        <div class="dialog-body">
          <div class="preview-section">
            <h4>原始内容:</h4>
            <div class="preview-content">{{ usingReply?.content }}</div>
          </div>

          <div class="preview-section" v-if="replacedContent">
            <h4>替换后:</h4>
            <div class="preview-content replaced">{{ replacedContent }}</div>
          </div>

          <div class="form-group" v-if="needsVariableInput">
            <label>请提供变量值:</label>
            <div v-for="variable in usingReply?.variables" :key="variable" class="variable-input">
              <label>{{ variable }}:</label>
              <input v-model="variableValues[variable]" @input="updatePreview" />
            </div>
          </div>
        </div>

        <div class="dialog-footer">
          <button class="btn-secondary" @click="closeUseDialog">取消</button>
          <button class="btn-primary" @click="copyToClipboard">
            复制内容
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentStore } from '../stores/agentStore'
import { getAccessToken } from '@/utils/authStorage'

const authStore = useAgentStore()
const router = useRouter()

const requireToken = () => {
  const token = getAccessToken()
  if (!token) {
    alert('认证信息已失效，请重新登录')
    router.push('/login')
    return null
  }
  return token
}

// API 基础地址配置（遵循 claude.md 规范）
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 状态
const quickReplies = ref([])
const categories = ref({})
const supportedVariables = ref({})
const filters = ref({
  category: '',
  keyword: '',
  onlyMine: false
})

const showDialog = ref(false)
const editingReply = ref(null)
const formData = ref({
  title: '',
  content: '',
  category: 'greeting',
  shortcut_key: '',
  is_shared: false
})

const showUseDialog = ref(false)
const usingReply = ref(null)
const variableValues = ref({})
const replacedContent = ref('')

// 搜索防抖
let searchTimeout = null
const debounceSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadQuickReplies()
  }, 500)
}

// 提取变量
const extractedVariables = computed(() => {
  const pattern = /\{(\w+)\}/g
  const matches = formData.value.content.matchAll(pattern)
  return [...new Set([...matches].map(m => m[1]))]
})

// 是否需要输入变量
const needsVariableInput = computed(() => {
  return usingReply.value?.variables && usingReply.value.variables.length > 0
})

// 权限检查
const canModify = (reply) => {
  if (authStore.agentRole === 'admin') return true
  return reply.created_by === authStore.agentId
}

// 获取分类名称
const getCategoryName = (key) => {
  return categories.value[key]?.name || key
}

// 加载分类
const loadCategories = async () => {
  try {
    const token = requireToken()
    if (!token) return
    const response = await fetch(`${API_BASE}/api/quick-replies/categories`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (data.success) {
      categories.value = data.data.categories
      supportedVariables.value = data.data.supported_variables
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

// 加载快捷回复列表
const loadQuickReplies = async () => {
  try {
    const params = new URLSearchParams()
    params.append('limit', '100')

    if (filters.value.category) {
      params.append('category', filters.value.category)
    }

    if (filters.value.keyword) {
      params.append('keyword', filters.value.keyword)
    }

    if (filters.value.onlyMine) {
      params.append('agent_id', authStore.agentId)
      params.append('include_shared', 'false')
    }

    const token = requireToken()
    if (!token) return
    const response = await fetch(`${API_BASE}/api/quick-replies?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    const data = await response.json()
    if (data.success) {
      quickReplies.value = data.data.items
    }
  } catch (error) {
    console.error('加载快捷回复失败:', error)
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  editingReply.value = null
  formData.value = {
    title: '',
    content: '',
    category: 'greeting',
    shortcut_key: '',
    is_shared: false
  }
  showDialog.value = true
}

// 编辑快捷回复
const editReply = (reply) => {
  if (!canModify(reply)) {
    alert('只有创建者或管理员可以修改')
    return
  }

  editingReply.value = reply
  formData.value = {
    title: reply.title,
    content: reply.content,
    category: reply.category,
    shortcut_key: reply.shortcut_key || '',
    is_shared: reply.is_shared
  }
  showDialog.value = true
}

// 保存快捷回复
const saveReply = async () => {
  try {
    const url = editingReply.value
      ? `${API_BASE}/api/quick-replies/${editingReply.value.id}`
      : `${API_BASE}/api/quick-replies`

    const method = editingReply.value ? 'PUT' : 'POST'
    const token = requireToken()
    if (!token) return

    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: formData.value.title,
        content: formData.value.content,
        category: formData.value.category,
        shortcut_key: formData.value.shortcut_key || null,
        is_shared: formData.value.is_shared
      })
    })

    const data = await response.json()
    if (data.success) {
      closeDialog()
      loadQuickReplies()
    } else {
      alert('保存失败: ' + data.detail)
    }
  } catch (error) {
    console.error('保存失败:', error)
    alert('保存失败')
  }
}

// 删除快捷回复
const deleteReply = async (reply) => {
  if (!canModify(reply)) {
    alert('只有创建者或管理员可以删除')
    return
  }

  if (!confirm(`确定要删除快捷回复"${reply.title}"吗?`)) {
    return
  }

  try {
    const token = requireToken()
    if (!token) return
    const response = await fetch(`${API_BASE}/api/quick-replies/${reply.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    const data = await response.json()
    if (data.success) {
      loadQuickReplies()
    } else {
      alert('删除失败: ' + data.detail)
    }
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败')
  }
}

// 使用快捷回复
const useReply = async (reply) => {
  usingReply.value = reply
  variableValues.value = {}

  // 如果有变量,显示输入对话框
  if (reply.variables && reply.variables.length > 0) {
    showUseDialog.value = true
    updatePreview()
  } else {
    // 直接复制
    replacedContent.value = reply.content
    showUseDialog.value = true
  }
}

// 更新预览
const updatePreview = () => {
  let content = usingReply.value.content

  // 替换变量
  for (const [key, value] of Object.entries(variableValues.value)) {
    if (value) {
      content = content.replace(new RegExp(`\\{${key}\\}`, 'g'), value)
    }
  }

  replacedContent.value = content
}

// 复制到剪贴板
const copyToClipboard = () => {
  const textToCopy = replacedContent.value || usingReply.value.content

  navigator.clipboard.writeText(textToCopy).then(() => {
    alert('已复制到剪贴板')
    closeUseDialog()
  }).catch(err => {
    console.error('复制失败:', err)
    alert('复制失败')
  })
}

// 关闭对话框
const closeDialog = () => {
  showDialog.value = false
  editingReply.value = null
}

const closeUseDialog = () => {
  showUseDialog.value = false
  usingReply.value = null
  variableValues.value = {}
  replacedContent.value = ''
}

// 初始化
onMounted(() => {
  loadCategories()
  loadQuickReplies()
})
</script>

<style scoped>
.quick-reply-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.filter-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-weight: 500;
  color: #666;
}

.filter-group select,
.filter-group input[type="text"] {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.filter-group input[type="text"] {
  width: 200px;
}

.reply-list {
  display: grid;
  gap: 15px;
}

.reply-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  transition: box-shadow 0.2s;
}

.reply-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.reply-card.shared {
  border-left: 3px solid #4CAF50;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.reply-title {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.reply-title h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.category-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.category-greeting { background: #2196F3; }
.category-pre_sales { background: #4CAF50; }
.category-after_sales { background: #FF9800; }
.category-logistics { background: #9C27B0; }
.category-technical { background: #F44336; }
.category-closing { background: #607D8B; }
.category-custom { background: #795548; }

.shared-badge {
  font-size: 12px;
  color: #4CAF50;
}

.reply-actions {
  display: flex;
  gap: 5px;
}

.btn-icon {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-icon:hover {
  background: #f0f0f0;
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger:hover:not(:disabled) {
  background: #ffebee;
}

.reply-content {
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 10px;
  font-size: 14px;
  line-height: 1.5;
  color: #555;
  white-space: pre-wrap;
}

.reply-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #999;
}

.shortcut-hint {
  color: #2196F3;
  font-weight: 500;
}

.variables {
  color: #FF9800;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: auto;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
  line-height: 1;
  padding: 0;
  width: 30px;
  height: 30px;
}

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.variable-hint {
  padding: 10px;
  background: #e3f2fd;
  border-radius: 4px;
  font-size: 13px;
  color: #1976d2;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.btn-primary,
.btn-secondary {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary {
  background: #2196F3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1976D2;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.icon {
  margin-right: 5px;
}

.preview-section {
  margin-bottom: 15px;
}

.preview-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
}

.preview-content {
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.preview-content.replaced {
  background: #e8f5e9;
  color: #2e7d32;
}

.variable-input {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.variable-input label {
  min-width: 120px;
  font-weight: normal;
}
</style>
