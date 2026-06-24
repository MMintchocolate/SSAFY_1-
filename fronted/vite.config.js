import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  envDir: '../backend',
  plugins: [
    vue(),
    tailwindcss(),
    vueDevTools({ launchEditor: false }),
    basicSsl(),
  ],
  server: {
    host: true,
    https: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_WS_TARGET || 'ws://localhost:8002',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
