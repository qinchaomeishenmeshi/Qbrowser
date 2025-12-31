import { defineStore } from 'pinia'
import { browserApi } from '@/api'
import type { BrowserStatus, StartResult } from '@/types/api'

export const useBrowserStore = defineStore('browser', {
  state: () => ({
    status: null as BrowserStatus | null,
    activeInstances: [] as string[],
    activeCount: 0,
    loading: false,
    error: null as string | null
  }),

  getters: {
    isRunning: (state) => state.status?.status === 'running',
    instanceCount: (state) => state.activeInstances.length
  },

  actions: {
    async fetchStatus() {
      this.loading = true
      this.error = null
      try {
        this.status = await browserApi.getStatus()
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },

    async fetchActiveInstances() {
      this.loading = true
      this.error = null
      try {
        const result = await browserApi.getActiveInstances()
        this.activeInstances = result.active_instances
        this.activeCount = result.active_count
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },

    async startInstance(userId: string, url?: string): Promise<StartResult | null> {
      this.loading = true
      this.error = null
      try {
        const result = await browserApi.start(userId, url)
        if (result.status === 'success') {
          await this.fetchActiveInstances()
        }
        return result
      } catch (e) {
        this.error = (e as Error).message
        return null
      } finally {
        this.loading = false
      }
    },

    async stopInstance(userId: string) {
      this.loading = true
      this.error = null
      try {
        const result = await browserApi.stopInstance(userId)
        if (result.status === 'success') {
          await this.fetchActiveInstances()
        }
        return result
      } catch (e) {
        this.error = (e as Error).message
        return null
      } finally {
        this.loading = false
      }
    },

    async stopAll() {
      this.loading = true
      this.error = null
      try {
        const result = await browserApi.stopAll()
        if (result.status === 'success') {
          this.activeInstances = []
          this.activeCount = 0
          await this.fetchStatus()
        }
        return result
      } catch (e) {
        this.error = (e as Error).message
        return null
      } finally {
        this.loading = false
      }
    },

    async refresh() {
      // 避免重复加载导致的 loading 闪烁，这里内部调用不设置全局 loading
      try {
        const [status, active] = await Promise.all([
          browserApi.getStatus(),
          browserApi.getActiveInstances()
        ])
        this.status = status
        this.activeInstances = active.active_instances
        this.activeCount = active.active_count
      } catch (e) {
        this.error = (e as Error).message
      }
    }
  }
})
