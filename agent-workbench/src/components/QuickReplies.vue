<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getAccessToken } from '@/utils/authStorage'

const emit = defineEmits<{
  (e: 'select', content: string): void
}>()

// API 基础地址配置（遵循 claude.md 规范）
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 分类名称映射（后端 key -> 中文名称）
const categoryNames: Record<string, string> = {
  'greeting': '问候',
  'pre_sales': '售前',
  'after_sales': '售后',
  'logistics': '物流',
  'technical': '技术',
  'closing': '结束',
  'custom': '自定义'
}

// 分类排序（按此顺序显示）
const categoryOrder = ['greeting', 'pre_sales', 'after_sales', 'logistics', 'technical', 'closing', 'custom']

interface QuickReply {
  id: string
  title: string
  content: string
  category: string
  shortcut_key?: string
  is_shared: boolean
  usage_count: number
  variables?: string[]
  created_by: string
}

interface CategoryGroup {
  id: string
  category: string
  items: QuickReply[]
}

// 状态
const quickRepliesRaw = ref<QuickReply[]>([])
const isLoading = ref(false)
const searchKeyword = ref('')
const expandedCategory = ref<string | null>(null)

// 按分类分组
const quickReplies = computed<CategoryGroup[]>(() => {
  const grouped: Record<string, QuickReply[]> = {}

  // 分组
  quickRepliesRaw.value.forEach(reply => {
    let bucket = grouped[reply.category]
    if (!bucket) {
      bucket = []
      grouped[reply.category] = bucket
    }
    bucket.push(reply)
  })

  // 转换为数组并排序
  return categoryOrder
    .map(cat => {
      const items = grouped[cat] ? [...grouped[cat]] : []
      return {
        id: cat,
        category: categoryNames[cat] || cat,
        items
      }
    })
    .filter(group => group.items.length > 0)
})

// 过滤后的快捷短语
const filteredReplies = computed(() => {
  if (!searchKeyword.value.trim()) {
    return quickReplies.value
  }

  const keyword = searchKeyword.value.toLowerCase()
  return quickReplies.value.map(category => ({
    ...category,
    items: category.items.filter(
      item =>
        item.title.toLowerCase().includes(keyword) ||
        item.content.toLowerCase().includes(keyword)
    )
  })).filter(category => category.items.length > 0)
})

// 加载快捷回复
const loadQuickReplies = async () => {
  try {
    isLoading.value = true
    const token = getAccessToken()
    if (!token) {
      console.warn('未获取到认证信息，无法加载快捷回复')
      return
    }

    const response = await fetch(`${API_BASE}/api/quick-replies?limit=100&include_shared=true`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    const data = await response.json()
    if (data.success) {
      quickRepliesRaw.value = data.data.items
    }
  } catch (error) {
    console.error('加载快捷回复失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 切换分类展开
const toggleCategory = (categoryId: string) => {
  if (expandedCategory.value === categoryId) {
    expandedCategory.value = null
  } else {
    expandedCategory.value = categoryId
  }
}

// 选择快捷短语
const handleSelect = (content: string) => {
  emit('select', content)
}

// 初始化
onMounted(() => {
  loadQuickReplies()
})
</script>

<template>
  <div class="quick-replies">
    <div class="quick-replies-header">
      <h3>快捷短语</h3>
      <input
        v-model="searchKeyword"
        type="text"
        class="search-input"
        placeholder="搜索短语..."
      >
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- 分类列表 -->
    <div v-else class="categories">
      <div
        v-for="category in filteredReplies"
        :key="category.id"
        class="category"
      >
        <div
          class="category-header"
          @click="toggleCategory(category.id)"
        >
          <span class="category-name">{{ category.category }}</span>
          <span class="category-count">{{ category.items.length }}</span>
          <span class="expand-icon" :class="{ expanded: expandedCategory === category.id }">
            ▶
          </span>
        </div>

        <transition name="slide">
          <div
            v-if="expandedCategory === category.id"
            class="category-items"
          >
            <div
              v-for="item in category.items"
              :key="item.id"
              class="reply-item"
              @click="handleSelect(item.content)"
            >
              <div class="reply-header">
                <span class="reply-title">{{ item.title }}</span>
                <span v-if="item.is_shared" class="shared-badge">🌐</span>
              </div>
              <span class="reply-preview">{{ item.content.substring(0, 40) }}...</span>
              <div v-if="item.variables && item.variables.length > 0" class="reply-variables">
                <span class="variables-label">变量:</span>
                <span class="variable-tag" v-for="variable in item.variables" :key="variable">
                  {{ '{' + variable + '}' }}
                </span>
              </div>
              <div v-if="item.shortcut_key" class="reply-shortcut">
                快捷键: Ctrl+{{ item.shortcut_key }}
              </div>
            </div>
          </div>
        </transition>
      </div>

      <div v-if="filteredReplies.length === 0 && !isLoading" class="no-results">
        未找到匹配的短语
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-replies {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.quick-replies-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.quick-replies-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}

.search-input:focus {
  border-color: #667eea;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #9ca3af;
  font-size: 13px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.categories {
  max-height: 300px;
  overflow-y: auto;
}

.category {
  border-bottom: 1px solid #f3f4f6;
}

.category:last-child {
  border-bottom: none;
}

.category-header {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.category-header:hover {
  background: #f9fafb;
}

.category-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.category-count {
  font-size: 12px;
  color: #9ca3af;
  margin-right: 8px;
}

.expand-icon {
  font-size: 10px;
  color: #9ca3af;
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.category-items {
  padding: 4px 8px 8px;
  background: #f9fafb;
}

.reply-item {
  padding: 8px 12px;
  margin-bottom: 4px;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.reply-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
}

.reply-item:last-child {
  margin-bottom: 0;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.reply-title {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.shared-badge {
  font-size: 11px;
  opacity: 0.7;
}

.reply-preview {
  display: block;
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.reply-variables {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.variables-label {
  font-size: 11px;
  color: #9ca3af;
}

.variable-tag {
  font-size: 10px;
  padding: 2px 6px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 3px;
  font-family: monospace;
}

.reply-shortcut {
  font-size: 11px;
  color: #667eea;
  margin-top: 4px;
}

.no-results {
  padding: 20px;
  text-align: center;
  font-size: 13px;
  color: #9ca3af;
}

/* 动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 300px;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
