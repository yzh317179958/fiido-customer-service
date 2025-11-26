<template>
  <div class="ticket-management">
    <el-card class="header-card">
      <div class="header-content">
        <h2>工单管理</h2>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建工单
        </el-button>
      </div>
    </el-card>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable @change="loadTickets">
            <el-option label="待接单" value="pending" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="待客户" value="waiting_customer" />
            <el-option label="待配件" value="waiting_parts" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>

        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="全部优先级" clearable @change="loadTickets">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="普通" value="normal" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>

        <el-form-item label="分类">
          <el-select v-model="filters.category" placeholder="全部分类" clearable @change="loadTickets">
            <el-option label="售前配置" value="pre_sales" />
            <el-option label="订单修改" value="order_modify" />
            <el-option label="物流异常" value="shipping" />
            <el-option label="售后维修" value="after_sales" />
            <el-option label="技术故障" value="technical" />
            <el-option label="合规申诉" value="compliance" />
            <el-option label="退换货" value="returns" />
            <el-option label="保修" value="warranty" />
          </el-select>
        </el-form-item>

        <el-form-item label="部门">
          <el-select v-model="filters.department" placeholder="全部部门" clearable @change="loadTickets">
            <el-option label="欧洲售前" value="sales_eu" />
            <el-option label="深圳售后" value="service_cn" />
            <el-option label="配件仓" value="warehouse" />
            <el-option label="合规团队" value="compliance" />
            <el-option label="技术支持" value="technical" />
            <el-option label="物流团队" value="logistics" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工单列表 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tickets"
        style="width: 100%"
        @row-click="viewTicket"
        :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column prop="ticket_number" label="工单编号" width="140" />

        <el-table-column prop="title" label="标题" min-width="200" />

        <el-table-column label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            {{ getCategoryLabel(row.category) }}
          </template>
        </el-table-column>

        <el-table-column label="SLA状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getSLAType(row.sla_status)">
              {{ getSLALabel(row.sla_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="assignee_name" label="负责人" width="120">
          <template #default="{ row }">
            {{ row.assignee_name || '未分配' }}
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTickets"
          @current-change="loadTickets"
        />
      </div>
    </el-card>

    <!-- 创建工单对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建工单"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入工单标题" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入工单描述"
          />
        </el-form-item>

        <el-form-item label="分类" prop="category">
          <el-select v-model="createForm.category" placeholder="请选择分类" style="width: 100%">
            <el-option label="售前配置" value="pre_sales" />
            <el-option label="订单修改" value="order_modify" />
            <el-option label="物流异常" value="shipping" />
            <el-option label="售后维修" value="after_sales" />
            <el-option label="技术故障" value="technical" />
            <el-option label="合规申诉" value="compliance" />
            <el-option label="退换货" value="returns" />
            <el-option label="保修" value="warranty" />
          </el-select>
        </el-form-item>

        <el-form-item label="优先级" prop="priority">
          <el-select v-model="createForm.priority" placeholder="请选择优先级" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="普通" value="normal" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>

        <el-form-item label="部门" prop="department">
          <el-select v-model="createForm.department" placeholder="请选择部门" style="width: 100%">
            <el-option label="欧洲售前" value="sales_eu" />
            <el-option label="深圳售后" value="service_cn" />
            <el-option label="配件仓" value="warehouse" />
            <el-option label="合规团队" value="compliance" />
            <el-option label="技术支持" value="technical" />
            <el-option label="物流团队" value="logistics" />
          </el-select>
        </el-form-item>

        <el-form-item label="客户ID" prop="customer_id">
          <el-input v-model="createForm.customer_id" placeholder="请输入客户ID" />
        </el-form-item>

        <el-form-item label="订单ID">
          <el-input v-model="createForm.order_id" placeholder="请输入订单ID（可选）" />
        </el-form-item>

        <el-form-item label="车型">
          <el-input v-model="createForm.bike_model" placeholder="请输入车型（可选）" />
        </el-form-item>

        <el-form-item label="车辆VIN">
          <el-input v-model="createForm.vin" placeholder="请输入车辆VIN（可选）" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTicket" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAgentStore } from '@/stores/agentStore'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const agentStore = useAgentStore()

// 筛选条件
const filters = reactive({
  status: '',
  priority: '',
  category: '',
  department: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 工单列表
const tickets = ref<any[]>([])
const loading = ref(false)

// 创建工单
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref<FormInstance>()

const createForm = reactive({
  title: '',
  description: '',
  category: '',
  priority: 'normal',
  department: '',
  customer_id: '',
  order_id: '',
  bike_model: '',
  vin: ''
})

const createRules: FormRules = {
  title: [{ required: true, message: '请输入工单标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入工单描述', trigger: 'blur' }],
  category: [{ required: true, message: '请选择工单分类', trigger: 'change' }],
  department: [{ required: true, message: '请选择部门', trigger: 'change' }],
  customer_id: [{ required: true, message: '请输入客户ID', trigger: 'blur' }]
}

// 加载工单列表
const loadTickets = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: String(pagination.page),
      page_size: String(pagination.pageSize)
    })

    if (filters.status) params.append('status', filters.status)
    if (filters.priority) params.append('priority', filters.priority)
    if (filters.category) params.append('category', filters.category)
    if (filters.department) params.append('department', filters.department)

    const response = await fetch(`http://localhost:8000/api/tickets?${params}`, {
      headers: {
        'Authorization': `Bearer ${agentStore.accessToken}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to load tickets')
    }

    const data = await response.json()
    if (data.success) {
      tickets.value = data.data.items
      pagination.total = data.data.total
    }
  } catch (error) {
    console.error('加载工单列表失败:', error)
    ElMessage.error('加载工单列表失败')
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilters = () => {
  filters.status = ''
  filters.priority = ''
  filters.category = ''
  filters.department = ''
  pagination.page = 1
  loadTickets()
}

// 创建工单
const createTicket = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return

    creating.value = true
    try {
      const response = await fetch('http://localhost:8000/api/tickets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${agentStore.accessToken}`
        },
        body: JSON.stringify(createForm)
      })

      if (!response.ok) {
        throw new Error('Failed to create ticket')
      }

      const data = await response.json()
      if (data.success) {
        ElMessage.success('工单创建成功')
        showCreateDialog.value = false
        createFormRef.value?.resetFields()
        loadTickets()
      }
    } catch (error) {
      console.error('创建工单失败:', error)
      ElMessage.error('创建工单失败')
    } finally {
      creating.value = false
    }
  })
}

// 查看工单详情
const viewTicket = (row: any) => {
  router.push(`/tickets/${row.ticket_id}`)
}

// 格式化时间
const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

// 优先级相关
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

// 状态相关
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

// 分类相关
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

// SLA相关
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
  loadTickets()
})
</script>

<style scoped lang="scss">
.ticket-management {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h2 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
    }
  }
}

.filter-card {
  margin-bottom: 20px;

  .filter-form {
    margin-bottom: 0;
  }
}

.table-card {
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
