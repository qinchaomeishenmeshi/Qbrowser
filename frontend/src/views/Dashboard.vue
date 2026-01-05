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

    <!-- 快速操作 -->
    <el-card class="quick-actions" shadow="never">
      <template #header>
        <div class="card-header">
          <span>资源管理</span>
        </div>
      </template>

      <div class="action-bar">
        <el-space wrap>
          <el-button type="primary" :icon="Plus" @click="showStartDialog = true">
            新建浏览器
          </el-button>
          <el-button :icon="Refresh" @click="handleRefresh" :loading="browserStore.loading">
            刷新状态
          </el-button>
          <div class="polling-indicator" :class="{ active: isPolling }">
            <span class="dot"></span>
            实时同步中
          </div>
        </el-space>

        <!-- 批量操作栏（有选中时显示） -->
        <transition name="el-zoom-in-top">
          <div v-if="selectedIds.length > 0" class="batch-bar">
            <div class="selection-info">
              已选中 <span class="count">{{ selectedIds.length }}</span> 项
            </div>
            <el-divider direction="vertical" />
            <el-space>
              <el-button type="primary" size="small" :icon="VideoPlay" @click="handleBatchOpen">
                批量打开
              </el-button>
              <el-button type="warning" size="small" :icon="VideoPause" @click="handleBatchClose">
                批量关闭
              </el-button>
              <el-button type="danger" size="small" :icon="Delete" @click="handleBatchDelete">
                批量删除
              </el-button>
              <el-button size="small" link @click="clearSelection">取消选择</el-button>
            </el-space>
          </div>
        </transition>
      </div>
    </el-card>

    <!-- 浏览器实例列表 -->
    <el-card class="instance-list" shadow="never">
      <template #header>
        <div class="card-header">
          <span>浏览器列表</span>&nbsp;
          <el-tag type="info" effect="plain">{{ browserStore.totalCount }} 个</el-tag>
        </div>
      </template>

      <el-empty v-if="browserStore.allInstances.length === 0" description="暂无浏览器环境" />

      <el-table
        v-else
        ref="instanceTable"
        :data="browserStore.allInstances"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="user_id" label="浏览器名称 / ID" width="220">
          <template #default="{ row }">
            <div class="user-id-cell">
              <el-icon class="browser-icon"><ChromeFilled /></el-icon>
              <el-tag size="small" effect="light">{{ row.user_id }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="运行状态" width="150">
          <template #default="{ row }">
            <span v-if="row.is_running" class="status-badge success">
              <span class="dot pulse"></span>
              打开中
            </span>
            <span v-else-if="row.status === 'starting'" class="status-badge info">
              <span class="dot spinning"></span>
              启动中...
            </span>
            <span v-else-if="row.status === 'stopping'" class="status-badge warning">
              <span class="dot spinning"></span>
              关闭中...
            </span>
            <span v-else class="status-badge gray">
              <span class="dot"></span>
              已关闭
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="port" label="调试端口" width="120">
          <template #default="{ row }">
            <code v-if="row.port">{{ row.port }}</code>
            <span v-else class="text-secondary">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="180" align="center">
          <template #default="{ row }">
            <el-space>
              <el-button
                v-if="!row.is_running"
                size="small"
                type="primary"
                :icon="VideoPlay"
                @click="handleRun(row.user_id)"
                :loading="row.status === 'starting'"
              >
                打开
              </el-button>
              <el-button
                v-else
                size="small"
                type="warning"
                :icon="VideoPause"
                @click="handleStop(row.user_id)"
                :loading="row.status === 'stopping'"
              >
                关闭
              </el-button>

              <el-dropdown trigger="click">
                <el-button
                  link
                  type="primary"
                  :icon="MoreFilled"
                  style="font-size: 16px; margin-left: 8px"
                />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      :icon="Delete"
                      @click="handleDelete(row.user_id)"
                      style="color: var(--el-color-danger)"
                    >
                      彻底删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建浏览器对话框 -->
    <el-dialog v-model="showStartDialog" title="新建浏览器" width="460px" border-radius="12px">
      <el-form :model="startForm" label-width="100px" label-position="left">
        <el-form-item label="浏览器 ID" placeholder="例如：account-01" required>
          <el-input v-model="startForm.userId" placeholder="请输入浏览器标识符" />
          <div class="form-tip">标识符用于区分不同的浏览器环境和数据目录</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showStartDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreateBrowser" :loading="browserStore.loading">
            立即创建
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useBrowserStore, useAppStore } from '@/stores'
import { usePolling } from '@/composables/usePolling'
import { useBrowserSocket } from '@/composables/useBrowserSocket'
import {
  Monitor,
  ChromeFilled,
  Opportunity,
  Connection,
  Plus,
  VideoPlay,
  VideoPause,
  Refresh,
  Delete,
  MoreFilled
} from '@element-plus/icons-vue'

const browserStore = useBrowserStore()
const appStore = useAppStore()

onMounted(async () => {
  // 每次进入仪表盘尝试刷新一次数据
  if (appStore.backendConnected) {
    await browserStore.refresh()
  }
})

// WebSocket 实时状态 (使用浏览器频道)
const { isConnected: wsConnected } = useBrowserSocket()

