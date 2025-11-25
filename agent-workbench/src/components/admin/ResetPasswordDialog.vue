<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import { ElMessage } from 'element-plus'
import type { Agent } from '@/types'

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
const formData = ref({
  new_password: '',
  confirm_password: ''
})

// 自定义验证：确认密码一致
const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== formData.value.new_password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const formRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '至少 8 个字符', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/, message: '必须包含字母和数字', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const formRef = ref()
const loading = ref(false)

// 重置表单
const resetForm = () => {
  formData.value = {
    new_password: '',
    confirm_password: ''
  }
  formRef.value?.resetFields()
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

    await adminStore.resetPassword(props.agent.username, formData.value.new_password)

    ElMessage.success('密码重置成功')
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
    title="重置密码"
    width="500px"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleCancel"
  >
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      <template #title>
        正在为坐席【{{ agent?.name }}】({{ agent?.username }})重置密码
      </template>
    </el-alert>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="新密码" prop="new_password">
        <el-input
          v-model="formData.new_password"
          type="password"
          placeholder="至少8字符，含字母和数字"
          show-password
          clearable
        />
      </el-form-item>

      <el-form-item label="确认密码" prop="confirm_password">
        <el-input
          v-model="formData.confirm_password"
          type="password"
          placeholder="再次输入新密码"
          show-password
          clearable
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确定重置
      </el-button>
    </template>
  </el-dialog>
</template>
