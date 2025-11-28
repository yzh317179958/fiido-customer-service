<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import { ElMessage } from 'element-plus'
import type { CreateAgentRequest } from '@/types'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const adminStore = useAdminStore()

// 表单数据
const formData = ref<CreateAgentRequest>({
  username: '',
  password: '',
  name: '',
  role: 'agent',
  max_sessions: 5,
  avatar_url: ''
})

// 表单验证规则
const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '至少 8 个字符', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/, message: '必须包含字母和数字', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const formRef = ref()
const loading = ref(false)

// 重置表单
const resetForm = () => {
  formData.value = {
    username: '',
    password: '',
    name: '',
    role: 'agent',
    max_sessions: 5,
    avatar_url: ''
  }
  formRef.value?.resetFields()
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    await adminStore.createAgent(formData.value)

    ElMessage.success('创建成功')
    emit('success')
    emit('update:modelValue', false)
    resetForm()
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
  resetForm()
}

// 监听对话框关闭
watch(() => props.modelValue, (val) => {
  if (!val) {
    resetForm()
  }
})
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="创建坐席"
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
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="formData.username"
          placeholder="3-20字符，字母数字下划线"
          clearable
        />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input
          v-model="formData.password"
          type="password"
          placeholder="至少8字符，含字母和数字"
          show-password
          clearable
        />
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
