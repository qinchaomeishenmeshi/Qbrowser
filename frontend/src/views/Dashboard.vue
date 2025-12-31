<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card hover-card">
          <div class="stat-icon icon-blue">
            <el-icon :size="28"><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">服务状态</div>
            <div class="stat-value">
              <span :class="['status-badge', browserStore.isRunning ? 'success' : 'danger']">
                {{ browserStore.isRunning ? '运行中' : '已停止' }}
              </span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card hover-card">
          <div class="stat-icon icon-green">
            <el-icon :size="28"><ChromeFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">活跃实例</div>
            <div class="stat-value">{{ browserStore.activeCount }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card hover-card">
          <div class="stat-icon icon-orange">
            <el-icon :size="28"><Opportunity /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">已加载扩展</div>
            <div class="stat-value">{{ extensionCount }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card hover-card">
          <div class="stat-icon" :class="wsConnected ? 'icon-green' : 'icon-gray'">
            <el-icon :size="28"><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">实时连接</div>
            <div class="stat-value">
              <span :class="['status-badge', wsConnected ? 'success' : 'danger']">
                {{ wsConnected ? 'WebSocket 已连接' : '未连接' }}
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时任务状态 -->
    <el-card
      v-if="runningCount > 0 || eventHistory.length > 0"
      class="realtime-tasks"
      shadow="never"
    >
      <template #header>
        <div class="card-header">
          <span>
            <el-icon class="pulse-icon"><Loading /></el-icon>
            实时任务状态
          </span>
          <el-tag v-if="runningCount > 0" type="warning">{{ runningCount }} 个运行中</el-tag>
        </div>
      </template>

      <div class="event-list">
        <div
          v-for="(event, index) in eventHistory.slice(0, 5)"
          :key="index"
          class="event-item"
          :class="event.event"
        >
          <el-icon class="event-icon">
            <SuccessFilled v-if="event.event === 'task_completed'" />
            <CircleCloseFilled v-else-if="event.event === 'task_failed'" />
            <Loading v-else />
          </el-icon>
          <div class="event-content">
            <span class="event-name">{{ event.data?.name || event.task_id }}</span>
            <span class="event-status">
              {{
                event.event === 'task_completed'
                  ? '执行成功'
                  : event.event === 'task_failed'
                  ? '执行失败'
                  : '运行中'
              }}
            </span>
          </div>
          <span v-if="event.duration" class="event-duration">{{ event.duration.toFixed(2) }}s</span>
          <span class="event-time">{{ formatTime(event.timestamp) }}</span>
        </div>
        <el-empty v-if="eventHistory.length === 0" description="暂无任务事件" :image-size="60" />
      </div>
    </el-card>

    <!-- 快速操作 -->
    <el-card class="quick-actions" shadow="never">
      <template #header>
        <div class="card-header">
          <span>快速操作</span>
        </div>
      </template>

      <el-space wrap>
        <el-button type="primary" :icon="Plus" @click="showStartDialog = true">
          新建实例
        </el-button>
        <el-button type="warning" :icon="SwitchButton" @click="handleStopAll"> 停止全部 </el-button>
        <el-button :icon="Refresh" @click="handleRefresh" :loading="browserStore.loading">
          刷新状态
        </el-button>
        <div class="polling-indicator" :class="{ active: isPolling }">
          <span class="dot"></span>
          实时同步中
        </div>
      </el-space>
    </el-card>

    <!-- 浏览器实例列表 -->
    <el-card class="instance-list" shadow="never">
      <template #header>
        <div class="card-header">
          <span>浏览器实例 (已缓存)</span>
          <el-tag type="info">{{ browserStore.totalCount }} 个</el-tag>
        </div>
      </template>

      <el-empty v-if="browserStore.allInstances.length === 0" description="暂无实例记录" />

      <el-table v-else :data="browserStore.allInstances" style="width: 100%">
        <el-table-column prop="user_id" label="用户 ID" width="200">
          <template #default="{ row }">
            <el-tag>{{ row.user_id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <span v-if="row.is_running" class="status-badge success">
              <el-icon><SuccessFilled /></el-icon>
              运行中
            </span>
            <span v-else class="status-badge warning">
              <el-icon><CircleCloseFilled /></el-icon>
              已停止
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-space>
              <el-tooltip
                :content="row.is_running ? '停止进程并保留缓存' : '恢复浏览器运行'"
                placement="top"
              >
                <el-button
                  v-if="!row.is_running"
                  size="small"
                  type="primary"
                  link
                  :icon="VideoPlay"
                  @click="handleRun(row.user_id)"
                >
                  启动
                </el-button>
                <el-button
                  v-else
                  size="small"
                  type="warning"
                  link
                  :icon="VideoPause"
                  @click="handleStop(row.user_id)"
                >
                  停止
                </el-button>
              </el-tooltip>

              <el-tooltip content="彻底删除实例及本地数据" placement="top">
                <el-button
                  size="small"
                  type="danger"
                  link
                  :icon="Delete"
                  @click="handleDelete(row.user_id)"
                >
                  删除
                </el-button>
              </el-tooltip>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 启动实例对话框 -->
    <el-dialog v-model="showStartDialog" title="启动新实例" width="500">
      <el-form :model="startForm" label-width="80px">
        <el-form-item label="用户 ID" required>
          <el-input v-model="startForm.userId" placeholder="请输入用户 ID" />
        </el-form-item>
        <el-form-item label="初始 URL">
          <el-input v-model="startForm.url" placeholder="https://example.com (可选)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStartDialog = false">取消</el-button>
        <el-button type="primary" @click="handleStart" :loading="browserStore.loading">
          启动
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useBrowserStore, useAppStore } from '@/stores'
import { usePolling } from '@/composables/usePolling'
import { useSchedulerSocket } from '@/composables/useSchedulerSocket'
import {
  Monitor,
  ChromeFilled,
  Opportunity,
  Connection,
  Plus,
  VideoPlay,
  VideoPause,
  Refresh,
  SuccessFilled,
  CircleCloseFilled,
  Loading,
  Delete,
  SwitchButton
} from '@element-plus/icons-vue'

const browserStore = useBrowserStore()
const appStore = useAppStore()

// WebSocket 实时状态
const { isConnected: wsConnected, runningCount, eventHistory } = useSchedulerSocket()

const showStartDialog = ref(false)
const startForm = ref({
  userId: '',
  url: ''
})
const extensionCount = ref(0)

// 格式化时间
const formatTime = (isoString?: string) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// 开启 5 秒一次的轮询
const { isPolling } = usePolling(async () => {
  await browserStore.refresh()
  await appStore.checkBackendHealth()
}, 5000)

const handleRefresh = async () => {
  await browserStore.refresh()
  ElMessage.success('数据已刷新')
}

const handleStart = async () => {
  if (!startForm.value.userId.trim()) {
    ElMessage.warning('请输入用户 ID')
    return
  }

  const result = await browserStore.startInstance(
    startForm.value.userId,
    startForm.value.url || undefined
  )

  if (result?.status === 'success') {
    ElMessage.success(`实例 ${startForm.value.userId} 启动成功`)
    showStartDialog.value = false
    startForm.value = { userId: '', url: '' }
  } else if (result?.status === 'already_running') {
    ElMessage.warning('该实例已在运行中')
  } else {
    ElMessage.error('启动失败: ' + (result?.message || '未知错误'))
  }
}

const handleStopAll = async () => {
  try {
    await ElMessageBox.confirm('确定要停止所有浏览器实例吗？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const result = await browserStore.stopAll()
    if (result?.status === 'success') {
      ElMessage.success('所有实例已停止')
    }
  } catch {
    // 用户取消
  }
}

const handleStop = async (userId: string) => {
  try {
    await ElMessageBox.confirm(`确定要停止实例 ${userId} 吗？`, '确认操作', {
      type: 'warning'
    })
    const result = await browserStore.stopInstance(userId)
    if (result?.status === 'success') {
      ElMessage.success(`实例 ${userId} 已停止（已缓存）`)
    } else {
      ElMessage.error('停止失败')
    }
  } catch {
    // 取消
  }
}

const handleRun = async (userId: string) => {
  const result = await browserStore.startInstance(userId)
  if (result?.status === 'success' || result?.status === 'already_running') {
    ElMessage.success(`实例 ${userId} 已启动`)
  } else {
    ElMessage.error('启动失败')
  }
}

const handleDelete = async (userId: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要彻底删除实例 <strong style="color: #ef4444">${userId}</strong> 及其本地数据吗？<br/><small style="color: #94a3b8">此操作将永久清理磁盘空间，且不可恢复。</small>`,
      '危险操作',
      {
        confirmButtonText: '彻底删除',
        cancelButtonText: '取消',
        type: 'error',
        dangerouslyUseHTMLString: true,
        distinguishCancelAndClose: true
      }
    )
    const result = await browserStore.deleteInstance(userId)
    if (result?.status === 'success') {
      ElMessage.success(`实例 ${userId} 已彻底删除`)
    } else {
      ElMessage.error('删除失败: ' + (result?.message || '未知错误'))
    }
  } catch {
    // 取消
  }
}
</script>

<style scoped lang="scss">
.dashboard {
  padding: 24px;
  background: linear-gradient(180deg, var(--bg-color-soft) 0%, var(--bg-color) 100%);
  min-height: 100%;
}

.stat-cards {
  margin-bottom: 24px;
}

.stat-card {
  height: 100%;
  /* 入场动画 */
  animation: cardEnter 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  opacity: 0;

  &:nth-child(1) {
    animation-delay: 0s;
  }
  &:nth-child(2) {
    animation-delay: 0.1s;
  }
  &:nth-child(3) {
    animation-delay: 0.2s;
  }
  &:nth-child(4) {
    animation-delay: 0.3s;
  }

  @keyframes cardEnter {
    from {
      opacity: 0;
      transform: scale(0.95) translateY(12px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }

  :deep(.el-card__body) {
    display: flex;
    align-items: center;
    padding: 24px;
    height: 100%;
  }
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  color: white;
  margin-right: 20px;
  flex-shrink: 0;
  transition: all 0.3s ease;
  position: relative;

  /* 悬停时图标放大 */
  .stat-card:hover & {
    transform: scale(1.08);
  }

  &.icon-blue {
    background: linear-gradient(135deg, var(--color-blue-500) 0%, var(--color-blue-600) 100%);
    box-shadow: 0 8px 16px -4px rgba(59, 130, 246, 0.4);
  }

  &.icon-green {
    background: linear-gradient(135deg, var(--success-color) 0%, #34d399 100%);
    box-shadow: 0 8px 16px -4px rgba(16, 185, 129, 0.4);
  }

  &.icon-orange {
    background: linear-gradient(135deg, var(--warning-color) 0%, #fbbf24 100%);
    box-shadow: 0 8px 16px -4px rgba(245, 158, 11, 0.4);
  }

  &.icon-gray {
    background: linear-gradient(135deg, var(--color-slate-500) 0%, var(--color-slate-600) 100%);
    box-shadow: 0 8px 16px -4px rgba(100, 116, 139, 0.4);
  }
}

.stat-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;

  .stat-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-color-secondary);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-color);
    letter-spacing: -0.5px;
    line-height: 1.2;
  }
}

.quick-actions,
.instance-list {
  margin-bottom: 24px;

  :deep(.el-card__header) {
    padding: 16px 20px;
    background: var(--bg-color-soft);
    border-bottom: 1px solid var(--border-color);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--text-color);
}

.polling-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-left: 16px;
  padding: 6px 12px;
  background: var(--bg-color-soft);
  border-radius: 20px;
  opacity: 0.7;
  transition: all 0.3s ease;

  &.active {
    opacity: 1;
    background: rgba(16, 185, 129, 0.1);

    .dot {
      background-color: var(--success-color);
      box-shadow: 0 0 8px var(--success-color);
      animation: dotPulse 2s infinite;
    }
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--text-color-placeholder);
    transition: all 0.3s ease;
  }
}

@keyframes dotPulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.6;
  }
}

// 实时任务状态卡片样式
.realtime-tasks {
  margin-bottom: 24px;

  .pulse-icon {
    animation: spin 2s linear infinite;
    margin-right: 8px;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-color-soft);
  border-radius: 8px;
  transition: all 0.3s ease;

  &:hover {
    background: var(--bg-color-muted);
  }

  &.task_completed {
    border-left: 3px solid var(--success-color);

    .event-icon {
      color: var(--success-color);
    }
  }

  &.task_failed {
    border-left: 3px solid var(--danger-color);

    .event-icon {
      color: var(--danger-color);
    }
  }

  &.task_started {
    border-left: 3px solid var(--warning-color);

    .event-icon {
      color: var(--warning-color);
      animation: spin 1s linear infinite;
    }
  }
}

.event-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.event-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;

  .event-name {
    font-weight: 500;
    color: var(--text-color);
  }

  .event-status {
    font-size: 12px;
    color: var(--text-color-secondary);
  }
}

.event-duration {
  font-size: 13px;
  font-weight: 500;
  color: var(--primary-color);
  padding: 2px 8px;
  background: rgba(var(--primary-color-rgb), 0.1);
  border-radius: 4px;
}

.event-time {
  font-size: 12px;
  color: var(--text-color-placeholder);
  flex-shrink: 0;
}
</style>
