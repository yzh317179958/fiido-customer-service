<template>
  <div class="ticket-detail">
    <el-card v-loading="loading" class="ticket-card">
      <!-- 返回按钮 -->
      <el-button @click="$router.back()" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>

      <div v-if="ticket" class="ticket-content">
        <!-- 工单头部 -->
        <div class="ticket-header">
          <div class="ticket-title-row">
            <h2>{{ ticket.ticket_number }}</h2>
            <div class="ticket-tags">
              <el-tag :type="getPriorityType(ticket.priority)">
                {{ getPriorityLabel(ticket.priority) }}
              </el-tag>
              <el-tag :type="getStatusType(ticket.status)">
                {{ getStatusLabel(ticket.status) }}
              </el-tag>
              <el-tag :type="getSLAType(ticket.sla_status)">
                {{ getSLALabel(ticket.sla_status) }}
              </el-tag>
            </div>
          </div>

          <h3>{{ ticket.title }}</h3>

          <div class="ticket-meta">
            <div class="meta-item">
              <span class="label">分类:</span>
              <span>{{ getCategoryLabel(ticket.category) }}</span>
            </div>
            <div class="meta-item">
              <span class="label">部门:</span>
              <span>{{ getDepartmentLabel(ticket.department) }}</span>
            </div>
            <div class="meta-item">
              <span class="label">负责人:</span>
              <span>{{ ticket.assignee_name || '未分配' }}</span>
            </div>
            <div class="meta-item">
              <span class="label">创建人:</span>
              <span>{{ ticket.created_by_name }}</span>
            </div>
            <div class="meta-item">
              <span class="label">创建时间:</span>
              <span>{{ formatTime(ticket.created_at) }}</span>
            </div>
            <div class="meta-item" v-if="ticket.sla_deadline">
              <span class="label">SLA截止:</span>
              <span>{{ formatTime(ticket.sla_deadline) }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="ticket-actions">
          <el-button type="primary" @click="showAssignDialog = true">指派工单</el-button>
          <el-button type="success" @click="showStatusDialog = true">更新状态</el-button>
          <el-button @click="showEditDialog = true">编辑工单</el-button>
        </div>

        <!-- 工单描述 -->
        <el-card class="description-card">
          <template #header>
            <div class="card-header">
              <span>工单描述</span>
            </div>
          </template>
          <div class="description-content">{{ ticket.description }}</div>
        </el-card>

        <!-- 客户信息 -->
        <el-card v-if="ticket.customer_id" class="customer-card">
          <template #header>
            <div class="card-header">
              <span>客户信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="客户ID">{{ ticket.customer_id }}</el-descriptions-item>
            <el-descriptions-item label="订单ID">{{ ticket.order_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="车型">{{ ticket.bike_model || '-' }}</el-descriptions-item>
            <el-descriptions-item label="车辆VIN">{{ ticket.vin || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- AI摘要 -->
        <el-card v-if="ticket.ai_summary" class="ai-card">
          <template #header>
            <div class="card-header">
              <span>AI摘要</span>
            </div>
          </template>
          <div class="ai-content">{{ ticket.ai_summary }}</div>
        </el-card>

        <!-- 评论区 -->
        <el-card class="comments-card">
          <template #header>
            <div class="card-header">
              <span>评论 ({{ ticket.comments.length }})</span>
            </div>
          </template>

          <!-- 添加评论 -->
          <div class="add-comment">
            <el-input
              v-model="newComment"
              type="textarea"
              :rows="3"
              placeholder="添加评论..."
            />
            <div class="comment-actions">
              <el-checkbox v-model="commentInternal">内部评论（客户不可见）</el-checkbox>
              <el-button type="primary" @click="addComment" :loading="commenting">发表评论</el-button>
            </div>
          </div>

          <!-- 评论列表 -->
          <div class="comments-list">
            <div
              v-for="comment in ticket.comments"
              :key="comment.id"
              class="comment-item"
              :class="{ internal: comment.is_internal }"
            >
              <div class="comment-header">
                <span class="comment-author">{{ comment.author_name }}</span>
                <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
                <el-tag v-if="comment.is_internal" size="small" type="warning">内部</el-tag>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
            </div>
          </div>
        </el-card>

        <!-- 活动日志 -->
        <el-card class="activity-card">
          <template #header>
            <div class="card-header">
              <span>活动日志 ({{ ticket.activity_log.length }})</span>
            </div>
          </template>

          <el-timeline>
            <el-timeline-item
              v-for="activity in ticket.activity_log"
              :key="activity.id"
              :timestamp="formatTime(activity.timestamp)"
              placement="top"
            >
              <div class="activity-item">
                <strong>{{ activity.operator_name }}</strong>
                {{ activity.description }}
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </div>
    </el-card>

    <!-- 指派对话框 -->
    <el-dialog v-model="showAssignDialog" title="指派工单" width="500px">
      <el-form :model="assignForm" label-width="100px">
        <el-form-item label="负责人ID">
          <el-input v-model="assignForm.assignee_id" placeholder="请输入负责人ID" />
        </el-form-item>
        <el-form-item label="负责人姓名">
          <el-input v-model="assignForm.assignee_name" placeholder="请输入负责人姓名" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="assignForm.department" placeholder="请选择部门" style="width: 100%">
            <el-option label="欧洲售前" value="sales_eu" />
            <el-option label="深圳售后" value="service_cn" />
            <el-option label="配件仓" value="warehouse" />
            <el-option label="合规团队" value="compliance" />
            <el-option label="技术支持" value="technical" />
            <el-option label="物流团队" value="logistics" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="assignTicket" :loading="assigning">确定</el-button>
      </template>
    </el-dialog>

    <!-- 更新状态对话框 -->
    <el-dialog v-model="showStatusDialog" title="更新工单状态" width="500px">
      <el-form :model="statusForm" label-width="100px">
        <el-form-item label="新状态">
          <el-select v-model="statusForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="待接单" value="pending" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="待客户" value="waiting_customer" />
            <el-option label="待配件" value="waiting_parts" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="statusForm.comment"
            type="textarea"
            :rows="3"
            placeholder="请输入状态变更备注（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStatusDialog = false">取消</el-button>
        <el-button type="primary" @click="updateStatus" :loading="updating">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑工单" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" placeholder="请输入工单标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入工单描述"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="editForm.priority" placeholder="请选择优先级" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="普通" value="normal" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateTicket" :loading="editing">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useAgentStore } from '@/stores/agentStore'

const route = useRoute()
const router = useRouter()
const agentStore = useAgentStore()

const ticketId = route.params.id as string

const ticket = ref<any>(null)
const loading = ref(false)

// 评论相关
const newComment = ref('')
const commentInternal = ref(false)
const commenting = ref(false)

// 指派对话框
const showAssignDialog = ref(false)
const assigning = ref(false)
const assignForm = reactive({
  assignee_id: '',
  assignee_name: '',
  department: ''
})

// 状态更新对话框
const showStatusDialog = ref(false)
const updating = ref(false)
const statusForm = reactive({
  status: '',
  comment: ''
})

// 编辑对话框
const showEditDialog = ref(false)
const editing = ref(false)
const editForm = reactive({
  title: '',
  description: '',
  priority: ''
})

// 加载工单详情
const loadTicket = async () => {
  loading.value = true
  try {
    const response = await fetch(`http://localhost:8000/api/tickets/${ticketId}`, {
      headers: {
        'Authorization': `Bearer ${agentStore.accessToken}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to load ticket')
    }

    const data = await response.json()
    if (data.success) {
      ticket.value = data.data
      // 初始化编辑表单
      editForm.title = data.data.title
      editForm.description = data.data.description
      editForm.priority = data.data.priority
    }
  } catch (error) {
    console.error('加载工单详情失败:', error)
    ElMessage.error('加载工单详情失败')
  } finally {
    loading.value = false
  }
}

// 添加评论
const addComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }

  commenting.value = true
  try {
    const response = await fetch(`http://localhost:8000/api/tickets/${ticketId}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${agentStore.accessToken}`
      },
      body: JSON.stringify({
        content: newComment.value,
        is_internal: commentInternal.value,
        mentions: []
      })
    })

    if (!response.ok) {
      throw new Error('Failed to add comment')
    }

    const data = await response.json()
    if (data.success) {
      ElMessage.success('评论发表成功')
      newComment.value = ''
      commentInternal.value = false
      loadTicket()
    }
  } catch (error) {
    console.error('发表评论失败:', error)
    ElMessage.error('发表评论失败')
  } finally {
    commenting.value = false
  }
}

// 指派工单
const assignTicket = async () => {
  if (!assignForm.assignee_id || !assignForm.assignee_name || !assignForm.department) {
    ElMessage.warning('请填写完整的指派信息')
    return
  }

  assigning.value = true
  try {
    const response = await fetch(`http://localhost:8000/api/tickets/${ticketId}/assign`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${agentStore.accessToken}`
      },
      body: JSON.stringify(assignForm)
    })

    if (!response.ok) {
      throw new Error('Failed to assign ticket')
    }

    const data = await response.json()
    if (data.success) {
      ElMessage.success('工单指派成功')
      showAssignDialog.value = false
      loadTicket()
    }
  } catch (error) {
    console.error('指派工单失败:', error)
    ElMessage.error('指派工单失败')
  } finally {
    assigning.value = false
  }
}

// 更新状态
const updateStatus = async () => {
  if (!statusForm.status) {
    ElMessage.warning('请选择新状态')
    return
  }

  updating.value = true
  try {
    const response = await fetch(`http://localhost:8000/api/tickets/${ticketId}/status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${agentStore.accessToken}`
      },
      body: JSON.stringify(statusForm)
    })

    if (!response.ok) {
      throw new Error('Failed to update status')
    }

    const data = await response.json()
    if (data.success) {
      ElMessage.success('状态更新成功')
      showStatusDialog.value = false
      loadTicket()
    }
  } catch (error) {
    console.error('更新状态失败:', error)
    ElMessage.error('更新状态失败')
  } finally {
    updating.value = false
  }
}

// 更新工单
const updateTicket = async () => {
  editing.value = true
  try {
    const response = await fetch(`http://localhost:8000/api/tickets/${ticketId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${agentStore.accessToken}`
      },
      body: JSON.stringify(editForm)
    })

    if (!response.ok) {
      throw new Error('Failed to update ticket')
    }

    const data = await response.json()
    if (data.success) {
      ElMessage.success('工单更新成功')
      showEditDialog.value = false
      loadTicket()
    }
  } catch (error) {
    console.error('更新工单失败:', error)
    ElMessage.error('更新工单失败')
  } finally {
    editing.value = false
  }
}

// 辅助函数
const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

const getPriorityType = (priority: string) => {
  const types: Record<string, any> = {
    urgent: 'danger',
    high: 'warning',
    normal: '',
    low: 'info'
  }
  return types[priority] || ''
}

const getPriorityLabel = (priority: string) => {
  const labels: Record<string, string> = {
    urgent: '紧急',
    high: '高',
    normal: '普通',
    low: '低'
  }
  return labels[priority] || priority
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'warning',
    in_progress: 'primary',
    waiting_customer: 'info',
    waiting_parts: 'info',
    resolved: 'success',
    closed: 'info'
  }
  return types[status] || ''
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '待接单',
    in_progress: '处理中',
    waiting_customer: '待客户',
    waiting_parts: '待配件',
    resolved: '已解决',
    closed: '已关闭'
  }
  return labels[status] || status
}

