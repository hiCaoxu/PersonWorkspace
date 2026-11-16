import { createRouter, createWebHistory } from 'vue-router'

import { useSessionStore } from '@/stores/session'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: (to, _from, saved) => (saved ?? { top: 0 }),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '首页' },
    },
    {
      path: '/todos',
      name: 'todos',
      component: () => import('@/views/Todos.vue'),
      meta: { title: '待办' },
    },
    {
      path: '/diary',
      name: 'diary',
      component: () => import('@/views/Diary.vue'),
      meta: { title: '日记' },
    },
    {
      path: '/notes',
      name: 'notes',
      component: () => import('@/views/Notes.vue'),
      meta: { title: '笔记' },
    },
    {
      path: '/health',
      name: 'health',
      component: () => import('@/views/Health.vue'),
      meta: { title: '健康' },
    },
    {
      path: '/entertainment',
      name: 'entertainment',
      component: () => import('@/views/Entertainment.vue'),
      meta: { title: '娱乐' },
    },
    {
      path: '/finance',
      name: 'finance',
      component: () => import('@/views/Finance.vue'),
      meta: { title: '记账' },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/Profile.vue'),
      meta: { title: '档案' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录', public: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFound.vue'),
      meta: { title: '页面不存在', public: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const session = useSessionStore()
  if (!session.checked) {
    await session.fetchMe()
  }

  if (to.meta.public) {
    return session.authed && to.name === 'login' ? { path: '/' } : true
  }

  if (!session.authed) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  return true
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} · 个人工作台` : '个人工作台'
})

export default router
