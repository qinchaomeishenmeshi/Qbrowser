import { createRouter, createWebHistory } from 'vue-router';

// 路由组件懒加载
const Dashboard = () => import('@/views/Dashboard.vue');
const BrowserManager = () => import('@/views/BrowserManager.vue');
const Scheduler = () => import('@/views/Scheduler.vue');
const Extensions = () => import('@/views/Extensions.vue');
const Settings = () => import('@/views/Settings.vue');

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: '仪表盘',
      icon: 'dashboard'
    }
  },
  {
    path: '/browser',
    name: 'BrowserManager',
    component: BrowserManager,
    meta: {
      title: '浏览器管理',
      icon: 'browser'
    }
  },
  {
    path: '/scheduler',
    name: 'Scheduler',
    component: Scheduler,
    meta: {
      title: '定时任务',
      icon: 'schedule'
    }
  },
  {
    path: '/extensions',
    name: 'Extensions',
    component: Extensions,
    meta: {
      title: '扩展管理',
      icon: 'extension'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置',
      icon: 'settings'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 全网直播浏览器`;
  }

  // 检查后端状态（可选）
  if (window.electronAPI) {
    window.electronAPI.getBackendStatus().then(status => {
      if (!status.isRunning && to.name !== 'Settings') {
        console.warn('后端服务未运行，某些功能可能不可用');
      }
    }).catch(error => {
      console.error('检查后端状态失败:', error);
    });
  }

  next();
});

router.afterEach((to, from) => {
  // 路由切换后的处理
  console.log(`路由从 ${from.path} 切换到 ${to.path}`);
});

export default router;