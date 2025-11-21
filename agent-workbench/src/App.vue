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

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
