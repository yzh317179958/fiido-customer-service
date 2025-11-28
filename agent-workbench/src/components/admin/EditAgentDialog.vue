<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import { ElMessage } from 'element-plus'
import type { Agent, UpdateAgentRequest } from '@/types'

const props = defineProps<{
  modelValue: boolean
  agent: Agent | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const adminStore = useAdminStore()

// 表单数据
const formData = ref<UpdateAgentRequest>({
  name: '',
  role: 'agent',
  status: 'offline',
  max_sessions: 5,
  avatar_url: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const formRef = ref()
const loading = ref(false)

// 重置表单
const resetForm = () => {
  if (props.agent) {
    formData.value = {
      name: props.agent.name,
      role: props.agent.role,
      status: props.agent.status,
      max_sessions: props.agent.max_sessions,
      avatar_url: props.agent.avatar_url || ''
    }
  }
  formRef.value?.clearValidate()
}

// 提交表单
const handleSubmit = async () => {
  if (!props.agent) {
    ElMessage.error('坐席信息不存在')
    return
  }

  try {
    await formRef.value?.validate()
    loading.value = true

    await adminStore.updateAgent(props.agent.username, formData.value)

    ElMessage.success('修改成功')
    emit('success')
    emit('update:modelValue', false)
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:modelValue', false)
}

// 监听对话框打开，初始化表单
watch(() => props.modelValue, (val) => {
  if (val && props.agent) {
    resetForm()
  }
})

// 监听 agent 变化
watch(() => props.agent, (newAgent) => {
  if (newAgent && props.modelValue) {
    resetForm()
  }
})
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="编辑坐席"
    width="500px"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleCancel"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="用户名">
        <el-input :value="agent?.username" disabled />
      </el-form-item>

      <el-form-item label="姓名" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="1-50字符"
          clearable
        />
      </el-form-item>

      <el-form-item label="角色" prop="role">
        <el-select v-model="formData.role" style="width: 100%">
          <el-option label="管理员" value="admin" />
          <el-option label="坐席" value="agent" />
        </el-select>
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-select v-model="formData.status" style="width: 100%">
          <el-option label="在线" value="online" />
          <el-option label="忙碌" value="busy" />
          <el-option label="小休" value="break" />
          <el-option label="午休" value="lunch" />
          <el-option label="培训" value="training" />
          <el-option label="离线" value="offline" />
        </el-select>
      </el-form-item>

      <el-form-item label="最大会话数">
        <el-input-number
          v-model="formData.max_sessions"
          :min="1"
          :max="100"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="头像URL">
        <el-input
          v-model="formData.avatar_url"
          placeholder="可选"
          clearable
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>
