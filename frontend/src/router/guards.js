import { useAuthStore } from '../stores/auth.js'

export const authGuard = async (to, from) => {
  const auth = useAuthStore()
  
  // Check if route requires authentication
  if (to.meta.requiresAuth === true && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  
  // Redirect authenticated users away from login/register pages
  if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
  
  // Allow navigation
  return true
}
