import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/platform',
    name: 'PlatformManage',
    component: () => import('../views/PlatformManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/order',
    name: 'OrderProcess',
    component: () => import('../views/OrderProcess.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/order-query',
    name: 'OrderQuery',
    component: () => import('../views/OrderQuery.vue'),
    meta: { requiresAuth: true }
  },
  // 管理员专用路由（不在导航中显示，仅admin用户可访问）
  {
    path: '/sys-mgmt-console',
    name: 'UserManagement',
    component: () => import('../views/UserManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
  } else if (to.meta.requiresAdmin && authStore.username !== 'admin') {
    // 非admin用户访问管理员页面，重定向到首页
    next('/')
  } else {
    next()
  }
})

export default router
