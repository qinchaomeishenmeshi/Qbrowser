import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘', icon: 'Monitor' }
  },
  {
    path: '/browsers',
    name: 'Browsers',
    component: () => import('@/views/BrowserList.vue'),
    meta: { title: '浏览器管理', icon: 'Chrome' }
  },
  {
    path: '/extensions',
    name: 'Extensions',
    component: () => import('@/views/Extensions.vue'),
    meta: { title: '扩展管理', icon: 'Puzzle' }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/Logs.vue'),
    meta: { title: '系统日志', icon: 'Document' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置', icon: 'Setting' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：更新页面标题
router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || '清简浏览器'} - 清简浏览器`
  next()
})

export default router
