const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const isDev = !app.isPackaged;

let mainWindow;
let pythonProcess;

// Python后端进程管理
class PythonBackend {
  constructor() {
    this.process = null;
    this.isRunning = false;
  }

  start() {
    return new Promise((resolve, reject) => {
      // Python后端启动路径（相对于原项目）
      const pythonScript = path.join(__dirname, '../app.py');

      console.log('启动Python后端:', pythonScript);

      this.process = spawn('python3', [pythonScript], {
        cwd: path.join(__dirname, '../'),
        stdio: ['pipe', 'pipe', 'pipe']
      });

      this.process.stdout.on('data', (data) => {
        console.log(`Python后端输出: ${data}`);
        // 检测FastAPI服务启动成功
        if (data.toString().includes('Uvicorn running on')) {
          this.isRunning = true;
          resolve();
        }
      });

      this.process.stderr.on('data', (data) => {
        console.error(`Python后端错误: ${data}`);
        // 也检测stderr中的启动成功信息
        if (data.toString().includes('Uvicorn running on')) {
          this.isRunning = true;
          resolve();
        }
      });

      this.process.on('close', (code) => {
        console.log(`Python后端进程退出，代码: ${code}`);
        this.isRunning = false;
      });

      this.process.on('error', (err) => {
        console.error('Python后端启动失败:', err);
        reject(err);
      });

      // 设置超时
      setTimeout(() => {
        if (!this.isRunning) {
          reject(new Error('Python后端启动超时'));
        }
      }, 10000);
    });
  }

  stop() {
    if (this.process && this.isRunning) {
      this.process.kill();
      this.isRunning = false;
    }
  }
}

const pythonBackend = new PythonBackend();

function createWindow() {
  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: '全网直播浏览器',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets/icon.png'), // 可选：应用图标
    titleBarStyle: 'default',
    show: false // 先隐藏，等加载完成后显示
  });

  // 加载应用
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile('dist/index.html');
  }

  // 窗口准备好后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // 窗口关闭事件
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// 应用准备就绪
app.whenReady().then(async () => {
  try {
    console.log('启动Python后端服务...');
    await pythonBackend.start();
    console.log('Python后端启动成功');

    createWindow();
  } catch (error) {
    console.error('Python后端启动失败:', error);
    // 可以选择继续启动前端或退出应用
    createWindow();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// 所有窗口关闭时退出应用（macOS除外）
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    pythonBackend.stop();
    app.quit();
  }
});

// 应用退出前清理
app.on('before-quit', () => {
  pythonBackend.stop();
});

// IPC通信处理
ipcMain.handle('get-backend-status', () => {
  return {
    isRunning: pythonBackend.isRunning,
    baseUrl: 'http://localhost:8000'
  };
});

ipcMain.handle('restart-backend', async () => {
  try {
    pythonBackend.stop();
    await new Promise(resolve => setTimeout(resolve, 2000)); // 等待2秒
    await pythonBackend.start();
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 日志处理
ipcMain.handle('log', (event, { level, message }) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

  switch (level) {
    case 'error':
      console.error(logMessage);
      break;
    case 'warn':
      console.warn(logMessage);
      break;
    case 'info':
    default:
      console.log(logMessage);
      break;
  }

  return { success: true };
});

// 窗口控制
ipcMain.handle('window-minimize', () => {
  if (mainWindow) {
    mainWindow.minimize();
  }
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.handle('window-close', () => {
  if (mainWindow) {
    mainWindow.close();
  }
});

// 应用信息
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

// 开发者工具
ipcMain.handle('open-dev-tools', () => {
  if (mainWindow) {
    mainWindow.webContents.openDevTools();
  }
});

// 处理应用协议（可选，用于深度链接）
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('qw-browser', process.execPath, [path.resolve(process.argv[1])]);
  }
} else {
  app.setAsDefaultProtocolClient('qw-browser');
}