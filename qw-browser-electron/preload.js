const { contextBridge, ipcRenderer } = require('electron');

// 向渲染进程暴露安全的API
contextBridge.exposeInMainWorld('electronAPI', {
  // 后端状态管理
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  restartBackend: () => ipcRenderer.invoke('restart-backend'),
  
  // 系统信息
  platform: process.platform,
  
  // 窗口控制
  minimize: () => ipcRenderer.invoke('window-minimize'),
  maximize: () => ipcRenderer.invoke('window-maximize'),
  close: () => ipcRenderer.invoke('window-close'),
  
  // 文件系统操作（如果需要）
  selectFile: (options) => ipcRenderer.invoke('dialog-open-file', options),
  selectDirectory: (options) => ipcRenderer.invoke('dialog-open-directory', options),
  
  // 通知系统
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', { title, body }),
  
  // 应用信息
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // 开发者工具
  openDevTools: () => ipcRenderer.invoke('open-dev-tools'),
  
  // 事件监听
  onBackendStatusChange: (callback) => {
    ipcRenderer.on('backend-status-changed', callback);
    return () => ipcRenderer.removeListener('backend-status-changed', callback);
  },
  
  // 日志记录
  log: {
    info: (message) => ipcRenderer.invoke('log', { level: 'info', message }),
    warn: (message) => ipcRenderer.invoke('log', { level: 'warn', message }),
    error: (message) => ipcRenderer.invoke('log', { level: 'error', message })
  }
});

// HTTP请求封装（用于与Python后端通信）
const httpAPI = {
  // 基础请求方法
  request: async (url, options = {}) => {
    const baseUrl = 'http://localhost:6001'; // 修正为正确的后端端口
    const fullUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;
    
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options
    };
    
    try {
      const response = await fetch(fullUrl, defaultOptions);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text();
      }
    } catch (error) {
      console.error('HTTP请求失败:', error);
      throw error;
    }
  }
};

// 添加便捷方法
httpAPI.get = (url, options = {}) => {
  return httpAPI.request(url, { ...options, method: 'GET' });
};

httpAPI.post = (url, data, options = {}) => {
  return httpAPI.request(url, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data)
  });
};

httpAPI.put = (url, data, options = {}) => {
  return httpAPI.request(url, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data)
  });
};

httpAPI.delete = (url, options = {}) => {
  return httpAPI.request(url, { ...options, method: 'DELETE' });
};

contextBridge.exposeInMainWorld('httpAPI', httpAPI);

// 工具函数
contextBridge.exposeInMainWorld('utils', {
  // 格式化日期
  formatDate: (date, format = 'YYYY-MM-DD HH:mm:ss') => {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds);
  },
  
  // 深拷贝
  deepClone: (obj) => JSON.parse(JSON.stringify(obj)),
  
  // 防抖
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },
  
  // 节流
  throttle: (func, limit) => {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
});

// 在窗口加载完成后执行初始化
window.addEventListener('DOMContentLoaded', () => {
  console.log('Electron preload script loaded');
  
  // 检查后端状态（确保API已经暴露）
  if (window.electronAPI && window.electronAPI.getBackendStatus) {
    window.electronAPI.getBackendStatus().then(status => {
      console.log('后端状态:', status);
    }).catch(error => {
      console.error('获取后端状态失败:', error);
    });
  } else {
    console.warn('electronAPI.getBackendStatus 方法不可用');
  }
});