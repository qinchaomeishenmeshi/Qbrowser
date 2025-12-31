<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card hover-card">
          <div
            class="stat-icon"
            style="background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%)"
          >
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
          <div
            class="stat-icon"
            style="background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%)"
          >
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
          <div
            class="stat-icon"
            style="background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%)"
          >
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
          <div
            class="stat-icon"
            style="background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%)"
          >
            <el-icon :size="28"><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">后端连接</div>
            <div class="stat-value">
              <span :class="['status-badge', appStore.backendConnected ? 'success' : 'danger']">
                {{ appStore.backendConnected ? '正常' : '断开' }}
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
          <span>快速操作</span>
        </div>
      </template>

      <el-space wrap>
        <el-button type="primary" :icon="Plus" @click="showStartDialog = true">
          新建实例
        </el-button>
        <el-button type="danger" :icon="VideoPause" @click="handleStopAll"> 停止全部 </el-button>
        <el-button :icon="Refresh" @click="handleRefresh" :loading="browserStore.loading">
          刷新状态
        </el-button>
        <div class="polling-indicator" :class="{ active: isPolling }">
          <span class="dot"></span>
          实时同步中
        </div>
      </el-space>
    </el-card>

    <!-- 活跃实例列表 -->
    <el-card class="instance-list" shadow="never">
      <template #header>
        <div class="card-header">
          <span>活跃实例</span>
          <el-tag type="info">{{ browserStore.activeCount }} 个</el-tag>
        </div>
      </template>

      <el-empty v-if="browserStore.activeInstances.length === 0" description="暂无活跃实例" />

      <el-table v-else :data="browserStore.activeInstances" style="width: 100%">
        <el-table-column prop="userId" label="用户 ID" width="200">
          <template #default="{ row }">
            <el-tag>{{ row }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态">
          <template #default>
            <span class="status-badge success">
              <el-icon><SuccessFilled /></el-icon>
              运行中
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="danger" text @click="handleStop(row)"> 停止 </el-button>
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
import {
  Monitor,
  ChromeFilled,
  Opportunity,
  Connection,
  Plus,
  VideoPause,
  Refresh,
  SuccessFilled
} from '@element-plus/icons-vue'

const browserStore = useBrowserStore()
const appStore = useAppStore()

const showStartDialog = ref(false)
const startForm = ref({
  userId: '',
  url: ''
})
const extensionCount = ref(0)

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
      ElMessage.success(`实例 ${userId} 已停止`)
    } else {
      ElMessage.error('停止失败')
    }
  } catch {
    // 取消
  }
}
</script>

<style scoped lang="scss">
.dashboard {
  padding: 20px;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  .el-card__body {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
  }
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 12px;
  color: white;
}

.stat-content {
  .stat-label {
    font-size: 14px;
    color: var(--text-color-secondary);
    margin-bottom: 8px;
  }

  .stat-value {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-color);
  }
}

.quick-actions,
.instance-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.polling-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-left: 12px;
  opacity: 0.6;
  transition: opacity 0.3s;

  &.active {
    opacity: 1;

    .dot {
      background-color: var(--el-color-success);
      box-shadow: 0 0 6px var(--el-color-success);
      animation: pulse 2s infinite;
    }
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--el-text-color-placeholder);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.5;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
