import { createRouter, createWebHistory } from 'vue-router'
import { useAgentStore } from '@/stores/agentStore'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    // ⭐ v3.1.3 新增：管理员页面
    {
      path: '/admin/agents',
      name: 'AdminManagement',
      component: () => import('@/views/AdminManagement.vue'),
      meta: {
        requiresAuth: true,
        requiresAdmin: true  // 需要管理员权限
      }
    },
    // ⭐ v3.7.0 新增：快捷回复管理
    {
      path: '/quick-replies',
      name: 'QuickReplyManagement',
      component: () => import('@/views/QuickReplyManagement.vue'),
      meta: {
        requiresAuth: true  // 所有坐席都可以访问
      }
    },
    {
      path: '/',
      redirect: '/dashboard'
    }
  ]
})

// Navigation guard
router.beforeEach((to, _from, next) => {
  const agentStore = useAgentStore()

  // 🔴 关键修复: 确保在检查权限前恢复会话
  // 因为router guard可能在App.vue的onMounted之前执行
  if (!agentStore.isLoggedIn) {
    agentStore.restoreSession()
  }

  // 🔴 v3.1.3: 检查是否需要管理员权限
  if (to.meta.requiresAdmin) {
    if (!agentStore.isLoggedIn) {
      next('/login')
      return
    }
    if (agentStore.agentRole !== 'admin') {
      // 非管理员无法访问管理页面
      ElMessage.warning('需要管理员权限')
      next('/dashboard')
      return
    }
  }

  // 如果需要认证但未登录，跳转到登录页
  if (to.meta.requiresAuth && !agentStore.isLoggedIn) {
    next('/login')
    return
  }

  // 如果已登录访问登录页，跳转到工作台
  if (to.path === '/login' && agentStore.isLoggedIn) {
    next('/dashboard')
    return
  }

  next()
})

export default router
