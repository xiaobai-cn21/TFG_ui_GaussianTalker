<template>
  <button class="cyber-button" @click="$emit('click')">
    <div class="button-content">
      <!-- 左侧图标槽位 -->
      <div class="icon-container">
        <slot name="icon"></slot>
      </div>
      
      <!-- 文字内容 -->
      <div class="text-container">
        <span class="label">{{ label }}</span>
        <span class="sub-label">{{ subLabel }}</span>
      </div>
    </div>

    <!-- 右侧状态装饰点 -->
    <div class="status-indicator">
      <div class="dot"></div>
    </div>

    <!-- 悬停时的扫光动效层 -->
    <div class="scanner-layer"></div>
  </button>
</template>

<script setup>
defineProps({
  label: String,
  subLabel: String
});
defineEmits(['click']);
</script>

<style scoped>
.cyber-button {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  outline: none;
}

.cyber-button:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(6, 182, 212, 0.5);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
  transform: translateY(-2px);
}

.cyber-button:active {
  transform: scale(0.98);
}

.button-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.icon-container {
  display: flex;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  color: #22d3ee;
  transition: background 0.3s;
}

.cyber-button:hover .icon-container {
  background: rgba(6, 182, 212, 0.2);
  color: #ffffff;
}

.text-container {
  text-align: left;
}

.label {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: 0.05em;
}

.sub-label {
  display: block;
  font-size: 0.7rem;
  color: var(--fg);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.status-indicator {
  opacity: 0;
  transition: opacity 0.3s;
}

.cyber-button:hover .status-indicator {
  opacity: 1;
}

.dot {
  width: 8px;
  height: 8px;
  background: #22d3ee;
  border-radius: 50%;
  box-shadow: 0 0 10px #22d3ee;
  animation: pulse 1.5s infinite;
}

.scanner-layer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  transform: skewX(-20deg);
  transition: left 0.6s ease-in-out;
}

.cyber-button:hover .scanner-layer {
  left: 100%;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}
</style>