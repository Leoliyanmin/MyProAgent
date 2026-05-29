# 登录页面实现 TODO

## 📋 任务清单

### 1. 创建登录/注册组件
-[x] 创建 `frontend/src/views/LoginView.vue`
-[x] 创建 `frontend/src/views/RegisterView.vue`
-[x] 或者创建统一的 `frontend/src/views/AuthView.vue`（包含登录和注册切换）

### 2. 登录页面功能
-[x] 邮箱输入框（带格式验证）
-[x] 密码输入框（带显示/隐藏切换）
-[x] 登录按钮（带 loading 状态）
-[x] 记住我选项（可选）
-[x] 跳转到注册页面的链接
-[x] 错误提示显示区域

### 3. 注册页面功能
-[x] 邮箱输入框（带格式验证）
-[x] 发送验证码按钮（带 60 秒倒计时）
-[x] 验证码输入框
-[x] 密码输入框（强度提示可选）
-[x] 确认密码输入框（密码匹配验证）
-[x] 姓名输入框
-[x] 注册按钮（带 loading 状态）
-[x] 跳转到登录页面的链接
-[x] 错误提示显示区域

### 4. 表单验证
-[x] 邮箱格式验证（正则表达式）
-[x] 密码长度验证（最少 6 位）
-[x] 必填字段验证
-[x] 验证码格式验证（6 位数字）
-[x] 实时验证反馈

### 5. 集成 API
-[x] 导入 `useAuthStore`
-[x] 登录方法调用 `auth.login(email, password)`
-[x] 注册方法调用 `auth.register(email, password, full_name, code)`
-[x] 发送验证码调用 `auth.sendVerificationCode(email)`
-[x] 处理 API 错误（显示错误信息）
-[x] 登录成功后保存 token

### 6. 路由配置
-[x] 添加登录路由 `/login`
-[x] 添加注册路由 `/register`
-[x] 配置路由守卫（未登录跳转到登录页）
-[x] 登录后跳转到首页 `/dashboard`

### 7. 路由守卫
-[x] 创建 `frontend/src/router/guards.js`
-[x] 检查登录状态 `auth.isAuthenticated`
-[x] 未登录用户重定向到 `/login`
-[x] 已登录用户访问 `/login` 重定向到 `/dashboard`

### 8. 状态初始化
-[x] 在 `App.vue` 中调用 `auth.initAuth()`
-[x] 页面刷新时自动恢复登录状态
-[x] 验证 token 有效性

### 9. UI/UX 优化
-[x] 添加加载动画（登录/注册时）
-[x] 添加成功提示（Toast 或 Alert）
-[x] 表单输入框样式美化
-[x] 响应式布局（移动端适配）
-[x] 添加项目 Logo 和标题
-[x] 背景图片或渐变

### 10. 测试
-[x] 测试登录流程（正确/错误密码）
-[x] 测试注册流程（发送验证码、注册成功）
-[x] 测试表单验证（各种边界情况）
-[x] 测试路由跳转
-[x] 测试 token 持久化

---

## 🗂️ 文件结构

```
frontend/src/
├── views/
│   ├── AuthView.vue          # 登录/注册统一视图（可选）
│   ├── LoginView.vue         # 登录页面
│   └── RegisterView.vue      # 注册页面
├── components/
│   └── auth/
│       ├── LoginForm.vue     # 登录表单组件
│       ├── RegisterForm.vue  # 注册表单组件
│       └── VerifyCode.vue    # 验证码发送组件
├── router/
│   ├── index.js              # 路由配置
│   └── guards.js             # 路由守卫
├── stores/
│   └── auth.js               # 已创建
└── services/
    └── api.js                # 已创建
```

---

## 🔧 技术实现要点

### 1. 使用 Composition API
```vue
<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  email: '',
  password: ''
})

const handleLogin = async () => {
  const result = await auth.login(form.email, form.password)
  if (result.success) {
    router.push('/dashboard')
  }
}
</script>
```

### 2. 表单验证示例
```javascript
const validateEmail = (email) => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return regex.test(email)
}

const validatePassword = (password) => {
  return password.length >= 6
}
```

### 3. 验证码倒计时
```javascript
const countdown = ref(0)

const sendCode = async () => {
  await auth.sendVerificationCode(form.email)
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}
```

### 4. 路由守卫示例
```javascript
// router/guards.js
import { useAuthStore } from '../stores/auth.js'

export const authGuard = (to, from, next) => {
  const auth = useAuthStore()
  
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && auth.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
}
```

---

## 📚 相关文档

- [后端 API 文档](http://localhost:8000/docs)
- [前端 Integration 指南](./frontend/INTEGRATION.md)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vue Router 文档](https://router.vuejs.org/)

---

## ✅ 验收标准

-[x] 用户可以通过邮箱和密码登录
-[x] 用户可以通过邮箱注册新账号
-[x] 注册时需要通过邮箱验证码验证
-[x] 登录成功后跳转到工作台
-[x] 未登录用户无法访问受保护页面
-[x] 页面刷新后保持登录状态
-[x] 表单有基本的输入验证
-[x] 显示友好的错误提示

---

## 🎯 优先级建议

**P0 - 必须完成：**
1. 登录页面基本功能
2. 路由配置和守卫
3. 状态初始化

**P1 - 重要：**
4. 注册页面
5. 验证码功能
6. 表单验证

**P2 - 优化：**
7. UI/UX 美化
8. 记住我功能
9. 密码强度提示
