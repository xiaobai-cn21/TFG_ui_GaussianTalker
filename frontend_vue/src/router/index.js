import { createRouter, createWebHashHistory } from 'vue-router'

import Index from '../views/index.vue'
import ModelTraining from '../views/model_training.vue'
import VideoGeneration from '../views/video_generation.vue'
import ChatSystem from '../views/chat_system.vue'

const routes = [
  { 
    path: '/', 
    name: 'Index',
    component: Index 
  },
  { 
    path: '/model_training', 
    name: 'ModelTraining',
    component: ModelTraining 
  },
  { path: '/video_generation', 
    name: 'VideoGeneration',
    component: VideoGeneration 
  },
  {
    path: '/chat_system',
    name: 'ChatSystem',
    component: ChatSystem
  },
  // 捕获所有未定义路由并重定向到首页，防止因为路径输入错误导致黑屏
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  /**
   * 核心修复：切换到 Hash 模式 (createWebHashHistory)
   * WebHistory 模式需要后端服务器配合重定向，否则在预览环境下刷新或初次加载
   * 经常会导致路由无法匹配到组件，从而卡在根容器背景色中。
   */
  history: createWebHashHistory(),
  routes
})

// 导航守卫：用于在控制台监控路由跳转情况，方便排查卡死问题
router.beforeEach((to, from, next) => {
  console.log(`[ROUTER] 正在从 ${from.path} 跳转至 ${to.path}`);
  next();
})

export default router