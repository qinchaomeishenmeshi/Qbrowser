const { app, BrowserWindow, ipcMain, dialog, shell, Menu, Tray, nativeImage } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const os = require('os');

// 开发环境检测
const isDev = process.env.NODE_ENV === 'development';

// 全局变量
let mainWindow = null;
let backendProcess = null;
let tray = null;
let isQuitting = false;

// 应用配置
const config = {
  window: {
    width: 1200,
    height: 800,
    minWidth: 1000,
    minHeight: 600
  },
  backend: {
    port: 8000,
    host: 'localhost',
    executable: isDev ? 'python' : path.join(process.resourcesPath, 'backend', 'main.py'),
    args: isDev ? [path.join(__dirname, '../../backend/main.py')] : [],
    maxRetries: 3,
    retryDelay: 2000
  },
  paths: {
    userData: app.getPath('userData'),
    logs: path.join(app.getPath('userData'), 'logs'),
    config: path.join(app.getPath('userData'), 'config.json'),
    backend: isDev ? path.join(__dirname, '../../backend') : path.join(process.resourcesPath, 'backend')
  }
};

// 确保必要目录存在
function ensureDirectories() {
  const dirs = [config.paths.logs];
  dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

// 日志记录
function log(level, message, data = null) {
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    level,
    message,
    data,
    pid: process.pid
  };
  
  console.log(`[${timestamp}] [${level.toUpperCase()}] ${message}`, data || '');
  
  // 写入日志文件
  const logFile = path.join(config.paths.logs, `app-${new Date().toISOString().split('T')[0]}.log`);
  fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
}

// 创建主窗口
function createMainWindow() {
  log('info', '创建主窗口');
  
  mainWindow = new BrowserWindow({
    width: config.window.width,
    height: config.window.height,
    minWidth: config.window.minWidth,
    minHeight: config.window.minHeight,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: !isDev
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    show: false, // 先隐藏，加载完成后显示
    backgroundColor: '#1a1a1a'
  });

  // 加载应用
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  // 窗口事件
  mainWindow.once('ready-to-show', () => {
    log('info', '主窗口准备显示');
    mainWindow.show();
    
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  mainWindow.on('closed', () => {
    log('info', '主窗口关闭');
    mainWindow = null;
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting && process.platform === 'darwin') {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  // 处理外部链接
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  return mainWindow;
}

// 创建系统托盘
function createTray() {
  if (tray) return;
  
  log('info', '创建系统托盘');
  
  const iconPath = path.join(__dirname, '../assets/tray-icon.png');
  const icon = nativeImage.createFromPath(iconPath);
  
  tray = new Tray(icon.resize({ width: 16, height: 16 }));
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示窗口',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        } else {
          createMainWindow();
        }
      }
    },
    {
      label: '后端状态',
      submenu: [
        {
          label: '启动后端',
          click: () => startBackend()
        },
        {
          label: '停止后端',
          click: () => stopBackend()
        },
        {
          label: '重启后端',
          click: () => restartBackend()
        }
      ]
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);
  
  tray.setContextMenu(contextMenu);
  tray.setToolTip('QW Browser Manager');
  
  tray.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    } else {
      createMainWindow();
    }
  });
}

// 启动后端服务
function startBackend() {
  return new Promise((resolve, reject) => {
    if (backendProcess) {
      log('warn', '后端进程已存在');
      resolve(backendProcess);
      return;
    }

    log('info', '启动后端服务', { executable: config.backend.executable, args: config.backend.args });

    try {
      backendProcess = spawn(config.backend.executable, config.backend.args, {
        cwd: config.paths.backend,
        env: {
          ...process.env,
          PORT: config.backend.port,
          HOST: config.backend.host,
          NODE_ENV: isDev ? 'development' : 'production'
        },
        stdio: ['pipe', 'pipe', 'pipe']
      });

      // 处理后端输出
      backendProcess.stdout.on('data', (data) => {
        const output = data.toString().trim();
        if (output) {
          log('info', `[Backend] ${output}`);
          // 发送到渲染进程
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('backend-log', { type: 'stdout', data: output });
          }
        }
      });

      backendProcess.stderr.on('data', (data) => {
        const output = data.toString().trim();
        if (output) {
          log('error', `[Backend Error] ${output}`);
          // 发送到渲染进程
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('backend-log', { type: 'stderr', data: output });
          }
        }
      });

      backendProcess.on('close', (code) => {
        log('info', `后端进程退出，代码: ${code}`);
        backendProcess = null;
        
        // 通知渲染进程
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('backend-status', { status: 'stopped', code });
        }
        
        // 如果不是正常退出且应用仍在运行，尝试重启
        if (code !== 0 && !isQuitting) {
          log('warn', '后端异常退出，尝试重启');
          setTimeout(() => {
            if (!isQuitting) {
              startBackend();
            }
          }, config.backend.retryDelay);
        }
      });

      backendProcess.on('error', (error) => {
        log('error', '后端进程启动失败', error);
        backendProcess = null;
        reject(error);
      });

      // 等待后端启动
      setTimeout(() => {
        if (backendProcess && !backendProcess.killed) {
          log('info', '后端服务启动成功');
          // 通知渲染进程
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('backend-status', { status: 'running', pid: backendProcess.pid });
          }
          resolve(backendProcess);
        } else {
          reject(new Error('后端启动超时'));
        }
      }, 3000);

    } catch (error) {
      log('error', '启动后端服务失败', error);
      reject(error);
    }
  });
}