const getCategoryLabel = (category: string) => {
  const labels: Record<string, string> = {
    pre_sales: '售前配置',
    order_modify: '订单修改',
    shipping: '物流异常',
    after_sales: '售后维修',
    technical: '技术故障',
    compliance: '合规申诉',
    returns: '退换货',
    warranty: '保修'
  }
  return labels[category] || category
}

const getDepartmentLabel = (department: string) => {
  const labels: Record<string, string> = {
    sales_eu: '欧洲售前',
    service_cn: '深圳售后',
    warehouse: '配件仓',
    compliance: '合规团队',
    technical: '技术支持',
    logistics: '物流团队'
  }
  return labels[department] || department
}

const getSLAType = (slaStatus: string) => {
  const types: Record<string, any> = {
    within: 'success',
    warning: 'warning',
    breached: 'danger'
  }
  return types[slaStatus] || ''
}

const getSLALabel = (slaStatus: string) => {
  const labels: Record<string, string> = {
    within: '正常',
    warning: '即将超时',
    breached: '已超时'
  }
  return labels[slaStatus] || slaStatus
}

onMounted(() => {
  loadTicket()
})
</script>

<style scoped lang="scss">
.ticket-detail {
  padding: 20px;
}

.back-btn {
  margin-bottom: 20px;
}

