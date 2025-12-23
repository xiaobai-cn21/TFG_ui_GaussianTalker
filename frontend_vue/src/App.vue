<template>
  <!-- 应用的根容器 -->
  <div id="app-root">
    <!-- 全局背景粒子：四个页面共用一层，避免重复渲染 -->
    <BackgroundParticles v-bind="particleProps" />
    <!-- 路由视图：确保 router-view 能够正确接收并渲染组件 -->
    <router-view v-slot="{ Component }">
      <!-- 页面切换动画：使用内建的 transition 组件 -->
      <transition name="fade-page" mode="out-in">
        <!-- 
          添加 key 属性可以确保在相同组件不同参数跳转时也能触发动画
          同时增加 component 动态挂载
        -->
        <component :is="Component" :key="$route.fullPath" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import BackgroundParticles from './components/BackgroundParticles.vue'
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router';
import { useTheme } from './composables/useTheme'
import { useFont } from './composables/useFont'

const route = useRoute();

/**
 * 根据主题动态生成粒子参数：
 * - 暗色：粒子更多、更亮、速度略快，增强赛博氛围
 * - 亮色：粒子更少、更淡、速度更慢，避免“发灰/刺眼”
 */
const { theme, initTheme } = useTheme();
const { initFont } = useFont();
const particleProps = computed(() => {
  const isLight = theme.value === 'light';

  return {
    // 亮色模式：粒子更少，避免画面“发灰/脏”
    maxDensity: isLight ? 60 : 100,
    minDensity: isLight ? 20 : 30,

    // 亮色更慢，暗色更活跃
    speedFactor: isLight ? 0.6 : 1.0,

    // 亮色粒子更小更轻
    sizeMin: isLight ? 0.5 : 0.6,
    sizeMax: isLight ? 1.6 : 2.0,

    // 亮色透明度更低
    alpha: isLight ? 0.18 : 0.3,

    // 亮色偏紫蓝，暗色偏青蓝（与你页面主视觉一致）
    colorA: isLight ? 'rgba(133, 132, 255, 1)' : 'rgba(34, 211, 238, 1)',
    colorB: isLight ? 'rgba(255, 109, 56, 1)' : 'rgba(6, 182, 212, 1)',

    // 密度计算分母：亮色稍大 → 更稀疏
    densityDivisor: isLight ? 18000 : 15000,
  };
});

onMounted(() => {
  // ✅ 初始化必须放在生命周期里，但 import 不能放这里
  initTheme()
  initFont()

  console.log('[SYSTEM] App Initialized')
  console.log('[SYSTEM] Current Route FullPath:', route.fullPath)
})

</script>

<style>
/**
 * 全局基础样式重置
 * 这里的样式不使用 scoped，以确保 body 和 html 能够受到控制
 */
html, body {
  margin: 0;
  padding: 0;
  background-color: #050505; /* 核心：防止背景在组件加载前闪烁白色 */
  color: #ffffff;
  width: 100%;
  height: 100%;
  overflow-x: hidden;
}

#app-root {
  min-height: 100vh;
  width: 100%;
  position: relative;
}

/* 页面切换动画：淡入淡出并带有轻微位移 */
.fade-page-enter-active,
.fade-page-leave-active {
  transition: opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1), 
              transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 自定义滚动条美化 */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: #000;
}
::-webkit-scrollbar-thumb {
  background: #164e63; /* cyan-900 */
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: #0891b2; /* cyan-600 */
}
</style>