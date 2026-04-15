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
  } else {
    next()
  }
})

export default router
