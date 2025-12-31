/**
 * 调度器 WebSocket 实时状态 Composable
 *
 * 使用 VueUse 的 useWebSocket 封装调度器状态实时推送
 */

import { ref, computed, watch } from 'vue'
import { useWebSocket } from '@vueuse/core'

// 任务事件类型
export interface TaskEvent {
  event: 'task_started' | 'task_completed' | 'task_failed' | 'connected' | 'pong'
  task_id?: string
  status?: string
  duration?: number
  error?: string
  timestamp?: string
  data?: {
    name?: string
    execution_id?: string
  }
}

// 最近任务记录
export interface RecentTask {
  task_id: string
  name: string
  status: string
  start_time: string
  end_time?: string
  duration?: number
  error_message?: string
}

export function useSchedulerSocket() {
  // WebSocket 连接
  const wsUrl = computed(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = 8000 // 后端默认端口
    return `${protocol}//${host}:${port}/ws/scheduler`
  })

  const { status, data, send, open, close } = useWebSocket(wsUrl.value, {
    autoReconnect: {
      retries: 3,
      delay: 3000,
      onFailed() {
        console.warn('WebSocket 自动重连失败')
      }
    },
    heartbeat: {
      message: 'ping',
      interval: 30000,
      pongTimeout: 5000
    },
    onConnected() {
      console.log('✅ 调度器 WebSocket 已连接')
    },
    onDisconnected() {
      console.log('❌ 调度器 WebSocket 已断开')
    },
    onError(_, event) {
      console.error('WebSocket 错误:', event)
    }
  })

  // 最新事件
  const latestEvent = ref<TaskEvent | null>(null)

  // 事件历史（最多保留 50 条）
  const eventHistory = ref<TaskEvent[]>([])

  // 运行中的任务
  const runningTasks = ref<Map<string, TaskEvent>>(new Map())

  // 解析 WebSocket 消息
  watch(data, (newData) => {
    if (!newData) return

    try {
      const event: TaskEvent = typeof newData === 'string' ? JSON.parse(newData) : newData

      latestEvent.value = event

      // 添加到历史记录
      if (event.event !== 'pong' && event.event !== 'connected') {
        eventHistory.value.unshift(event)
        if (eventHistory.value.length > 50) {
          eventHistory.value.pop()
        }
      }

      // 更新运行中任务
      if (event.task_id) {
        if (event.event === 'task_started') {
          runningTasks.value.set(event.task_id, event)
        } else if (event.event === 'task_completed' || event.event === 'task_failed') {
          runningTasks.value.delete(event.task_id)
        }
      }
    } catch (e) {
      console.error('解析 WebSocket 消息失败:', e)
    }
  })

  // 连接状态
  const isConnected = computed(() => status.value === 'OPEN')
  const isConnecting = computed(() => status.value === 'CONNECTING')

  // 运行中任务数量
  const runningCount = computed(() => runningTasks.value.size)

  return {
    // 状态
    status,
    isConnected,
    isConnecting,
    latestEvent,
    eventHistory,
    runningTasks,
    runningCount,

    // 方法
    send,
    open,
    close
  }
}

export default useSchedulerSocket
