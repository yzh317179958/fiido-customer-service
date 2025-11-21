<script setup lang="ts">
import { useAgentStore } from '@/stores/agentStore'
import { useRouter } from 'vue-router'

const agentStore = useAgentStore()
const router = useRouter()

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    agentStore.logout()
    router.push('/login')
  }
}
</script>

<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1>坐席工作台</h1>
      <div class="agent-info">
        <span class="agent-name">{{ agentStore.agentName }}</span>
        <span class="agent-id">({{ agentStore.agentId }})</span>
        <button @click="handleLogout" class="logout-button">退出</button>
      </div>
    </div>

    <div class="dashboard-content">
      <div class="welcome-message">
        <h2>欢迎，{{ agentStore.agentName }}！</h2>
        <p>您已成功登录坐席工作台</p>
        <div class="info-box">
          <p>📋 <strong>下一步功能</strong>：</p>
          <ul>
            <li>P0-12: 会话列表 - 查看待处理的用户会话</li>
            <li>P0-13: 接入操作 - 接管用户会话</li>
            <li>P0-14: 坐席聊天 - 与用户实时对话</li>
            <li>P0-15: 释放操作 - 结束会话并恢复AI</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.dashboard-header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.agent-id {
  font-size: 13px;
  color: #666;
}

.logout-button {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-button:hover {
  background: #e5e7eb;
}

.dashboard-content {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-message {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.welcome-message h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.welcome-message > p {
  font-size: 16px;
  color: #666;
  margin-bottom: 30px;
}

.info-box {
  background: #f9fafb;
  border-left: 4px solid #667eea;
  padding: 20px;
  border-radius: 8px;
}

.info-box p {
  font-size: 14px;
  color: #333;
  margin-bottom: 12px;
}

.info-box ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-box li {
  padding: 8px 0;
  font-size: 14px;
  color: #666;
  border-bottom: 1px solid #e5e7eb;
}

.info-box li:last-child {
  border-bottom: none;
}
</style>
