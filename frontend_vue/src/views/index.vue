<template>
  <div class="index-container">
    <!-- 右上角外观控制条：主题 + 字体（横向并排） -->
    <div class="appearance-bar">
      <ThemeToggle />
      <FontSelector />
    </div>

    <!-- 主体内容区 -->
    <main class="main-content">
      <!-- 头部装饰与标题 -->
      <header class="header-section">
        <div class="icon-wrapper">
          <ShieldCheckIcon class="main-icon" />
        </div>
        <h1 class="title">
          Data Hammer Group
          <span class="subtitle">Talking System</span>
        </h1>
        <div class="divider"></div>
      </header>

      <!-- 导航按钮组 -->
      <nav class="button-grid">
        <CyberButton
          label="训练模型"
          sub-label="Model Training Protocol"
          @click="navigate('/model_training')"
        >
          <template #icon>
            <SettingsIcon class="w-6 h-6" />
          </template>
        </CyberButton>

        <CyberButton
          label="视频生成"
          sub-label="Render Engine Active"
          @click="navigate('/video_generation')"
        >
          <template #icon>
            <VideoIcon class="w-6 h-6" />
          </template>
        </CyberButton>

        <CyberButton
          label="人机对话"
          sub-label="Neural Link Stable"
          @click="navigate('/chat_system')"
        >
          <template #icon>
            <MessageSquareIcon class="w-6 h-6" />
          </template>
        </CyberButton>
      </nav>

      <!-- 底部系统信息 -->
      <footer class="footer-section">
        <div class="status-bar">
          <div class="status-dot"></div>
          <span>语音识别与合成</span>
          <span class="sep">|</span>
          <span>第 2 组</span>
        </div>
        <p class="copyright">© 2025 DATA HAMMER TALKING SYSTEM. ALL RIGHTS RESERVED.</p>
      </footer>
    </main>

    <!-- 顶部和底部装饰扫光条 -->
    <div class="top-scanline"></div>
    <div class="bottom-glow"></div>
  </div>
</template>

<script setup>
import ThemeToggle from '../components/ThemeToggle.vue'
import FontSelector from '../components/FontSelector.vue'

import { useRouter } from 'vue-router'
import {
  ShieldCheck as ShieldCheckIcon,
  Settings as SettingsIcon,
  Video as VideoIcon,
  MessageSquare as MessageSquareIcon
} from 'lucide-vue-next'

import CyberButton from '../components/CyberButton.vue'

const router = useRouter()

const navigate = (path) => {
  console.log(`[SYSTEM] 正在切换至协议: ${path}`)
  if (router) {
    router.push(path).catch(err => {
      console.warn('路由跳转受限，使用原生链接跳转', err)
      window.location.href = path
    })
  } else {
    window.location.href = path
  }
}
</script>

<style scoped>
.index-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg);
  color: var(--fg);
  overflow: hidden;
  font-family: var(--font-sans);
}

.main-content {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 440px;
  padding: 2rem;
  text-align: center;
  animation: contentFadeIn 1.2s cubic-bezier(0.22, 1, 0.36, 1);
}

.header-section {
  margin-bottom: 3.5rem;
}

.icon-wrapper {
  display: inline-flex;
  padding: 1rem;
  margin-bottom: 1.5rem;
  background: rgba(34, 211, 238, 0.05);
  border: 1px solid rgba(34, 211, 238, 0.2);
  border-radius: 1.25rem;
  box-shadow: 0 0 30px rgba(6, 182, 212, 0.1);
}

.main-icon {
  width: 2.5rem;
  height: 2.5rem;
  color: #22d3ee;
  filter: drop-shadow(0 0 8px rgba(34, 211, 238, 0.6));
}

/* 关键修复：标题渐变不要写死白色，改为主题变量 */
.title {
  font-size: 2.5rem;
  font-weight: 900;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin: 0;

  background: linear-gradient(to bottom, var(--fg), var(--text-muted));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 副标题也走主题变量（并保持 cyan 点缀） */
.subtitle {
  display: block;
  font-size: 1rem;
  font-weight: 300;
  letter-spacing: 0.5em;
  color: #22d3ee;
  opacity: 0.85;
  margin-top: 0.75rem;
  -webkit-text-fill-color: initial;
}

.divider {
  height: 2px;
  width: 60px;
  background: #06b6d4;
  margin: 2rem auto 0;
  border-radius: 2px;
  box-shadow: 0 0 20px #06b6d4;
}

.button-grid {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.footer-section {
  margin-top: 5rem;
}

.status-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.7rem;
  color: var(--text-muted);
  letter-spacing: 0.2em;
  margin-bottom: 0.75rem;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: #22d3ee;
  border-radius: 50%;
  box-shadow: 0 0 8px #22d3ee;
  animation: blink 2s infinite;
}

.sep {
  color: rgba(34, 211, 238, 0.2);
}

/* 关键修复：版权不要写死深灰，改为主题变量 */
.copyright {
  font-size: 0.7rem;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

/* 装饰性动效 */
.top-scanline {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, #06b6d4, transparent);
  opacity: 0.5;
  animation: scanlineMove 8s linear infinite;
}

.bottom-glow {
  position: fixed;
  bottom: -50px;
  left: 50%;
  transform: translateX(-50%);
  width: 300px;
  height: 100px;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, transparent 70%);
  filter: blur(20px);
  pointer-events: none;
}

/* 右上角外观控制条：固定定位，不挤压主内容 */
.appearance-bar {
  position: fixed;
  top: 22px;
  right: 26px;
  z-index: 30;
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

@media (max-width: 480px) {
  .appearance-bar {
    top: 14px;
    right: 14px;
    gap: 10px;
  }
}

@keyframes contentFadeIn {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

@keyframes scanlineMove {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@media (max-width: 480px) {
  .title { font-size: 2rem; }
  .main-content { padding: 1.5rem; }
}
</style>
