<template>
  <div class="theme-wrapper">
    <!-- 原主题切换按钮：行为不变 -->
    <button
      type="button"
      class="theme-toggle"
      @click="toggleTheme"
      :aria-label="theme === 'dark' ? '切换到日间模式' : '切换到夜间模式'"
      :title="theme === 'dark' ? '日间模式' : '夜间模式'"
    >
      <span class="dot" />
      <span class="label">{{ theme === 'dark' ? 'Night' : 'Day' }}</span>
    </button>

    <!-- 展开区域：放字体选择（桌面 hover / 移动端点击） -->
    <div class="theme-panel">
      <slot />
    </div>
  </div>
</template>


<script setup>
import { useTheme } from '../composables/useTheme'
const { theme, toggleTheme } = useTheme()
</script>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--fg);
  cursor: pointer;
  user-select: none;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--secondary);
}

.label {
  font-size: 12px;
  opacity: 0.85;
}

.theme-wrapper {
  position: relative;
  display: inline-block;
}

/* 原按钮样式保持 */
.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  color: var(--fg);
  cursor: pointer;
  user-select: none;
}

/* 小圆点随主题变化 */
.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--accent);
}

/* 标签 */
.label {
  font-size: 12px;
  opacity: 0.85;
}

/* 二级面板（默认隐藏） */
.theme-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  min-width: 160px;
  padding: 12px;
  border-radius: 12px;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  opacity: 0;
  pointer-events: none;
  transform: translateY(-6px);
  transition: all 0.2s ease;
}

/* hover 展开（桌面端） */
.theme-wrapper:hover .theme-panel {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

</style>
