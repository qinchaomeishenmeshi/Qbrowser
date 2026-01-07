import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { browserApi } from '@/api'
import type { BrowserStatus, StartResult } from '@/types/api'

// 实例状态类型
type InstanceStatus = 'running' | 'stopped' | 'starting' | 'stopping' | 'error'

// 实例信息
interface BrowserInstance {
  user_id: string
  is_running: boolean
  status?: InstanceStatus
  port?: number
}

export const useBrowserStore = defineStore('browser', () => {
  // ========== State ==========
  const status = ref<BrowserStatus | null>(null)
  const activeInstances = ref<string[]>([])
  const allInstances = ref<BrowserInstance[]>([])
  const activeCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ========== Getters ==========
  const isRunning = computed(() => status.value?.status === 'running')
  const instanceCount = computed(() => activeInstances.value.length)
  const totalCount = computed(() => allInstances.value.length)

  // ========== Actions ==========

  async function fetchStatus() {
    loading.value = true
    error.value = null
    try {
      status.value = await browserApi.getStatus()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function fetchActiveInstances() {
    loading.value = true
    error.value = null
    try {
      const result = await browserApi.getActiveInstances()
      activeInstances.value = result.active_instances
      activeCount.value = result.active_count
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function fetchAllInstances() {
    try {
      const result = await browserApi.getAllInstances()
      allInstances.value = result.instances
    } catch (e) {
      console.error('Failed to fetch all instances:', e)
    }
  }

  async function startInstance(userId: string, url?: string): Promise<StartResult | null> {
    loading.value = true
    error.value = null
    // 乐观更新：在请求发送前先将状态设为启动中，确保 UI 响应
    updateInstanceStatus(userId, 'starting')

    try {
      const result = await browserApi.start(userId, url)
      // 成功返回后，手动触发一次状态更新作为 WebSocket 的兜底
      if (result?.status === 'success' || result?.status === 'already_running') {
        updateInstanceStatus(userId, 'running', result.port)
      }
      return result
    } catch (e) {
      error.value = (e as Error).message
      // 失败后恢复状态
      updateInstanceStatus(userId, 'stopped')
      return null
    } finally {
      loading.value = false
    }
  }

  async function stopInstance(userId: string) {
    loading.value = true
    error.value = null
    // 乐观更新：立即显示停止中状态
    updateInstanceStatus(userId, 'stopping')

    try {
      const result = await browserApi.stopInstance(userId)
      // 成功返回后，手动触发一次状态更新作为 WebSocket 的兜底
      if (result?.status === 'success') {
        updateInstanceStatus(userId, 'stopped')
      }
      return result
    } catch (e) {
      error.value = (e as Error).message
      // 失败后恢复为运行
      updateInstanceStatus(userId, 'running')
      return null
    } finally {
      loading.value = false
    }
  }

  async function createBrowser(
    userId: string,
    config?: Record<string, any>
  ): Promise<{ status: string; user_id: string } | null> {
    loading.value = true
    error.value = null
    try {
      const result = await browserApi.create(userId, config)
      // WebSocket 会推送新增事件，这里不需要手动 push
      return result
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteInstance(userId: string) {
    loading.value = true
    error.value = null
    try {
      const result = await browserApi.deleteInstance(userId)
      // 删除通常较快，且 WebSocket 会处理移除逻辑
      return result
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteBatch(userIds: string[]) {
    loading.value = true
    error.value = null
    try {
      const result = await browserApi.deleteBatch(userIds)
      return result
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      loading.value = false
    }
  }

  async function startAll(userIds: string[]) {
    loading.value = true
    error.value = null
    // 乐观更新：将所有选中的设为启动中
    userIds.forEach((id) => updateInstanceStatus(id, 'starting'))
    try {
      const result = await browserApi.startAll(userIds)
      return result
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      loading.value = false
    }
  }

  async function stopAll(userIds?: string[]) {
    loading.value = true
    error.value = null
    // 批量停止时，将指定或运行中的实例设为停止中
    const targets = userIds
      ? allInstances.value.filter((i) => userIds.includes(i.user_id))
      : allInstances.value.filter((i) => i.is_running)

    targets.forEach((inst) => {
      inst.status = 'stopping'
    })

    try {
      const result = await browserApi.stopAll(userIds)
      return result
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      loading.value = false
    }
  }

  async function refresh() {
    try {
      const [statusResult, active, all] = await Promise.all([
        browserApi.getStatus(),
        browserApi.getActiveInstances(),
        browserApi.getAllInstances()
      ])
      status.value = statusResult
      activeInstances.value = active.active_instances
      activeCount.value = active.active_count
      // 整体替换数组确保响应式
      allInstances.value = all.instances
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  // ========== WebSocket 响应式更新方法 ==========

  /**
   * 更新单个实例的状态（由 WebSocket 事件触发）
   */
  function updateInstanceStatus(userId: string, instanceStatus: InstanceStatus, port?: number) {
    const instance = allInstances.value.find((i) => i.user_id === userId)

    if (instance) {
      // 更新已存在的实例
      instance.is_running = instanceStatus === 'running'
      instance.status = instanceStatus
      if (port !== undefined) {
        instance.port = port
      }
    } else {
      // 新实例（无论状态如何都添加，支持新建浏览器的 'stopped' 状态）
      allInstances.value.push({
        user_id: userId,
        is_running: instanceStatus === 'running',
        status: instanceStatus,
        port: port || 0
      })
    }

    // 重新计算活跃数量
    activeCount.value = allInstances.value.filter((i) => i.is_running).length
    activeInstances.value = allInstances.value.filter((i) => i.is_running).map((i) => i.user_id)
  }

  /**
   * 从列表中移除实例（由 WebSocket 删除事件触发）
   */
  function removeInstance(userId: string) {
    const index = allInstances.value.findIndex((i) => i.user_id === userId)
    if (index !== -1) {
      allInstances.value.splice(index, 1)
      activeCount.value = allInstances.value.filter((i) => i.is_running).length
      activeInstances.value = allInstances.value.filter((i) => i.is_running).map((i) => i.user_id)
    }
  }

  return {
    // State
    status,
    activeInstances,
    allInstances,
    activeCount,
    loading,
    error,

    // Getters
    isRunning,
    instanceCount,
    totalCount,

    // Actions
    fetchStatus,
    fetchActiveInstances,
    fetchAllInstances,
    startInstance,
    startAll,
    stopInstance,
    deleteInstance,
    createBrowser,
    deleteBatch,
    stopAll,
    refresh,

    // WebSocket 响应式更新
    updateInstanceStatus,
    removeInstance
  }
})
