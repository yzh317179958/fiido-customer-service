<script setup lang="ts">
import { computed } from 'vue'
import type { CustomerProfile } from '@/types'

const props = defineProps<{
  customer: CustomerProfile | null
  loading?: boolean
}>()

// 语言名称映射
const languageNames: Record<string, string> = {
  en: 'English',
  de: 'Deutsch',
  fr: 'Français',
  it: 'Italiano',
  es: 'Español'
}

// 来源渠道名称映射
const channelNames: Record<string, string> = {
  shopify_organic: 'Shopify 自然流量',
  shopify_campaign: 'Shopify 活动',
  amazon: 'Amazon',
  dealer: '经销商',
  other: '其他'
}

// 数据脱敏
const maskEmail = (email: string): string => {
  const [namePart = '', domainPart = ''] = email.split('@')
  const safeName = namePart || 'user'
  const safeDomain = domainPart || 'example.com'
  const firstChar = safeName.charAt(0) || '*'
  return `${firstChar}***@${safeDomain}`
}

const maskPhone = (phone: string): string => {
  const cleaned = phone.replace(/\s/g, '')
  if (cleaned.length > 7) {
    const prefix = cleaned.slice(0, 3)
    const suffix = cleaned.slice(-4)
    return `${prefix}***${suffix}`
  }
  return phone
}

// 国旗 emoji
const getFlagEmoji = (countryCode: string): string => {
  if (!countryCode) return ''
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0))
  return String.fromCodePoint(...codePoints)
}

const maskedEmail = computed(() => props.customer ? maskEmail(props.customer.email) : '')
const maskedPhone = computed(() => props.customer ? maskPhone(props.customer.phone) : '')
const customerInitial = computed(() => props.customer?.name?.charAt(0)?.toUpperCase() || '客')
</script>

<template>
  <div class="customer-profile">
    <!-- Loading 状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载客户信息...</span>
    </div>

    <!-- 无客户信息 -->
    <div v-else-if="!customer" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
      </svg>
      <p>暂无客户信息</p>
    </div>

    <!-- 客户画像 -->
    <div v-else class="profile-content">
      <!-- 基本信息卡片 -->
      <div class="profile-card">
        <div class="card-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <h3>基本信息</h3>
        </div>

        <div class="card-body">
          <!-- 头像与姓名 -->
          <div class="profile-avatar">
            <img
              v-if="customer?.avatar_url"
              :src="customer.avatar_url"
              :alt="customer?.name || '客户头像'"
              class="avatar-img"
            >
            <div v-else class="avatar-placeholder">
              {{ customerInitial }}
            </div>
          </div>

          <div class="profile-name">{{ customer?.name || '匿名客户' }}</div>

          <!-- 联系信息 -->
          <div class="info-grid">
            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <polyline points="22,6 12,13 2,6"></polyline>
              </svg>
              <span class="info-label">邮箱</span>
              <span class="info-value">{{ maskedEmail }}</span>
            </div>

            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
              </svg>
              <span class="info-label">电话</span>
              <span class="info-value">{{ maskedPhone }}</span>
            </div>

            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                <circle cx="12" cy="10" r="3"></circle>
              </svg>
              <span class="info-label">位置</span>
              <span class="info-value">
                <span class="country-flag">{{ getFlagEmoji(customer?.country || '') }}</span>
                {{ customer?.city || '-' }}, {{ customer?.country || '' }}
              </span>
            </div>

            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
              </svg>
              <span class="info-label">语言</span>
              <span class="info-value">{{ languageNames[customer?.language_preference || ''] }}</span>
            </div>

            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"></line>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
              </svg>
              <span class="info-label">货币</span>
              <span class="info-value">{{ customer.payment_currency }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 来源与状态卡片 -->
      <div class="status-card">
        <div class="card-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          <h3>来源与状态</h3>
        </div>

        <div class="card-body">
          <!-- 来源渠道 -->
          <div class="status-item">
            <span class="status-label">来源渠道</span>
              <span class="status-badge channel">
                {{ channelNames[customer?.source_channel || 'other'] }}
              </span>
            </div>

          <!-- GDPR 状态 -->
          <div class="status-item">
            <span class="status-label">GDPR 同意</span>
            <span :class="['status-badge', customer?.gdpr_consent ? 'success' : 'warning']">
              {{ customer?.gdpr_consent ? '已同意' : '未同意' }}
            </span>
          </div>

          <!-- 营销订阅 -->
          <div class="status-item">
            <span class="status-label">营销订阅</span>
            <span :class="['status-badge', customer?.marketing_subscribed ? 'success' : 'default']">
              {{ customer?.marketing_subscribed ? '已订阅' : '未订阅' }}
            </span>
          </div>

          <!-- VIP 状态 -->
          <div v-if="customer?.vip_status" class="status-item">
            <span class="status-label">VIP 会员</span>
            <span class="status-badge vip">
              ⭐ {{ (customer?.vip_status || '').toUpperCase() }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.customer-profile {
  height: 100%;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #a0aec0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #4ECDC4;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state svg {
  margin-bottom: 16px;
  color: #cbd5e0;
}

.profile-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profile-card,
.status-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  background: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
}

.card-header svg {
  color: #4ECDC4;
}

.card-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}

.card-body {
  padding: 16px;
}

.profile-avatar {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.avatar-img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #4ECDC4;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4ECDC4, #52C7B8);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 600;
}

.profile-name {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 20px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-item {
  display: grid;
  grid-template-columns: 20px 70px 1fr;
  gap: 10px;
  align-items: center;
}

.info-item svg {
  color: #4ECDC4;
}

.info-label {
  font-size: 13px;
  color: #718096;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #2d3748;
  font-weight: 500;
}

.country-flag {
  font-size: 16px;
  margin-right: 4px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f7fafc;
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-size: 13px;
  color: #718096;
  font-weight: 500;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.channel {
  background: #e6f7f7;
  color: #4ECDC4;
}

.status-badge.success {
  background: #c6f6d5;
  color: #22543d;
}

.status-badge.warning {
  background: #fed7d7;
  color: #c53030;
}

.status-badge.default {
  background: #e2e8f0;
  color: #718096;
}

.status-badge.vip {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  color: #744210;
}
</style>
