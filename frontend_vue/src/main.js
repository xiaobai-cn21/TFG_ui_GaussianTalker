import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/style.css' // 引入 Tailwind CSS 或全局样式

/**
 * 初始化 Vue 应用
 * 1. 使用 createApp 创建实例
 * 2. 使用 .use(router) 挂载路由插件
 * 3. 使用 .mount('#app') 挂载到 index.html 中 ID 为 app 的 div 上
 */
const app = createApp(App)

// 挂载路由配置
app.use(router)

// 挂载应用
app.mount('#app')