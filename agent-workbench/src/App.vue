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
  background: var(--agent-body-bg, #f4f6fb);
  color: var(--agent-text-color, #111827);
  transition: background 0.3s ease, color 0.3s ease;
}

:root {
  --agent-body-bg: #f4f6fb;
  --agent-text-color: #111827;
}

[data-agent-theme='dark'] {
  --agent-body-bg: #050b18;
  --agent-text-color: #e2e8f0;
}
</style>
