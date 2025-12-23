// frontend_vue/src/composables/useTheme.js
import { ref } from 'vue'

const STORAGE_KEY = 'tfg_theme' // 'dark' | 'light'
const theme = ref('dark')       // 全局单例主题状态

function getSystemTheme() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches
    ? 'light'
    : 'dark'
}

function applyTheme(t) {
  const html = document.documentElement
  // 约定：默认暗色；日间模式时挂 .light
  if (t === 'light') html.classList.add('light')
  else html.classList.remove('light')
}

export function useTheme() {
  const initTheme = () => {
    const saved = localStorage.getItem(STORAGE_KEY)
    theme.value = saved === 'light' || saved === 'dark' ? saved : getSystemTheme()
    applyTheme(theme.value)
  }

  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem(STORAGE_KEY, theme.value)
    applyTheme(theme.value)
  }

  const setTheme = (t) => {
    theme.value = t === 'light' ? 'light' : 'dark'
    localStorage.setItem(STORAGE_KEY, theme.value)
    applyTheme(theme.value)
  }

  return { theme, initTheme, toggleTheme, setTheme }
}
