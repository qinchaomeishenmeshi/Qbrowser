import type {
  BrowserStatus,
  ActiveInstances,
  StartResult,
  ConnectResult,
  DetectBrowserResult
} from '@/types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const browserApi = {
  /**
   * 获取浏览器服务状态
   */
  async getStatus(): Promise<BrowserStatus> {
    const res = await fetch(`${API_BASE}/browser/status`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 获取活跃实例列表
   */
  async getActiveInstances(): Promise<ActiveInstances> {
    const res = await fetch(`${API_BASE}/active_instances`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 启动浏览器实例
   */
  async start(userId: string, url?: string): Promise<StartResult> {
    const params = new URLSearchParams()
    if (url) params.append('url', url)

    const res = await fetch(`${API_BASE}/start/${userId}?${params}`, {
      method: 'POST'
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 批量启动浏览器实例
   */
  async startAll(userIds: string[], url?: string): Promise<{ results: StartResult[] }> {
    const params = new URLSearchParams()
    userIds.forEach((id) => params.append('user_ids', id))
    if (url) params.append('url', url)

    const res = await fetch(`${API_BASE}/start_all?${params}`, {
      method: 'POST'
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 停止指定或所有浏览器实例
   */
  async stopAll(userIds?: string[]): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: userIds ? JSON.stringify(userIds) : null
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 停止单个浏览器实例
   */
  async stopInstance(userId: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/stop/${userId}`, { method: 'POST' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 连接到已打开的浏览器实例
   */
  async connect(userId: string, port: number): Promise<ConnectResult> {
    const res = await fetch(`${API_BASE}/connect/${userId}?port=${port}`, {
      method: 'POST'
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 获取指定实例的详细信息（包含扩展状态）
   */
  async getInstanceDetails(userId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/extensions/${userId}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 检测端口上的浏览器
   */
  async detectBrowser(port: number): Promise<DetectBrowserResult> {
    const res = await fetch(`${API_BASE}/detect_browser/${port}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 获取所有实例列表（从缓存或运行中）
   */
  async getAllInstances(): Promise<{ status: string; total_count: number; instances: any[] }> {
    const res = await fetch(`${API_BASE}/all_instances`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   /**
   * 新建浏览器配置（不启动）
   */
  async create(userId: string): Promise<{ status: string; user_id: string }> {
    const res = await fetch(`${API_BASE}/browser/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 彻底删除浏览器实例和其本地数据
   */
  async deleteInstance(userId: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/delete/${userId}`, { method: 'POST' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  /**
   * 批量彻底删除浏览器实例
   */
  async deleteBatch(userIds: string[]): Promise<{ status: string; results: any }> {
    const res = await fetch(`${API_BASE}/delete_batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userIds)
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
}
