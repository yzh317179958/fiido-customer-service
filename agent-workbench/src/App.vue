<script setup lang="ts">
import { onMounted } from 'vue'
import { useAgentStore } from '@/stores/agentStore'

const agentStore = useAgentStore()

onMounted(() => {
  // 尝试恢复会话
  agentStore.restoreSession()
})
</script>

<template>
  <router-view />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>
