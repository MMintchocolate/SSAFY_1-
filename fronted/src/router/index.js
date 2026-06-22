import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',              component: () => import('@/views/HomeView.vue') },
    { path: '/products',      component: () => import('@/views/ProductsView.vue') },
    { path: '/branches',      component: () => import('@/views/BranchesView.vue') },
    { path: '/receipts',      component: () => import('@/views/ReceiptsView.vue'),      meta: { requiresAuth: true } },
    { path: '/voicephishing', component: () => import('@/views/VoicePhishingView.vue'), meta: { requiresAuth: true } },
    { path: '/spending',      component: () => import('@/views/SpendingView.vue'),      meta: { requiresAuth: true } },
    { path: '/notify-sim',   component: () => import('@/views/NotifySimView.vue'),     meta: { requiresAuth: true } },
    { path: '/stocks',        component: () => import('@/views/StocksView.vue') },
    { path: '/indicators',    component: () => import('@/views/IndicatorsView.vue'), meta: { requiresAuth: true } },
    { path: '/news',          component: () => import('@/views/NewsView.vue') },
    { path: '/community',     component: () => import('@/views/CommunityView.vue') },
    { path: '/mypage',        component: () => import('@/views/MyPageView.vue'), meta: { requiresAuth: true } },
    { path: '/login',         component: () => import('@/views/LoginView.vue') },
    { path: '/register',      component: () => import('@/views/RegisterView.vue') },
  ],
  scrollBehavior: () => ({ top: 0, behavior: 'smooth' }),
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access')
  if (to.meta.requiresAuth && !token) return '/login'
})

export default router
