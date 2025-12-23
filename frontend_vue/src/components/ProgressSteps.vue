<template>
  <Transition name="progress-fade">
    <div v-if="visible" class="progress-overlay">
      <div class="progress-panel">
        <!-- 顶部标题 -->
        <div class="progress-header">
          <div class="header-icon">
            <Loader2Icon class="w-5 h-5 animate-spin" />
          </div>
          <div class="header-text">
            <h3>{{ title }}</h3>
            <p>{{ subtitle }}</p>
          </div>
        </div>

        <!-- 步骤进度条 -->
        <div class="steps-container">
          <div
            v-for="(step, index) in steps"
            :key="index"
            :class="['step-item', getStepClass(index)]"
          >
            <!-- 步骤图标 -->
            <div class="step-indicator">
              <CheckIcon v-if="index < currentStep" class="w-4 h-4" />
              <Loader2Icon v-else-if="index === currentStep" class="w-4 h-4 animate-spin" />
              <span v-else class="step-number">{{ index + 1 }}</span>
            </div>

            <!-- 步骤内容 -->
            <div class="step-content">
              <span class="step-label">{{ step.label }}</span>
              <span v-if="step.detail && index === currentStep" class="step-detail">
                {{ step.detail }}
              </span>
            </div>

            <!-- 连接线 -->
            <div v-if="index < steps.length - 1" :class="['step-connector', { 'completed': index < currentStep }]"></div>
          </div>
        </div>

        <!-- 总体进度条 -->
        <div class="overall-progress">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: overallProgress + '%' }"
            ></div>
            <div class="progress-glow"></div>
          </div>
          <div class="progress-info">
            <span class="progress-percent">{{ overallProgress }}%</span>
            <span v-if="estimatedTime" class="progress-time">
              预计剩余: {{ estimatedTime }}
            </span>
          </div>
        </div>

        <!-- 当前状态消息 -->
        <div class="status-message">
          <div class="message-dot"></div>
          <span>{{ statusMessage || '处理中...' }}</span>
        </div>

        <!-- 取消按钮（可选） -->
        <button v-if="cancellable" @click="$emit('cancel')" class="cancel-btn">
          <XIcon class="w-4 h-4" />
          <span>取消操作</span>
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue';
import {
  Loader2 as Loader2Icon,
  Check as CheckIcon,
  X as XIcon
} from 'lucide-vue-next';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '正在处理'
  },
  subtitle: {
    type: String,
    default: 'PROCESSING IN PROGRESS'
  },
  steps: {
    type: Array,
    default: () => [
      { label: '准备中', detail: '' },
      { label: '处理中', detail: '' },
      { label: '完成', detail: '' }
    ]
  },
  currentStep: {
    type: Number,
    default: 0
  },
  statusMessage: {
    type: String,
    default: ''
  },
  estimatedTime: {
    type: String,
    default: ''
  },
  cancellable: {
    type: Boolean,
    default: false
  }
});

defineEmits(['cancel']);

const overallProgress = computed(() => {
  if (props.steps.length === 0) return 0;
  return Math.round((props.currentStep / props.steps.length) * 100);
});

const getStepClass = (index) => {
  if (index < props.currentStep) return 'completed';
  if (index === props.currentStep) return 'active';
  return 'pending';
};
</script>

<style scoped>
.progress-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.progress-panel {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 20px;
  padding: 32px;
  width: 90%;
  max-width: 520px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

/* 日间模式适配 */
:global(html.light) .progress-overlay {
  background: rgba(255, 255, 255, 0.85);
}

:global(html.light) .progress-panel {
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.2);
}

/* 头部 */
.progress-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
}

.header-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 12px;
  color: var(--accent);
}

:global(html.light) .header-icon {
  background: rgba(3, 105, 161, 0.1);
  border-color: rgba(3, 105, 161, 0.3);
}

.header-text h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--fg);
  margin: 0;
}

.header-text p {
  font-size: 0.7rem;
  color: var(--text-muted);
  letter-spacing: 2px;
  margin: 4px 0 0;
}

/* 步骤容器 */
.steps-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 24px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  position: relative;
  padding: 12px 0;
}

/* 步骤指示器 */
.step-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

.step-item.pending .step-indicator {
  background: var(--card);
  border: 2px solid var(--border);
  color: var(--text-muted);
}

.step-item.active .step-indicator {
  background: rgba(34, 211, 238, 0.15);
  border: 2px solid var(--accent);
  color: var(--accent);
  box-shadow: 0 0 20px rgba(34, 211, 238, 0.3);
}

:global(html.light) .step-item.active .step-indicator {
  background: rgba(3, 105, 161, 0.1);
  border-color: #0369a1;
  color: #0369a1;
  box-shadow: 0 0 20px rgba(3, 105, 161, 0.2);
}

.step-item.completed .step-indicator {
  background: var(--accent);
  border: 2px solid var(--accent);
  color: #000;
}

:global(html.light) .step-item.completed .step-indicator {
  background: #0369a1;
  border-color: #0369a1;
  color: #fff;
}

/* 步骤内容 */
.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 32px;
}

.step-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
  transition: color 0.3s ease;
}

.step-item.active .step-label {
  color: var(--fg);
}

.step-item.completed .step-label {
  color: var(--accent);
}

:global(html.light) .step-item.completed .step-label {
  color: #0369a1;
}

.step-detail {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* 连接线 */
.step-connector {
  position: absolute;
  left: 15px;
  top: 44px;
  width: 2px;
  height: calc(100% - 20px);
  background: var(--border);
  transition: background 0.3s ease;
}

.step-connector.completed {
  background: var(--accent);
}

:global(html.light) .step-connector.completed {
  background: #0369a1;
}

/* 总体进度条 */
.overall-progress {
  margin-bottom: 20px;
}

.progress-bar {
  height: 8px;
  background: var(--card);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

:global(html.light) .progress-bar {
  background: rgba(15, 23, 42, 0.1);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #06b6d4);
  border-radius: 4px;
  transition: width 0.5s ease;
  position: relative;
}

:global(html.light) .progress-fill {
  background: linear-gradient(90deg, #0369a1, #0284c7);
}

.progress-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 50px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4));
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.progress-percent {
  font-size: 14px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
}

:global(html.light) .progress-percent {
  color: #0369a1;
}

.progress-time {
  font-size: 12px;
  color: var(--text-muted);
}

/* 状态消息 */
.status-message {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 16px;
}

:global(html.light) .status-message {
  background: rgba(15, 23, 42, 0.04);
  border-color: rgba(15, 23, 42, 0.1);
}

.message-dot {
  width: 8px;
  height: 8px;
  background: var(--accent);
  border-radius: 50%;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

:global(html.light) .message-dot {
  background: #0369a1;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.status-message span {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

/* 取消按钮 */
.cancel-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.cancel-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

/* 过渡动画 */
.progress-fade-enter-active,
.progress-fade-leave-active {
  transition: all 0.3s ease;
}

.progress-fade-enter-from,
.progress-fade-leave-to {
  opacity: 0;
}

.progress-fade-enter-from .progress-panel,
.progress-fade-leave-to .progress-panel {
  transform: scale(0.95) translateY(10px);
}
</style>

