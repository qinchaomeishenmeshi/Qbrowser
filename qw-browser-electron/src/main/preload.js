const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的API到渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 应用信息
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  
  // 后端服务控制
  backend: {
    start: () => ipcRenderer.invoke('backend-start'),
    stop: () => ipcRenderer.invoke('backend-stop'),
    restart: () => ipcRenderer.invoke('backend-restart'),
    checkHealth: () => ipcRenderer.invoke('backend-health'),
    
    // 监听后端状态变化
    onStatusChange: (callback) => {
      const handler = (event, data) => callback(data);
      ipcRenderer.on('backend-status', handler);
      return () => ipcRenderer.removeListener('backend-status', handler);
    },
    
    // 监听后端日志
    onLog: (callback) => {
      const handler = (event, data) => callback(data);
      ipcRenderer.on('backend-log', handler);
      return () => ipcRenderer.removeListener('backend-log', handler);
    }
  },
  
  // 文件系统操作
  fs: {
    showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
    showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
    showItemInFolder: (fullPath) => ipcRenderer.invoke('show-item-in-folder', fullPath),
    getPath: (name) => ipcRenderer.invoke('get-path', name)
  },
  
  // 外部链接
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // 日志操作
  logs: {
    get: (options) => ipcRenderer.invoke('get-logs', options),
    clear: (days) => ipcRenderer.invoke('clear-logs', days)
  },
  
  // 导航事件监听
  onNavigate: (callback) => {
    const handler = (event, route) => callback(route);
    ipcRenderer.on('navigate-to', handler);
    return () => ipcRenderer.removeListener('navigate-to', handler);
  },
  
  // 通用事件监听器
  on: (channel, callback) => {
    const validChannels = [
      'backend-status',
      'backend-log',
      'navigate-to',
      'app-update-available',
      'app-update-downloaded',
      'app-error'
    ];
    
    if (validChannels.includes(channel)) {
      const handler = (event, ...args) => callback(...args);
      ipcRenderer.on(channel, handler);
      return () => ipcRenderer.removeListener(channel, handler);
    } else {
      console.warn(`Invalid channel: ${channel}`);
      return () => {};
    }
  },
  
  // 移除事件监听器
  removeAllListeners: (channel) => {
    const validChannels = [
      'backend-status',
      'backend-log',
      'navigate-to',
      'app-update-available',
      'app-update-downloaded',
      'app-error'
    ];
    
    if (validChannels.includes(channel)) {
      ipcRenderer.removeAllListeners(channel);
    }
  },
  
  // 平台信息
  platform: process.platform,
  
  // 版本信息
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});

// 暴露Node.js环境变量（仅开发环境）
if (process.env.NODE_ENV === 'development') {
  contextBridge.exposeInMainWorld('nodeAPI', {
    env: process.env,
    platform: process.platform,
    arch: process.arch,
    versions: process.versions
  });
}

// 错误处理
window.addEventListener('DOMContentLoaded', () => {
  // 监听未捕获的错误
  window.addEventListener('error', (event) => {
    console.error('渲染进程错误:', event.error);
    // 可以发送错误信息到主进程
    // ipcRenderer.send('renderer-error', {
    //   message: event.error.message,
    //   stack: event.error.stack,
    //   filename: event.filename,
    //   lineno: event.lineno,
    //   colno: event.colno
    // });
  });
  
  // 监听未处理的Promise拒绝
  window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason);
    // 可以发送错误信息到主进程
    // ipcRenderer.send('renderer-promise-rejection', {
    //   reason: event.reason,
    //   promise: event.promise
    // });
  });
});

// 开发环境下的调试工具
if (process.env.NODE_ENV === 'development') {
  // 暴露调试API
  contextBridge.exposeInMainWorld('debugAPI', {
    log: (...args) => console.log('[Debug]', ...args),
    warn: (...args) => console.warn('[Debug]', ...args),
    error: (...args) => console.error('[Debug]', ...args),
    
    // 获取渲染进程内存使用情况
    getMemoryUsage: () => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    },
    
    // 性能标记
    mark: (name) => performance.mark(name),
    measure: (name, startMark, endMark) => performance.measure(name, startMark, endMark),
    getEntriesByType: (type) => performance.getEntriesByType(type),
    
    // 清理性能数据
    clearMarks: (name) => performance.clearMarks(name),
    clearMeasures: (name) => performance.clearMeasures(name)
  });
}