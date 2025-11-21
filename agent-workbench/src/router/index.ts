import { createRouter, createWebHistory } from 'vue-router'
import { useAgentStore } from '@/stores/agentStore'

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
    {
      path: '/',
      redirect: '/dashboard'
    }
  ]
})

// Navigation guard
router.beforeEach((to, _from, next) => {
  const agentStore = useAgentStore()

  // 如果需要认证但未登录，跳转到登录页
  if (to.meta.requiresAuth && !agentStore.isLoggedIn) {
    next('/login')
  }
  // 如果已登录访问登录页，跳转到工作台
  else if (to.path === '/login' && agentStore.isLoggedIn) {
    next('/dashboard')
  }
  else {
    next()
  }
})

export default router
