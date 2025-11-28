<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import { useAgentStore } from '@/stores/agentStore'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Agent, AgentRole, AgentStatus } from '@/types'
import CreateAgentDialog from '@/components/admin/CreateAgentDialog.vue'
import EditAgentDialog from '@/components/admin/EditAgentDialog.vue'
import ResetPasswordDialog from '@/components/admin/ResetPasswordDialog.vue'
import ChangePasswordDialog from '@/components/admin/ChangePasswordDialog.vue'
import ProfileDialog from '@/components/admin/ProfileDialog.vue'

const adminStore = useAdminStore()
const agentStore = useAgentStore()
const router = useRouter()

// 搜索和筛选
const searchKeyword = ref('')
const filterRole = ref<AgentRole | ''>('')
const filterStatus = ref<AgentStatus | ''>('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 对话框状态
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showResetPasswordDialog = ref(false)
const showChangePasswordDialog = ref(false)
const showProfileDialog = ref(false)

// 当前操作的坐席
const currentAgent = ref<Agent | null>(null)

// 过滤后的坐席列表
const filteredAgents = computed(() => {
  let result = adminStore.agents

  // 搜索过滤
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(agent =>
      agent.username.toLowerCase().includes(keyword) ||
      agent.name.toLowerCase().includes(keyword) ||
      agent.id.toLowerCase().includes(keyword)
    )
  }

  // 角色过滤
  if (filterRole.value) {
    result = result.filter(agent => agent.role === filterRole.value)
  }

  // 状态过滤
  if (filterStatus.value) {
    result = result.filter(agent => agent.status === filterStatus.value)
  }

  return result
})

// 格式化时间
const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp * 1000)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 角色标签类型
const getRoleType = (role: AgentRole) => {
  return role === 'admin' ? 'danger' : 'primary'
}

// 状态标签类型
const statusTagType: Record<AgentStatus, string> = {
  online: 'success',
  busy: 'warning',
  break: 'warning',
  lunch: 'warning',
  training: 'primary',
  offline: 'info'
}

const statusLabelMap: Record<AgentStatus, string> = {
  online: '在线',
  busy: '忙碌',
  break: '小休',
  lunch: '午休',
  training: '培训',
  offline: '离线'
}

const getStatusType = (status: AgentStatus) => statusTagType[status] || 'info'
const getStatusLabel = (status: AgentStatus) => statusLabelMap[status] || status

// 加载数据
const loadData = async () => {
  try {
    await adminStore.fetchAgents({
      role: filterRole.value || undefined,
      status: filterStatus.value || undefined,
      page: currentPage.value,
      page_size: pageSize.value
    })
  } catch (error: any) {
    ElMessage.error(error.message || '加载数据失败')
  }
}

// 打开创建对话框
const handleCreate = () => {
  showCreateDialog.value = true
}

// 打开编辑对话框
const handleEdit = (agent: Agent) => {
  currentAgent.value = { ...agent }
  showEditDialog.value = true
}

// 打开重置密码对话框
const handleResetPassword = (agent: Agent) => {
  currentAgent.value = agent
  showResetPasswordDialog.value = true
}

// 删除坐席
const handleDelete = async (agent: Agent) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除坐席【${agent.name}】(${agent.username})吗？此操作不可撤销。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await adminStore.deleteAgent(agent.username)
    ElMessage.success('删除成功')
    await loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 打开修改密码对话框（坐席自己）
const handleChangePassword = () => {
  showChangePasswordDialog.value = true
}

// 打开修改资料对话框
const handleEditProfile = () => {
  showProfileDialog.value = true
}

// 返回工作台
const handleBackToDashboard = () => {
  router.push('/dashboard')
}

onMounted(async () => {
  await loadData()
})
</script>

<template>
  <div class="admin-container">
    <!-- 顶部工具栏 -->
<div class="admin-header">
  <div class="header-left">
    <el-button @click="handleBackToDashboard" link>
      ← 返回工作台
    </el-button>
    <h1 class="page-title">坐席管理</h1>
  </div>
  <div class="header-right">
    <span class="admin-name">管理员: {{ agentStore.agentName }}</span>
    <el-button size="small" @click="handleEditProfile">编辑资料</el-button>
    <el-button size="small" @click="handleChangePassword">修改密码</el-button>
  </div>
</div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleCreate">
          + 创建坐席
        </el-button>
        <el-button @click="loadData">刷新</el-button>
      </div>
      <div class="toolbar-right">
        <!-- 搜索框 -->
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名、姓名、ID..."
          clearable
          style="width: 300px; margin-right: 12px;"
        >
          <template #prefix>
            <span>🔍</span>
          </template>
        </el-input>

        <!-- 角色筛选 -->
        <el-select
          v-model="filterRole"
          placeholder="角色"
          clearable
          style="width: 120px; margin-right: 12px;"
          @change="loadData"
        >
          <el-option label="管理员" value="admin" />
          <el-option label="坐席" value="agent" />
        </el-select>

        <!-- 状态筛选 -->
        <el-select
          v-model="filterStatus"
          placeholder="状态"
          clearable
          style="width: 120px;"
          @change="loadData"
        >
          <el-option label="在线" value="online" />
          <el-option label="忙碌" value="busy" />
          <el-option label="小休" value="break" />
          <el-option label="午休" value="lunch" />
          <el-option label="培训" value="training" />
          <el-option label="离线" value="offline" />
        </el-select>
      </div>
    </div>

    <!-- 坐席列表表格 -->
    <div class="table-container">
      <el-table
        :data="filteredAgents"
        v-loading="adminStore.loading"
        stripe
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#333' }"
      >
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ row.role === 'admin' ? '管理员' : '坐席' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="max_sessions" label="最大会话数" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login ? formatTime(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" @click="handleResetPassword(row)">重置密码</el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
              :disabled="row.username === agentStore.agentId"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredAgents.length"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadData"
          @size-change="loadData"
        />
      </div>
    </div>

    <!-- 对话框组件 -->
    <CreateAgentDialog v-model="showCreateDialog" @success="loadData" />
    <EditAgentDialog v-model="showEditDialog" :agent="currentAgent" @success="loadData" />
    <ResetPasswordDialog v-model="showResetPasswordDialog" :agent="currentAgent" @success="loadData" />
    <ChangePasswordDialog v-model="showChangePasswordDialog" />
    <ProfileDialog v-model="showProfileDialog" />
  </div>
</template>

<style scoped>
.admin-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.admin-header {
  background: #2C3E50;
  padding: 12px 24px;
  border-bottom: 1px solid #34495E;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: white;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.admin-name {
  font-size: 14px;
  color: white;
  font-weight: 600;
}

.toolbar {
  padding: 14px 20px;
  background: white;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  gap: 10px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.table-container {
  flex: 1;
  padding: 16px 20px;
  overflow: auto;
  background: white;
  margin: 16px;
  border-radius: 4px;
  border: 1px solid #E5E7EB;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
