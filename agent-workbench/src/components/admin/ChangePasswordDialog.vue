<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const adminStore = useAdminStore()

// 表单数据
const formData = ref({
  old_password: '',
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
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
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
    old_password: '',
    new_password: '',
    confirm_password: ''
  }
  formRef.value?.resetFields()
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    await adminStore.changeOwnPassword(formData.value.old_password, formData.value.new_password)

    ElMessage.success('密码修改成功')
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
    title="修改密码"
    width="500px"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleCancel"
  >
    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      <template #title>
        为了账号安全，请定期修改密码
      </template>
    </el-alert>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="旧密码" prop="old_password">
        <el-input
          v-model="formData.old_password"
          type="password"
          placeholder="请输入当前密码"
          show-password
          clearable
        />
      </el-form-item>

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
        确定修改
      </el-button>
    </template>
  </el-dialog>
</template>
