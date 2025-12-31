<template>
  <div class="extensions-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>扩展管理</span>
          <el-button :icon="Refresh" @click="fetchData" :loading="loading">刷新</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="扩展服务状态">
          <el-tag :type="statusTagType">{{ extensionStatus?.status || '未知' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="活跃浏览器数">
          {{ extensionStatus?.total_browsers || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="已配置扩展" :span="2">
          <el-tag
            v-for="ext in extensionStatus?.configured_extensions"
            :key="ext"
            class="extension-tag"
          >
            {{ ext }}
          </el-tag>
          <span v-if="!extensionStatus?.configured_extensions?.length">暂无扩展</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { extensionApi } from '@/api'
import type { ExtensionStatus } from '@/types/api'
import { Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const extensionStatus = ref<ExtensionStatus | null>(null)

const statusTagType = computed(() => {
  if (extensionStatus.value?.status === 'running') return 'success'
  if (extensionStatus.value?.status === 'stopped') return 'danger'
  return 'info'
})

const fetchData = async () => {
  loading.value = true
  try {
    extensionStatus.value = await extensionApi.getStatus()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped lang="scss">
.extensions-page {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.extension-tag {
  margin-right: 8px;
}
</style>
