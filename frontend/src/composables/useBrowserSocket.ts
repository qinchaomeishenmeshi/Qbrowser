/**
 * 浏览器状态 WebSocket 实时通信 Composable
 *
 * 监听后端浏览器状态变更事件，实时更新 UI
 */

import { ref, computed, watch } from 'vue'
import { useWebSocket } from '@vueuse/core'
import { useBrowserStore } from '@/stores'
import { ElNotification } from 'element-plus'

// 事件类型
export type BrowserEventType =
  | 'connected'
  | 'pong'
  | 'browser_starting'
  | 'browser_started'
  | 'browser_stopping'
  | 'browser_stopped'
  | 'browser_deleted'
  | 'browser_added'
  | 'browser_error'
  | 'batch_started'
  | 'batch_progress'
  | 'batch_completed'

// 浏览器事件数据
export interface BrowserEventData {
  user_id: string
  status: 'starting' | 'running' | 'stopping' | 'stopped' | 'error' | 'deleted'
  port?: number
  message?: string
  error?: string
}

// 批量操作事件数据
export interface BatchEventData {
  operation: 'start' | 'stop'
  total: number
  completed: number
  success: number
  failed: number
  current_user_id?: string
  results?: any[]
}

// WebSocket 消息
export interface BrowserWSMessage {
  event: BrowserEventType
  channel: string
  timestamp: string
  data: BrowserEventData | BatchEventData
}

// 单例实例
let socketInstance: ReturnType<typeof createBrowserSocket> | null = null

