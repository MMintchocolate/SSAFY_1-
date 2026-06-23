import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ── Blank layout (NavBar 없음) ──────────────────────────────────
    {
      path: '/',
      component: () => import('@/views/LandingView.vue'),
      meta: { layout: 'blank' },
    },
    {
      path: '/login',
      component: () => import('@/views/LoginView.vue'),
      meta: { layout: 'blank' },
    },
    {
      path: '/register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { layout: 'blank' },
    },

    // ── App layout (NavBar 포함, AppLayout 이 RouterView 를 감쌈) ───
    {
      path: '/app',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { layout: 'app' },
      children: [
        { path: '',             redirect: 'home' },
        { path: 'home',         component: () => import('@/views/HomeView.vue') },
        { path: 'products',     component: () => import('@/views/ProductsView.vue') },
        { path: 'branches',     component: () => import('@/views/BranchesView.vue') },
        { path: 'stocks',       component: () => import('@/views/StocksView.vue') },
        { path: 'gold',         component: () => import('@/views/GoldView.vue') },
        { path: 'dataset',      component: () => import('@/views/DatasetView.vue') },
        { path: 'news',         component: () => import('@/views/NewsView.vue') },
        { path: 'community',    component: () => import('@/views/CommunityView.vue') },
        // ── 인증 필요 ──────────────────────────────────────────────
        { path: 'receipts',     component: () => import('@/views/ReceiptsView.vue'),      meta: { requiresAuth: true } },
        { path: 'voicephishing',component: () => import('@/views/VoicePhishingView.vue'), meta: { requiresAuth: true } },
        { path: 'spending',     component: () => import('@/views/SpendingView.vue'),      meta: { requiresAuth: true } },
        { path: 'notify-sim',   component: () => import('@/views/NotifySimView.vue'),     meta: { requiresAuth: true } },
        { path: 'indicators',   component: () => import('@/views/IndicatorsView.vue'),    meta: { requiresAuth: true } },
        { path: 'mypage',       component: () => import('@/views/MyPageView.vue'),        meta: { requiresAuth: true } },
      ],
    },

    // ── 하위 호환 리다이렉트 (기존 경로 → /app/*) ──────────────────
    { path: '/home',          redirect: '/app/home' },
    { path: '/products',      redirect: '/app/products' },
    { path: '/branches',      redirect: '/app/branches' },
    { path: '/receipts',      redirect: '/app/receipts' },
    { path: '/voicephishing', redirect: '/app/voicephishing' },
    { path: '/spending',      redirect: '/app/spending' },
    { path: '/notify-sim',    redirect: '/app/notify-sim' },
    { path: '/stocks',        redirect: '/app/stocks' },
    { path: '/gold',          redirect: '/app/gold' },
    { path: '/dataset',       redirect: '/app/dataset' },
    { path: '/indicators',    redirect: '/app/indicators' },
    { path: '/news',          redirect: '/app/news' },
    { path: '/community',     redirect: '/app/community' },
    { path: '/mypage',        redirect: '/app/mypage' },
  ],

  scrollBehavior: () => ({ top: 0, behavior: 'smooth' }),
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access')
  if (to.meta.requiresAuth && !token) return '/login'
})

export default router
