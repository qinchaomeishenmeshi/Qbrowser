import type { HealthCheck, SystemLogsResponse, UISettings } from '@/types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const systemApi = {
  /**
   * 健康检查
   */
  async health(): Promise<HealthCheck> {
    const res = await fetch(`${API_BASE}/health`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 获取系统日志
   */
  async getLogs(limit = 10): Promise<SystemLogsResponse> {
    const res = await fetch(`${API_BASE}/system/logs?limit=${limit}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 获取 UI 设置
   */
  async getUISettings(): Promise<{ settings: UISettings; message: string }> {
    const res = await fetch(`${API_BASE}/settings/ui`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 保存 UI 设置
   */
  async saveUISettings(
    settings: Partial<UISettings>
  ): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/settings/ui`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings)
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
}
