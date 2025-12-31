<template>
  <div class="logs-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div class="header-actions">
            <el-select v-model="limit" size="small" style="width: 120px" @change="fetchLogs">
              <el-option :value="10" label="最近 10 条" />
              <el-option :value="50" label="最近 50 条" />
              <el-option :value="100" label="最近 100 条" />
            </el-select>
            <el-button :icon="Refresh" @click="handleManualRefresh" :loading="loading"
              >刷新</el-button
            >
          </div>
        </div>
      </template>

      <el-table :data="logs" style="width: 100%" v-loading="loading">
        <el-table-column prop="timestamp" label="时间" width="200">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="component" label="组件" width="150" />
        <el-table-column prop="message" label="消息" />
      </el-table>

      <el-empty v-if="logs.length === 0 && !loading" description="暂无日志记录" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { systemApi } from '@/api'
import type { SystemLog } from '@/types/api'
import { Refresh } from '@element-plus/icons-vue'
import { usePolling } from '@/composables/usePolling'

const loading = ref(false)
const logs = ref<SystemLog[]>([])
const limit = ref(10)

const fetchLogs = async () => {
  // 手动点击刷新才设置 loading 状态，轮询不设置
  try {
    const result = await systemApi.getLogs(limit.value)
    logs.value = result.logs
  } catch (e) {
    console.error(e)
  }
}

// 开启 10 秒轮询
usePolling(fetchLogs, 10000)

const handleManualRefresh = async () => {
  loading.value = true
  await fetchLogs()
  loading.value = false
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const getLevelType = (level: string) => {
  switch (level) {
    case 'ERROR':
      return 'danger'
    case 'WARNING':
      return 'warning'
    case 'INFO':
      return 'success'
    default:
      return 'info'
  }
}
</script>

<style scoped lang="scss">
.logs-page {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style>
