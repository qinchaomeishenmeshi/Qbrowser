import { defineStore } from 'pinia'
import { browserApi } from '@/api'
import type { BrowserStatus, StartResult } from '@/types/api'

export const useBrowserStore = defineStore('browser', {
  state: () => ({
    status: null as BrowserStatus | null,
    activeInstances: [] as string[],
    allInstances: [] as any[], // 新增：包含已停止的实例
    activeCount: 0,
    loading: false,
    error: null as string | null
  }),

  getters: {
    isRunning: (state) => state.status?.status === 'running',
    instanceCount: (state) => state.activeInstances.length,
    totalCount: (state) => state.allInstances.length
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

    async fetchAllInstances() {
      try {
        const result = await browserApi.getAllInstances()
        this.allInstances = result.instances
      } catch (e) {
        console.error('Failed to fetch all instances:', e)
      }
    },

    async startInstance(userId: string, url?: string): Promise<StartResult | null> {
      this.loading = true
      this.error = null
      try {
        const result = await browserApi.start(userId, url)
        if (result.status === 'success' || result.status === 'already_running') {
          await this.refresh()
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
        await this.refresh()
        return result
      } catch (e) {
        this.error = (e as Error).message
        return null
      } finally {
        this.loading = false
      }
    },

    async deleteInstance(userId: string) {
      this.loading = true
      this.error = null
      try {
        const result = await browserApi.deleteInstance(userId)
        if (result.status === 'success') {
          await this.refresh()
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
          await this.refresh()
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
      try {
        const [status, active, all] = await Promise.all([
          browserApi.getStatus(),
          browserApi.getActiveInstances(),
          browserApi.getAllInstances()
        ])
        this.status = status
        this.activeInstances = active.active_instances
        this.activeCount = active.active_count
        this.allInstances = all.instances
      } catch (e) {
        this.error = (e as Error).message
      }
    }
  }
})
