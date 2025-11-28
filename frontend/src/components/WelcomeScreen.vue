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
/* Premium Welcome Screen */
.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 30px;
  text-align: center;
  animation: welcomeFadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

@keyframes welcomeFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.welcome-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-weight: 600;
  font-size: 28px;
  margin-bottom: 24px;
  padding: 10px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1), 0 2px 6px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.welcome-avatar::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}

.welcome-avatar:hover {
  transform: scale(1.08) translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15), 0 4px 12px rgba(0, 0, 0, 0.1);
}

.welcome-avatar:hover::before {
  opacity: 1;
}

.welcome-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 50%;
  position: relative;
  z-index: 1;
}

.welcome-name {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #111827 0%, #374151 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-message {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.7;
  max-width: 300px;
  padding: 16px 20px;
  background: linear-gradient(to bottom, #f9fafb 0%, #f3f4f6 100%);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02);
  border: 1px solid #e5e7eb;
  position: relative;
  overflow: hidden;
}

.welcome-message::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);
  opacity: 0.6;
}
</style>
