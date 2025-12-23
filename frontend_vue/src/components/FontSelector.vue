<template>
  <!-- 字体选择：紧凑横向控件，风格与 ThemeToggle 一致 -->
  <div class="font-selector">
    <span class="label">Font</span>

    <!-- 使用 select 保持原生稳定性；样式做成“胶囊”风格 -->
    <select class="select" :value="font" @change="onChange" aria-label="选择字体">
      <option v-for="(item, key) in fonts" :key="key" :value="key">
        {{ item.label }}
      </option>
    </select>
  </div>
</template>

<script setup>
import { fonts } from '../fonts/fonts'
import { useFont } from '../composables/useFont'

const { font, setFont } = useFont()

/** 切换字体：写入 localStorage 并即时应用到 html class */
const onChange = (e) => {
  setFont(e.target.value)
}
</script>

<style scoped>
.font-selector {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--fg);
}

.label {
  font-size: 12px;
  opacity: 0.85;
  user-select: none;
}

/* select 做成透明，保持与胶囊一致 */
.select {
  background: transparent;
  border: none;
  color: inherit;
  font-size: 12px;
  outline: none;
  cursor: pointer;
  padding: 0;
}

/* 下拉选项在不同浏览器外观不同，这是原生限制；不影响整体风格 */
.select option {
  color: #111;
}
</style>
