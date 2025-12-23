import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: '../',                 // 输出到项目根
    emptyOutDir: false,
    rollupOptions: {
      input: {
        index: path.resolve(__dirname, 'index.html'),
        chat_system: path.resolve(__dirname, 'chat_system.html'),
        model_training: path.resolve(__dirname, 'model_training.html'),
        video_generation: path.resolve(__dirname, 'video_generation.html'),
      },
      output: {
        entryFileNames: 'static/js/[name].js',
        chunkFileNames: 'static/js/[name]-[hash].js',
        assetFileNames: assetInfo => {
          if (assetInfo.name.endsWith('.css')) {
            return 'static/css/[name].[ext]'
          }
          return 'static/assets/[name].[ext]'
        },
        dir: path.resolve(__dirname, '../'),
      }
    }
  },
  base: '/'
})