// 停止后端服务
function stopBackend() {
  return new Promise((resolve) => {
    if (!backendProcess) {
      log('info', '后端进程不存在');
      resolve();
      return;
    }

    log('info', '停止后端服务');

    const timeout = setTimeout(() => {
      if (backendProcess && !backendProcess.killed) {
        log('warn', '强制终止后端进程');
        backendProcess.kill('SIGKILL');
      }
    }, 5000);

    backendProcess.on('close', () => {
      clearTimeout(timeout);
      backendProcess = null;
      log('info', '后端服务已停止');
      resolve();
    });

    // 优雅关闭
    backendProcess.kill('SIGTERM');
  });
}

// 重启后端服务
async function restartBackend() {
  log('info', '重启后端服务');
  await stopBackend();
  await new Promise(resolve => setTimeout(resolve, 1000));
  return startBackend();
}

// 检查后端健康状态
async function checkBackendHealth() {
  try {
    const response = await fetch(`http://${config.backend.host}:${config.backend.port}/api/health`);
    return response.ok;
  } catch (error) {
    return false;
  }
}

// 创建应用菜单
function createMenu() {
  const template = [
    {
      label: 'QW Browser',
      submenu: [
        { label: '关于 QW Browser', role: 'about' },
        { type: 'separator' },
        { label: '偏好设置', accelerator: 'CmdOrCtrl+,', click: () => {
          if (mainWindow) {
            mainWindow.webContents.send('navigate-to', '/settings');
          }
        }},
        { type: 'separator' },
        { label: '隐藏 QW Browser', accelerator: 'CmdOrCtrl+H', role: 'hide' },
        { label: '隐藏其他', accelerator: 'CmdOrCtrl+Shift+H', role: 'hideothers' },
        { label: '显示全部', role: 'unhide' },
        { type: 'separator' },
        { label: '退出', accelerator: 'CmdOrCtrl+Q', click: () => {
          isQuitting = true;
          app.quit();
        }}
      ]
    },
    {
      label: '编辑',
      submenu: [
        { label: '撤销', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
        { label: '重做', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
        { type: 'separator' },
        { label: '剪切', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: '复制', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: '粘贴', accelerator: 'CmdOrCtrl+V', role: 'paste' },
        { label: '全选', accelerator: 'CmdOrCtrl+A', role: 'selectall' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { label: '重新加载', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { label: '强制重新加载', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
        { label: '切换开发者工具', accelerator: 'F12', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: '实际大小', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
        { label: '放大', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
        { label: '缩小', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
        { type: 'separator' },
        { label: '切换全屏', accelerator: 'F11', role: 'togglefullscreen' }
      ]
    },
    {
      label: '窗口',
      submenu: [
        { label: '最小化', accelerator: 'CmdOrCtrl+M', role: 'minimize' },
        { label: '关闭', accelerator: 'CmdOrCtrl+W', role: 'close' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '了解更多',
          click: () => {
            shell.openExternal('https://github.com/your-repo/qw-browser');
          }
        },
        {
          label: '报告问题',
          click: () => {
            shell.openExternal('https://github.com/your-repo/qw-browser/issues');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC 事件处理
function setupIPC() {
  // 获取应用信息
  ipcMain.handle('get-app-info', () => {
    return {
      name: app.getName(),
      version: app.getVersion(),
      platform: process.platform,
      arch: process.arch,
      electronVersion: process.versions.electron,
      nodeVersion: process.versions.node,
      chromeVersion: process.versions.chrome
    };
  });

  // 获取系统信息
  ipcMain.handle('get-system-info', () => {
    return {
      platform: os.platform(),
      arch: os.arch(),
      release: os.release(),
      hostname: os.hostname(),
      cpus: os.cpus().length,
      memory: {
        total: os.totalmem(),
        free: os.freemem(),
        used: os.totalmem() - os.freemem()
      },
      uptime: os.uptime()
    };
  });

  // 后端控制
  ipcMain.handle('backend-start', async () => {
    try {
      await startBackend();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('backend-stop', async () => {
    try {
      await stopBackend();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('backend-restart', async () => {
    try {
      await restartBackend();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('backend-health', async () => {
    return await checkBackendHealth();
  });

  // 文件操作
  ipcMain.handle('show-open-dialog', async (event, options) => {
    const result = await dialog.showOpenDialog(mainWindow, options);
    return result;
  });

  ipcMain.handle('show-save-dialog', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, options);
    return result;
  });

  // 打开外部链接
  ipcMain.handle('open-external', async (event, url) => {
    await shell.openExternal(url);
  });

  // 显示文件夹
  ipcMain.handle('show-item-in-folder', async (event, fullPath) => {
    shell.showItemInFolder(fullPath);
  });

  // 获取路径
  ipcMain.handle('get-path', async (event, name) => {
    return app.getPath(name);
  });

  // 日志操作
  ipcMain.handle('get-logs', async (event, options = {}) => {
    const { date, level, limit = 100 } = options;
    const logFile = path.join(config.paths.logs, `app-${date || new Date().toISOString().split('T')[0]}.log`);
    
    try {
      if (!fs.existsSync(logFile)) {
        return [];
      }
      
      const content = fs.readFileSync(logFile, 'utf8');
      const lines = content.trim().split('\n').filter(line => line);
      
      let logs = lines.map(line => {
        try {
          return JSON.parse(line);
        } catch (e) {
          return null;
        }
      }).filter(log => log);
      
      if (level) {
        logs = logs.filter(log => log.level === level);
      }
      
      return logs.slice(-limit);
    } catch (error) {
      log('error', '读取日志失败', error);
      return [];
    }
  });

  // 清理日志
  ipcMain.handle('clear-logs', async (event, days = 7) => {
    try {
      const files = fs.readdirSync(config.paths.logs);
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - days);
      
      let deletedCount = 0;
      
      files.forEach(file => {
        if (file.startsWith('app-') && file.endsWith('.log')) {
          const filePath = path.join(config.paths.logs, file);
          const stats = fs.statSync(filePath);
          
          if (stats.mtime < cutoff) {
            fs.unlinkSync(filePath);
            deletedCount++;
          }
        }
      });
      
      log('info', `清理了 ${deletedCount} 个日志文件`);
      return { success: true, deletedCount };
    } catch (error) {
      log('error', '清理日志失败', error);
      return { success: false, error: error.message };
    }
  });
}

// 应用事件处理
app.whenReady().then(async () => {
  log('info', 'Electron 应用启动');
  
  // 确保目录存在
  ensureDirectories();
  
  // 创建主窗口
  createMainWindow();
  
  // 创建菜单
  createMenu();
  
  // 创建系统托盘
  createTray();
  
  // 设置IPC
  setupIPC();
  
  // 启动后端服务
  try {
    await startBackend();
  } catch (error) {
    log('error', '启动后端服务失败', error);
    
    // 显示错误对话框
    dialog.showErrorBox(
      '启动失败',
      `无法启动后端服务：${error.message}\n\n请检查Python环境是否正确安装。`
    );
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    isQuitting = true;
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  } else if (mainWindow) {
    mainWindow.show();
  }
});

app.on('before-quit', async (event) => {
  if (!isQuitting) {
    event.preventDefault();
    isQuitting = true;
    
    log('info', '应用准备退出');
    
    // 停止后端服务
    if (backendProcess) {
      await stopBackend();
    }
    
    // 销毁托盘
    if (tray) {
      tray.destroy();
      tray = null;
    }
    
    app.quit();
  }
});

// 处理未捕获的异常
process.on('uncaughtException', (error) => {
  log('error', '未捕获的异常', error);
});

process.on('unhandledRejection', (reason, promise) => {
  log('error', '未处理的Promise拒绝', { reason, promise });
});

// 导出配置供其他模块使用
module.exports = { config, log };