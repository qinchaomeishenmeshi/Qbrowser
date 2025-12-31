// 浏览器状态相关类型
export interface BrowserStatus {
  status: 'running' | 'stopped' | 'error'
  total_instances: number
  active_instances: number
  message: string
}

export interface ActiveInstances {
  status: string
  active_count: number
  active_instances: string[]
}

export interface StartResult {
  user_id: string
  status: 'success' | 'already_running' | 'fail' | 'error'
  port?: number
  opened_url?: string
  message?: string
}

export interface ConnectResult {
  user_id: string
  status: 'connected' | 'already_connected' | 'connection_failed' | 'connection_error'
  port: number
  message: string
}

export interface DetectBrowserResult {
  port: number
  status: 'browser_detected' | 'not_browser' | 'port_free' | 'connection_failed' | 'detection_error'
  tabs_count?: number
  message: string
}

// 扩展状态相关类型
export interface ExtensionStatus {
  status: string
  total_browsers: number
  configured_extensions: string[]
  message: string
}

export interface UserExtensionStatus {
  user_id: string
  browser_running: boolean
  port?: number
  tab_url?: string
  extension_check?: {
    url: string
    extensions: string[]
    chrome_available: boolean
  }
  configured_extensions: string[]
  message: string
}

// 健康检查
export interface HealthCheck {
  status: string
  message: string
}

// 系统日志
export interface SystemLog {
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG'
  message: string
  component: string
}

export interface SystemLogsResponse {
  logs: SystemLog[]
  total_count: number
  limit: number
  message: string
  note?: string
}

// UI 设置
export interface UISettings {
  theme: 'light' | 'dark'
  language: string
  sidebarCollapsed: boolean
}
