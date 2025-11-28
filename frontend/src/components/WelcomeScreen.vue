<script setup lang="ts">
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()
</script>

<template>
  <div class="welcome-screen">
    <div class="welcome-avatar">
      <img
        src="/fiido2.png"
        :alt="chatStore.botConfig.name"
      >
    </div>
    <div class="welcome-name">{{ chatStore.botConfig.name }}</div>
    <div class="welcome-message">{{ chatStore.botConfig.welcome }}</div>
  </div>
</template>

<style scoped>
.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 30px;
  text-align: center;
  animation: welcomeFadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes welcomeFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.welcome-avatar {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
  font-weight: 700;
  font-size: 36px;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
  padding: 8px;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.welcome-avatar::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 50%;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s;
}

.welcome-avatar:hover::before {
  opacity: 1;
}

.welcome-avatar:hover {
  transform: scale(1.08) translateY(-4px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.25);
}

.welcome-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.welcome-avatar:hover img {
  transform: scale(1.05);
}

.welcome-name {
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
  letter-spacing: 0.3px;
}

.welcome-message {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.7;
  max-width: 300px;
  font-weight: 400;
}
</style>
