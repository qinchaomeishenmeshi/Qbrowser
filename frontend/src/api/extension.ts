import type { ExtensionStatus, UserExtensionStatus } from '@/types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const extensionApi = {
  /**
   * 获取全局扩展状态
   */
  async getStatus(): Promise<ExtensionStatus> {
    const res = await fetch(`${API_BASE}/extensions/status`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 获取指定用户的扩展状态
   */
  async getUserStatus(userId: string): Promise<UserExtensionStatus> {
    const res = await fetch(`${API_BASE}/extensions/${userId}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
}
