import { defineStore } from 'pinia'
import { systemApi } from '@/api'
import type { UISettings } from '@/types/api'

export const useAppStore = defineStore('app', {
  state: () => ({
    // 后端连接状态
    backendConnected: false,
    backendUrl: 'http://127.0.0.1:8000',

    // UI 设置
    settings: {
      theme: 'light',
      language: 'zh-CN',
      sidebarCollapsed: false
    } as UISettings,

    // 全局加载状态
    globalLoading: false
  }),

  getters: {
    isDarkTheme: (state) => state.settings.theme === 'dark'
  },

  actions: {
    async checkBackendHealth() {
      try {
        const result = await systemApi.health()
        this.backendConnected = result.status === 'ok'
        return this.backendConnected
      } catch {
        this.backendConnected = false
        return false
      }
    },

    async loadSettings() {
      try {
        const result = await systemApi.getUISettings()
        this.settings = result.settings
      } catch {
        // 使用默认设置
      }
    },

    async saveSettings(settings: Partial<UISettings>) {
      try {
        await systemApi.saveUISettings(settings)
        Object.assign(this.settings, settings)
        return true
      } catch {
        return false
      }
    },

    toggleSidebar() {
      this.settings.sidebarCollapsed = !this.settings.sidebarCollapsed
      this.saveSettings({ sidebarCollapsed: this.settings.sidebarCollapsed })
    },

    setTheme(theme: 'light' | 'dark') {
      this.settings.theme = theme
      document.documentElement.classList.toggle('dark', theme === 'dark')
      this.saveSettings({ theme })
    }
  }
})
