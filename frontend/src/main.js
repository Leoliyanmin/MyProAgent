import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth.js'

// 如果你有全局 CSS，也可以在这里引入
// import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

// Initialize auth state before mounting the app
// This ensures the auth state is ready before route guards run
const authStore = useAuthStore()
authStore.initAuth().then(() => {
  app.use(router)
  app.mount('#app')
})