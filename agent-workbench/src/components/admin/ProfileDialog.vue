<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import { useAgentStore } from '@/stores/agentStore'
import { ElMessage } from 'element-plus'
import { getAgentInfo, setAgentInfo } from '@/utils/authStorage'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const adminStore = useAdminStore()
const agentStore = useAgentStore()

// 表单数据
const formData = ref({
  name: '',
  avatar_url: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

const formRef = ref()
const loading = ref(false)

// 初始化表单
const initForm = () => {
  formData.value = {
    name: agentStore.agentName,
    avatar_url: ''  // 后续可从用户信息中获取
  }
}

// 重置表单
const resetForm = () => {
  initForm()
  formRef.value?.clearValidate()
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    // 只提交修改的字段
    const updateData: any = {}
    if (formData.value.name && formData.value.name !== agentStore.agentName) {
      updateData.name = formData.value.name
    }
    if (formData.value.avatar_url) {
      updateData.avatar_url = formData.value.avatar_url
    }

    // 检查是否有修改
    if (Object.keys(updateData).length === 0) {
      ElMessage.warning('没有修改任何内容')
      return
    }

    const updatedAgent = await adminStore.updateProfile(updateData)

    // 更新本地存储的姓名
    if (updatedAgent && updatedAgent.name) {
      agentStore.agentName = updatedAgent.name
      const saved = getAgentInfo()
      if (saved) {
        setAgentInfo({
          ...saved,
          agentName: updatedAgent.name
        })
      }
    }

    ElMessage.success('资料修改成功')
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
  resetForm()
}

// 监听对话框打开
watch(() => props.modelValue, (val) => {
  if (val) {
    initForm()
  } else {
    resetForm()
  }
})
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="修改资料"
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
        <el-input :value="agentStore.agentId" disabled />
      </el-form-item>

      <el-form-item label="角色">
        <el-tag :type="agentStore.agentRole === 'admin' ? 'danger' : 'primary'">
          {{ agentStore.agentRole === 'admin' ? '管理员' : '坐席' }}
        </el-tag>
      </el-form-item>

      <el-form-item label="姓名" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="1-50字符"
          clearable
        />
      </el-form-item>

      <el-form-item label="头像URL">
        <el-input
          v-model="formData.avatar_url"
          placeholder="可选，输入头像图片URL"
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