function createBrowserSocket() {
  const browserStore = useBrowserStore()

  // 动态获取后端地址
  const wsUrl = computed(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // 优先从环境变量获取
    let host = import.meta.env.VITE_API_HOST

    if (!host) {
      // 在 Tauri 环境中，hostname 可能是空的或者 localhost
      // 后端绑定在 127.0.0.1，使用 localhost 可能因为双栈(IPv6)导致连接缓慢或失败
      const currentHost = window.location.hostname
      host =
        !currentHost || currentHost === 'localhost' || currentHost === '127.0.0.1'
          ? '127.0.0.1'
          : currentHost
    }

    const port = import.meta.env.VITE_API_PORT || 8000
    const url = `${protocol}//${host}:${port}/ws/browser`
    console.log('🌐 Browser WebSocket URL:', url)
    return url
  })

  // 最近事件
  const latestEvent = ref<BrowserWSMessage | null>(null)

  // 批量操作进度
  const batchProgress = ref<BatchEventData | null>(null)

  // 事件历史
  const eventHistory = ref<BrowserWSMessage[]>([])

  const { status, data, send, open, close } = useWebSocket(wsUrl, {
    autoReconnect: {
      retries: 10,
      delay: 3000,
      onFailed() {
        console.warn('❌ 浏览器 WebSocket 重连均已失败')
        ElNotification.warning({
          title: '实时连接失败',
          message: 'WebSocket 连接多次尝试失败，部分状态更新可能不及时。',
          duration: 0 // 永久显示直到关闭
        })
      }
    },
    heartbeat: {
      message: 'ping',
      interval: 15000,
      pongTimeout: 5000
    },
    onConnected() {
      console.log('✅ 浏览器 WebSocket 已成功握手 (Channel: browser)')
    },
    onDisconnected() {
      console.warn('⚠️ 浏览器 WebSocket 连接已断开，准备重连...')
    },
    onError(_, event) {
      console.error('🔥 浏览器 WebSocket 严重错误:', event)
    }
  })

  // 通知去重记录
  const lastNotificationKey = ref('')
  const lastNotificationTime = ref(0)

  // 统一通知方法（带防抖）
  const notifyOnce = (config: {
    title: string
    message: string
    type: 'success' | 'warning' | 'info' | 'error'
    eventKey: string
  }) => {
    const now = Date.now()
    if (config.eventKey === lastNotificationKey.value && now - lastNotificationTime.value < 500) {
      return // 500ms 内重复通知，忽略
    }
    lastNotificationKey.value = config.eventKey
    lastNotificationTime.value = now

    const { title, message, type } = config
    if (type === 'success') ElNotification.success({ title, message, duration: 3000 })
    else if (type === 'warning') ElNotification.warning({ title, message, duration: 5000 })
    else if (type === 'error') ElNotification.error({ title, message, duration: 5000 })
    else ElNotification.info({ title, message, duration: 3000 })
  }

  // 浏览器事件处理器
  const browserEventHandlers: Record<string, (event: BrowserWSMessage) => void> = {
    connected: () => {
      console.log('✅ 已订阅 browser 频道')
    },

    pong: () => {
      // 心跳响应，忽略
    },

    browser_starting: (event) => {
      const data = event.data as BrowserEventData
      browserStore.updateInstanceStatus(data.user_id, 'starting')
    },

    browser_started: (event) => {
      const data = event.data as BrowserEventData
      browserStore.updateInstanceStatus(data.user_id, 'running', data.port)

      // 如果正在批量操作中，不显示单个通知（避免刷屏）
      if (!batchProgress.value) {
        notifyOnce({
          title: '浏览器已启动',
          message: `实例 ${data.user_id} 启动成功`,
          type: 'success',
          eventKey: `started_${data.user_id}`
        })
      }
    },

    browser_stopping: (event) => {
      const data = event.data as BrowserEventData
      browserStore.updateInstanceStatus(data.user_id, 'stopping')
    },

    browser_stopped: (event) => {
      const data = event.data as BrowserEventData
      browserStore.updateInstanceStatus(data.user_id, 'stopped')

      if (!batchProgress.value) {
        notifyOnce({
          title: '浏览器已停止',
          message: `实例 ${data.user_id} 已停止`,
          type: 'info',
          eventKey: `stopped_${data.user_id}`
        })
      }
    },

    browser_deleted: (event) => {
      const data = event.data as BrowserEventData
      browserStore.removeInstance(data.user_id)
      notifyOnce({
        title: '实例已删除',
        message: data.message || `实例 ${data.user_id} 已删除`,
        type: 'success',
        eventKey: `deleted_${data.user_id}`
      })
    },

    browser_error: (event) => {
      const data = event.data as BrowserEventData
      browserStore.updateInstanceStatus(data.user_id, 'error')
      notifyOnce({
        title: '操作失败',
        message: data.error || '未知错误',
        type: 'error',
        eventKey: `error_${data.user_id}_${data.error}`
      })
    },

    browser_added: (event) => {
      const data = event.data as BrowserEventData
      // 新增浏览器，初始状态通常为 stopped
      browserStore.updateInstanceStatus(data.user_id, 'stopped')
      notifyOnce({
        title: '新浏览器已创建',
        message: `浏览器 ${data.user_id} 已成功添加`,
        type: 'success',
        eventKey: `added_${data.user_id}`
      })
    },

    batch_started: (event) => {
      const data = event.data as BatchEventData
      batchProgress.value = data
      ElNotification.info({
        title: '批量操作开始',
        message: `正在${data.operation === 'start' ? '启动' : '停止'} ${data.total} 个实例...`,
        duration: 2000
      })
    },

    batch_progress: (event) => {
      const data = event.data as BatchEventData
      batchProgress.value = data
    },

    batch_completed: (event) => {
      const data = event.data as BatchEventData
      batchProgress.value = null
      ElNotification.success({
        title: '批量操作完成',
        message: `成功: ${data.success}，失败: ${data.failed}`,
        duration: 4000
      })
      // 刷新实例列表
      browserStore.refresh()
    }
  }

  // 监听消息
  watch(data, (newData) => {
    if (!newData) return

    try {
      const event: BrowserWSMessage = typeof newData === 'string' ? JSON.parse(newData) : newData

      latestEvent.value = event

      // 记录历史（排除心跳）
      if (event.event !== 'pong' && event.event !== 'connected') {
        eventHistory.value.unshift(event)
        if (eventHistory.value.length > 50) {
          eventHistory.value.pop()
        }
      }

      // 调用对应的处理器
      const handler = browserEventHandlers[event.event]
      if (handler) {
        handler(event)
      } else {
        console.warn('未知的浏览器事件类型:', event.event)
      }
    } catch (e) {
      console.error('解析浏览器 WebSocket 消息失败:', e)
    }
  })

  const isConnected = computed(() => status.value === 'OPEN')
  const isConnecting = computed(() => status.value === 'CONNECTING')

  return {
    // 状态
    status,
    isConnected,
    isConnecting,
    latestEvent,
    eventHistory,
    batchProgress,

    // 方法
    send,
    open,
    close
  }
}

/**
 * 获取浏览器 WebSocket 单例
 * 确保整个应用只有一个 WebSocket 连接
 */
export function useBrowserSocket() {
  if (!socketInstance) {
    socketInstance = createBrowserSocket()
    socketInstance.open() // 确保立即启动连接
  }
  return socketInstance
}

/**
 * 销毁单例（应用卸载时调用）
 */
export function destroyBrowserSocket() {
  if (socketInstance) {
    socketInstance.close()
    socketInstance = null
  }
}

export default useBrowserSocket
