import './assets/main.css'
import { createApp } from 'vue'
import { MotionPlugin } from '@vueuse/motion'
import App from './App.vue'
import router from './router/index.js'

createApp(App).use(router).use(MotionPlugin).mount('#app')
