import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import './styles/global.css';

// 创建Vue应用实例
const app = createApp(App);

// 使用Pinia状态管理
const pinia = createPinia();
app.use(pinia);

// 使用路由
app.use(router);

// 全局属性
app.config.globalProperties.$electronAPI = window.electronAPI;
app.config.globalProperties.$httpAPI = window.httpAPI;
app.config.globalProperties.$utils = window.utils;

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue错误:', err, info);
  if (window.electronAPI && window.electronAPI.log) {
    window.electronAPI.log.error(`Vue错误: ${err.message} - ${info}`);
  }
};

// 挂载应用
app.mount('#app');

// 隐藏加载页面
const loadingElement = document.getElementById('loading');
if (loadingElement) {
  setTimeout(() => {
    loadingElement.style.opacity = '0';
    setTimeout(() => {
      loadingElement.style.display = 'none';
    }, 300);
  }, 1000);
}

// 开发环境下的调试信息
if (import.meta.env.DEV) {
  console.log('应用运行在开发模式');
  console.log('Electron API:', window.electronAPI);
  console.log('HTTP API:', window.httpAPI);
}