import { createRouter, createWebHistory } from 'vue-router'
import { authGuard } from './guards.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/calendar',
      name: 'calendar',
      component: () => import('../views/CalendarView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/files',
      name: 'files',
      component: () => import('../views/FileManagerView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/self-portrait',
      name: 'self-portrait',
      component: () => import('../views/SelfPortraitView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/theme-settings',
      name: 'theme-settings',
      component: () => import('../views/ThemeSettingsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agent-settings',
      name: 'agent-settings',
      component: () => import('../views/AgentSettingsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/user-settings',
      name: 'user-settings',
      component: () => import('../views/UserSettingsView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach(authGuard)

export default router
