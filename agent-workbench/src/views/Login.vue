<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentStore } from '@/stores/agentStore'
import axios from 'axios'
import { setAccessToken, clearAccessToken } from '@/utils/authStorage'

const router = useRouter()
const agentStore = useAgentStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const handleLogin = async () => {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // 调用JWT登录API
    const response = await axios.post(`${API_BASE}/api/agent/login`, {
      username: username.value,
      password: password.value
    })

    if (!response.data.success) {
      throw new Error(response.data.message || '登录失败')
    }

    // 保存Token到当前标签，支持多账号同时登录
    setAccessToken(response.data.token)

    // 保存用户信息到store
    await agentStore.login({
      agentId: response.data.agent.username,
      agentName: response.data.agent.name,
      role: response.data.agent.role
    } as any)

    // 跳转到工作台
    router.push('/dashboard')
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.message || '登录失败'
    clearAccessToken()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="grid-pattern"></div>
    </div>

    <div class="login-box">
      <div class="login-header">
        <div class="brand-logo-container">
          <img src="/fiido2.png" alt="Fiido Logo" class="fiido-logo" />
        </div>
        <h1>客服工作台</h1>
        <p class="subtitle">CUSTOMER SERVICE WORKBENCH</p>
        <div class="divider"></div>
        <span class="welcome-text">欢迎登录，开始您的服务</span>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            用户名
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="请输入用户名，例如：admin"
            required
            class="form-input"
          >
        </div>

        <div class="form-group">
          <label for="password">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            密码
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            required
            class="form-input"
          >
        </div>

        <div v-if="error" class="error-message">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          {{ error }}
        </div>

        <button type="submit" :disabled="loading" class="login-button">
          <span v-if="!loading" class="button-content">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
              <polyline points="10 17 15 12 10 7"></polyline>
              <line x1="15" y1="12" x2="3" y2="12"></line>
            </svg>
            登录工作台
          </span>
          <span v-else class="loading-content">
            <div class="spinner-ring"></div>
            登录中...
          </span>
        </button>
      </form>

      <div class="login-footer">
        <div class="footer-links">
          <span class="footer-text">Powered by Fiido AI System</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecef 100%);
  position: relative;
  overflow: hidden;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.3;
  animation: float 25s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #4ECDC4 0%, transparent 70%);
  top: -250px;
  left: -250px;
  animation-delay: 0s;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #52C7B8 0%, transparent 70%);
  bottom: -200px;
  right: -200px;
  animation-delay: 12s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

.grid-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(78, 205, 196, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(78, 205, 196, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 60s linear infinite;
}

@keyframes gridMove {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(50px, 50px);
  }
}

.login-box {
  background: white;
  padding: 50px 45px;
  border-radius: 20px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(78, 205, 196, 0.1);
  width: 100%;
  max-width: 460px;
  position: relative;
  z-index: 10;
  animation: slideIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.brand-logo-container {
  margin-bottom: 30px;
  animation: logoAppear 0.8s ease 0.2s both;
}

@keyframes logoAppear {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.fiido-logo {
  height: 80px;
  width: auto;
  filter: drop-shadow(0 4px 12px rgba(78, 205, 196, 0.2));
}

.login-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 11px;
  color: #4ECDC4;
  margin: 0;
  letter-spacing: 3px;
  text-transform: uppercase;
  font-weight: 600;
}

.divider {
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #4ECDC4, #52C7B8);
  margin: 20px auto;
  border-radius: 2px;
}

.welcome-text {
  display: block;
  font-size: 14px;
  color: #718096;
  font-weight: 400;
}

.login-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 10px;
}

.form-group label svg {
  color: #4ECDC4;
}

.form-input {
  width: 100%;
  padding: 14px 18px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
  background: #fafafa;
  color: #2d3748;
}

.form-input:hover {
  border-color: #cbd5e0;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #4ECDC4;
  background: white;
  box-shadow: 0 0 0 4px rgba(78, 205, 196, 0.1);
}

.form-input::placeholder {
  color: #a0aec0;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
  color: #c53030;
  padding: 14px 18px;
  border-radius: 10px;
  font-size: 13px;
  margin-bottom: 24px;
  border-left: 4px solid #fc8181;
  font-weight: 500;
  animation: shake 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97);
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-8px); }
  20%, 40%, 60%, 80% { transform: translateX(8px); }
}

.error-message svg {
  flex-shrink: 0;
}

.login-button {
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, #4ECDC4 0%, #52C7B8 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(78, 205, 196, 0.4);
  position: relative;
  overflow: hidden;
}

.login-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: left 0.5s;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(78, 205, 196, 0.5);
}

.login-button:hover:not(:disabled)::before {
  left: 100%;
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.button-content,
.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.spinner-ring {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-footer {
  margin-top: 36px;
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
}

.footer-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.footer-text {
  font-size: 12px;
  color: #a0aec0;
  font-weight: 500;
}
</style>