.ticket-content {
  .ticket-header {
    margin-bottom: 20px;

    .ticket-title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;

      h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
      }

      .ticket-tags {
        display: flex;
        gap: 8px;
      }
    }

    h3 {
      margin: 0 0 15px 0;
      font-size: 20px;
      font-weight: 500;
    }

    .ticket-meta {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 10px;

      .meta-item {
        .label {
          font-weight: 600;
          margin-right: 8px;
          color: #606266;
        }
      }
    }
  }

  .ticket-actions {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
  }

  .description-card,
  .customer-card,
  .ai-card,
  .comments-card,
  .activity-card {
    margin-bottom: 20px;

    .card-header {
      font-weight: 600;
      font-size: 16px;
    }
  }

  .description-content,
  .ai-content {
    white-space: pre-wrap;
    line-height: 1.6;
  }

  .add-comment {
    margin-bottom: 20px;

    .comment-actions {
      margin-top: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }

  .comments-list {
    .comment-item {
      padding: 15px;
      border: 1px solid #e4e7ed;
      border-radius: 4px;
      margin-bottom: 10px;

      &.internal {
        background-color: #fdf6ec;
      }

      .comment-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;

        .comment-author {
          font-weight: 600;
        }

        .comment-time {
          font-size: 12px;
          color: #909399;
        }
      }

      .comment-content {
        line-height: 1.6;
      }
    }
  }

  .activity-item {
    line-height: 1.6;
  }
}
</style>
