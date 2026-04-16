import { useAuthStore } from '../stores/auth.js'

export const authGuard = async (to, from, next) => {
  const auth = useAuthStore()
  
  if (to.meta.requiresAuth === true && !auth.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
}
