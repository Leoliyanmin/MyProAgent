import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

// 如果你有全局 CSS，也可以在这里引入
// import './style.css' 

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')