const showStartDialog = ref(false)
const startForm = ref({
  userId: '',
  url: ''
})
const extensionCount = ref(0)
const instanceTable = ref<any>(null)
const selectedIds = ref<string[]>([])

// 轮询逻辑：WebSocket 断开时启用更频繁的轮询作为兜底
const { isPolling } = usePolling(async () => {
  if (!wsConnected.value) {
    await browserStore.refresh()
  }
  await appStore.checkBackendHealth()
}, 10000)

const handleRefresh = async () => {
  await Promise.all([browserStore.refresh(), appStore.checkBackendHealth()])
  ElMessage.success('数据已刷新')
}

// 多选处理
const handleSelectionChange = (selection: any[]) => {
  selectedIds.value = selection.map((item) => item.user_id)
}

const clearSelection = () => {
  instanceTable.value?.clearSelection()
}

// 新建浏览器（静默创建）
const handleCreateBrowser = async () => {
  if (!startForm.value.userId.trim()) {
    ElMessage.warning('请输入浏览器 ID')
    return
  }

  const result = await browserStore.createBrowser(startForm.value.userId)

  if (result?.status === 'success') {
    ElMessage.success(`浏览器 ${startForm.value.userId} 创建成功`)
    showStartDialog.value = false
    startForm.value = { userId: '', url: '' }
  } else {
    ElMessage.error('创建失败')
  }
}

// 批量打开
const handleBatchOpen = async () => {
  if (selectedIds.value.length === 0) return

  try {
    await browserStore.startAll(selectedIds.value)
    ElMessage.success(`已开始批量打开 ${selectedIds.value.length} 个浏览器`)
    clearSelection()
  } catch (error) {
    ElMessage.error('批量打开操作失败')
  }
}

// 批量关闭
const handleBatchClose = async () => {
  if (selectedIds.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要关闭选中的 ${selectedIds.value.length} 个浏览器吗？`,
      '批量关闭',
      {
        type: 'warning'
      }
    )
    await browserStore.stopAll(selectedIds.value)
    ElMessage.success('批量关闭指令已下发')
    clearSelection()
  } catch {
    // 用户取消
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要彻底删除选中的 <strong style="color: #ef4444">${selectedIds.value.length}</strong> 个浏览器环境及其本地数据吗？<br/><small style="color: #94a3b8">此操作不可恢复。</small>`,
      '批量删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: true,
        type: 'error'
      }
    )

    await browserStore.deleteBatch(selectedIds.value)
    ElMessage.success('批量删除完成')
    clearSelection()
  } catch {
    // 取消
  }
}

const handleStop = async (userId: string) => {
  try {
    const result = await browserStore.stopInstance(userId)
    if (result?.status !== 'success') {
      ElMessage.error('关闭失败')
    }
  } catch {
    // 取消
  }
}

const handleRun = async (userId: string) => {
  const result = await browserStore.startInstance(userId)
  if (result?.status !== 'success' && result?.status !== 'already_running') {
    ElMessage.error('打开失败')
  }
}

const handleDelete = async (userId: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要彻底删除浏览器 <strong style="color: #ef4444">${userId}</strong> 及其本地数据吗？<br/><small style="color: #94a3b8">此操作将永久清理磁盘空间，且不可恢复。</small>`,
      '危险操作',
      {
        confirmButtonText: '彻底删除',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: true,
        type: 'error'
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

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 40px;
  position: relative;
}

.batch-bar {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  background: var(--bg-color);
  padding: 8px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-color);
  z-index: 10;
  animation: slideInRight 0.3s ease;

  .selection-info {
    font-size: 13px;
    color: var(--text-color-secondary);

    .count {
      color: var(--primary-color);
      font-weight: 600;
      margin: 0 4px;
    }
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateY(-50%) translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateY(-50%) translateX(0);
  }
}

.user-id-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .browser-icon {
    font-size: 18px;
    color: var(--primary-color);
    opacity: 0.8;
  }
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 6px;

  &.success {
    color: var(--success-color);
    background: rgba(16, 185, 129, 0.1);
  }
  &.warning {
    color: var(--warning-color);
    background: rgba(245, 158, 11, 0.1);
  }
  &.info {
    color: var(--primary-color);
    background: rgba(59, 130, 246, 0.1);
  }
  &.gray {
    color: var(--text-color-secondary);
    background: var(--bg-color-soft);
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: currentColor;

    &.pulse {
      box-shadow: 0 0 0 0 currentColor;
      animation: statusPulse 2s infinite;
    }

    &.spinning {
      animation: dotScale 1s infinite alternate;
    }
  }
}

@keyframes statusPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
  }
}

@keyframes dotScale {
  from {
    transform: scale(0.8);
    opacity: 0.5;
  }
  to {
    transform: scale(1.2);
    opacity: 1;
  }
}

.form-tip {
  font-size: 12px;
  color: var(--text-color-placeholder);
  margin-top: 4px;
  line-height: 1.4;
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  padding: 2px 6px;
  background: var(--bg-color-soft);
  border-radius: 4px;
  color: var(--primary-color);
}

.text-secondary {
  color: var(--text-color-placeholder);
  font-size: 12px;
}
</style>
