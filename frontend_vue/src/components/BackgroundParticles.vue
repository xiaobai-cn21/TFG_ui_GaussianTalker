<template>
  <canvas
    ref="canvasRef"
    class="particle-canvas"
  />
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue';

/**
 * 粒子背景参数（由 App.vue 按主题传入）
 * 说明：
 * - 不传参时使用默认值，保持你当前暗色风格不变
 * - 传参后可在日间模式降低密度/透明度，避免刺眼
 */
const props = defineProps({
  // 允许外部传入“期望粒子数量上限”，最终仍会结合屏幕面积动态计算
  maxDensity: { type: Number, default: 100 },
  minDensity: { type: Number, default: 30 },

  // 粒子速度系数：越大越“活跃”
  speedFactor: { type: Number, default: 1 },

  // 粒子大小范围
  sizeMin: { type: Number, default: 0.6 },
  sizeMax: { type: Number, default: 2.0 },

  // 粒子透明度
  alpha: { type: Number, default: 0.3 },

  // 两种颜色（用于随机分配，增强层次）
  colorA: { type: String, default: 'rgba(34, 211, 238, 0.3)' },
  colorB: { type: String, default: 'rgba(6, 182, 212, 0.3)' },

  // 密度计算的“面积分母”，越小粒子越多；你原来是 15000
  densityDivisor: { type: Number, default: 15000 },
});

const canvasRef = ref(null);
let animationFrame = null;
let particles = [];
let ctx = null;

// 粒子密度（会根据屏幕面积动态计算，并受 min/max 约束）
const particleDensity = ref(80);

/**
 * resize handler（必须保持引用一致，才能正确 removeEventListener）
 * - 同时会根据屏幕面积重算 density 并重建粒子
 */
const resize = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  // 根据画布面积动态估算粒子数量，并限制到 min/max 范围
  const newDensity = Math.floor((canvas.width * canvas.height) / props.densityDivisor);
  particleDensity.value = Math.max(props.minDensity, Math.min(newDensity, props.maxDensity));

  initParticles();
};

/**
 * 根据当前参数初始化粒子
 * - 日夜模式切换时会触发 watch → 重建粒子
 */
const initParticles = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const speedBase = 0.4 * props.speedFactor;

  particles = Array.from({ length: particleDensity.value }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,

    // 基于原逻辑：速度在 [-0.5, 0.5] * speedBase
    vx: (Math.random() - 0.5) * speedBase,
    vy: (Math.random() - 0.5) * speedBase,

    // 粒子大小：由 sizeMin~sizeMax 控制
    size: props.sizeMin + Math.random() * (props.sizeMax - props.sizeMin),

    // 颜色：二选一，透明度由 alpha 控制（通过替换 rgba 的最后一位实现）
    color: Math.random() > 0.5 ? withAlpha(props.colorA, props.alpha) : withAlpha(props.colorB, props.alpha),
  }));
};

/**
 * 将 rgba(...) 的 alpha 覆盖为指定值
 * - 允许你传入的颜色字符串仍是 rgba
 * - 如果传入不是 rgba，保持原样（兜底）
 */
function withAlpha(rgbaStr, alpha) {
  const m = rgbaStr.match(/^rgba?\(([^)]+)\)$/i);
  if (!m) return rgbaStr;

  const parts = m[1].split(',').map(s => s.trim());
  // rgb 或 rgba 都允许，最终输出 rgba
  const r = parts[0] ?? '34';
  const g = parts[1] ?? '211';
  const b = parts[2] ?? '238';
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const animate = () => {
  const canvas = canvasRef.value;
  if (!canvas || !ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  particles.forEach((p) => {
    p.x += p.vx;
    p.y += p.vy;

    // 边界反弹
    if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fillStyle = p.color;
    ctx.fill();
  });

  animationFrame = requestAnimationFrame(animate);
};

onMounted(() => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  ctx = canvas.getContext('2d');

  resize();
  window.addEventListener('resize', resize);
  animationFrame = requestAnimationFrame(animate);

  /**
   * 当外部参数变化（主题切换）时：
   * - 重新计算 density 并重建粒子，使效果即时生效
   */
  watch(
    () => [
      props.maxDensity,
      props.minDensity,
      props.speedFactor,
      props.sizeMin,
      props.sizeMax,
      props.alpha,
      props.colorA,
      props.colorB,
      props.densityDivisor,
    ],
    () => {
      // 通过 resize 统一处理：重设画布尺寸 + 重算 density + initParticles
      resize();
    }
  );
});

onUnmounted(() => {
  window.removeEventListener('resize', resize);
  if (animationFrame) cancelAnimationFrame(animationFrame);
});
</script>

<style scoped>
.particle-canvas {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}
</style>
