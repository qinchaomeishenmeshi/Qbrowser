# 全网直播浏览器 - Electron 客户端

这是一个基于 Electron + Vue 3 + Vite 构建的桌面应用程序，用于短视频内容的生产和管理。

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

```bash
npm install
```

### 开发模式

#### 方式一：分步启动（推荐用于调试）

1. 启动 Vite 开发服务器：
```bash
npm run dev
```

2. 在另一个终端启动 Electron：
```bash
npm run electron
```

#### 方式二：一键启动

```bash
npm run electron:dev
```

这个命令会同时启动 Vite 开发服务器和 Electron 应用。

### 构建和打包

#### 构建 Web 资源

```bash
npm run build
```

#### 打包 Electron 应用

```bash
npm run electron:pack
```

## 📁 项目结构

```
qw-browser-electron/
├── src/
│   ├── main/              # Electron 主进程
│   │   ├── main.js         # 主进程入口
│   │   └── preload.js      # 预加载脚本
│   ├── components/         # Vue 组件
│   ├── views/             # 页面视图
│   ├── store/             # Pinia 状态管理
│   ├── router/            # Vue Router 路由
│   ├── api/               # API 接口
│   ├── utils/             # 工具函数
│   ├── styles/            # 样式文件
│   ├── assets/            # 静态资源
│   ├── App.vue            # 根组件
│   └── main.js            # 渲染进程入口
├── main.js                # Electron 主进程入口
├── preload.js             # 预加载脚本
├── index.html             # HTML 模板
├── vite.config.js         # Vite 配置
└── package.json           # 项目配置
```

## 🔧 开发说明

### 技术栈

- **Electron**: 桌面应用框架
- **Vue 3**: 前端框架（使用 Options API）
- **Vite**: 构建工具
- **Pinia**: 状态管理
- **Vue Router**: 路由管理

### 主要功能

- 🖥️ 跨平台桌面应用
- 🎨 现代化 UI 界面
- 🔄 前后端分离架构
- 📊 实时状态监控
- 🔔 消息通知系统
- 🌙 主题切换支持
- ⚙️ 系统设置管理

### 开发工具

- 开发者工具：在开发模式下按 `F12` 或 `Cmd+Option+I` (macOS) 打开
- 热重载：修改代码后自动刷新
- 调试：支持 Chrome DevTools 调试

## 🛠️ 常见问题

### 1. 端口冲突

如果 3000 端口被占用，可以修改 `vite.config.js` 中的端口配置：

```js
server: {
  port: 3001, // 修改为其他端口
  // ...
}
```

### 2. 依赖安装失败

尝试清除缓存后重新安装：

```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 3. Electron 启动失败

确保已经启动了 Vite 开发服务器，或者使用 `npm run electron:dev` 一键启动。

## 📝 开发规范

- 使用 ES6+ 语法
- 组件命名采用 PascalCase
- 文件命名采用 kebab-case
- 提交信息遵循 Conventional Commits 规范

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

ISC License