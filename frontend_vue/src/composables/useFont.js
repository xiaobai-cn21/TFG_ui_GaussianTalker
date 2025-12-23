import { ref } from 'vue'
import { fonts } from '../fonts/fonts'

const STORAGE_KEY = 'tfg_font'
const font = ref('inter') // 默认值可按你需求设为 system/inter

function applyFont(name) {
  const html = document.documentElement

  // 先移除所有字体 class（避免叠加）
  Object.values(fonts).forEach(f => html.classList.remove(f.className))

  // 再添加当前字体 class
  const target = fonts[name] || fonts.inter
  html.classList.add(target.className)
}

export function useFont() {
  const initFont = () => {
    const saved = localStorage.getItem(STORAGE_KEY)
    font.value = saved && fonts[saved] ? saved : 'inter'
    applyFont(font.value)
  }

  const setFont = (name) => {
    font.value = fonts[name] ? name : 'inter'
    localStorage.setItem(STORAGE_KEY, font.value)
    applyFont(font.value)
  }

  return { font, initFont, setFont }
}
