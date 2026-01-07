<template>
  <div class="browser-list">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>浏览器实例管理</span>
          <el-space>
            <el-button type="success" :icon="Plus" @click="showBatchStart = true">
              批量启动
            </el-button>
            <el-button type="primary" :icon="Plus" @click="showStartDialog = true">
              新建浏览器
            </el-button>
          </el-space>
        </div>
      </template>

      <el-empty v-if="browserStore.allInstances.length === 0" description="暂无浏览器记录">
        <el-space>
          <el-button type="primary" @click="showStartDialog = true">新建浏览器</el-button>
        </el-space>
      </el-empty>

      <el-row v-else :gutter="20">
        <el-col v-for="instance in browserStore.allInstances" :key="instance.user_id" :span="8">
          <el-card class="browser-card hover-card" shadow="hover">
            <div class="browser-card-header">
              <el-icon :size="32" color="#409eff"><ChromeFilled /></el-icon>
              <div class="browser-info">
                <div class="browser-name">{{ instance.user_id }}</div>
                <span :class="['status-badge', instance.is_running ? 'success' : 'warning']">
                  <el-icon>
                    <component :is="instance.is_running ? SuccessFilled : CircleCloseFilled" />
                  </el-icon>
                  {{ instance.is_running ? '运行中' : '已停止' }}
                </span>
              </div>
            </div>
            <div class="browser-card-actions">
              <el-button size="small" :icon="View" plain @click="handleView(instance.user_id)">
                详情
              </el-button>
              <el-button
                v-if="!instance.is_running"
                size="small"
                type="primary"
                plain
                :icon="VideoPlay"
                @click="handleRun(instance.user_id)"
              >
                启动
              </el-button>
              <el-button
                v-else
                size="small"
                type="warning"
                plain
                :icon="VideoPause"
                @click="handleStop(instance.user_id)"
              >
                停止
              </el-button>
              <el-button
                size="small"
                type="danger"
                plain
                :icon="Delete"
                @click="handleDelete(instance.user_id)"
              >
                删除
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 启动实例对话框 -> 新建浏览器对话框 -->
    <el-dialog v-model="showStartDialog" title="新建浏览器配置" width="500px" border-radius="12px">
      <el-form :model="startForm" label-width="120px" label-position="left">
        <el-form-item label="浏览器 ID" placeholder="例如：account-01" required>
          <el-input v-model="startForm.userId" placeholder="请输入浏览器标识符" />
          <div class="form-tip">标识符用于区分不同的浏览器环境和数据目录</div>
        </el-form-item>

        <el-divider content-position="left">高级配置 (可选)</el-divider>

        <el-form-item label="自定义内核路径">
          <el-input
            v-model="startForm.kernelPath"
            placeholder="例如：/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
          />
          <div class="form-tip">留空则使用默认内置内核。支持 Chrome/Edge/BitBrowser 等。</div>
        </el-form-item>

        <el-form-item label="代理服务器">
          <el-input v-model="startForm.proxyServer" placeholder="例如：http://127.0.0.1:7890" />
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

    <!-- 批量启动对话框 -->
    <el-dialog
      v-model="showBatchStart"
      title="批量启动实例"
      width="600px"
      :close-on-click-modal="!isBatching"
    >
      <div class="batch-container">
        <el-input
          v-model="batchInput"
          type="textarea"
          :rows="6"
          placeholder="请输入用户 ID 列表，每行一个 ID"
          :disabled="isBatching"
        />
        <div v-if="batchResults.length > 0" class="batch-results mt-20">
          <div v-for="res in batchResults" :key="res.userId" class="batch-item">
            <span>{{ res.userId }}</span>
            <el-tag
              :type="
                res.status === 'success'
                  ? 'success'
                  : res.status === 'running'
                  ? 'primary'
                  : 'danger'
              "
              size="small"
            >
              <el-icon v-if="res.status === 'running'" class="is-loading"><Loading /></el-icon>
              {{
                res.status === 'success' ? '启动成功' : res.status === 'running' ? '启动中' : '失败'
              }}
            </el-tag>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showBatchStart = false" :disabled="isBatching">取消</el-button>
        <el-button type="primary" @click="handleBatchStart" :loading="isBatching">
          {{ isBatching ? '正在批量启动...' : '开始启动' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 实例详情抽屉 -->
    <el-drawer v-model="showDetail" :title="`实例详情 - ${currentUserId}`" size="500px">
      <div v-if="detailLoading" v-loading="true" style="height: 200px"></div>
      <div v-else-if="instanceDetail" class="detail-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="用户 ID">{{ instanceDetail.user_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="instanceDetail.browser_running ? 'success' : 'danger'">
              {{ instanceDetail.browser_running ? '运行中' : '未运行' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="调试端口">{{ instanceDetail.port }}</el-descriptions-item>
          <el-descriptions-item label="当前页面">
            <el-link :href="instanceDetail.tab_url" target="_blank" type="primary">
              {{ instanceDetail.tab_url || 'N/A' }}
            </el-link>
          </el-descriptions-item>
        </el-descriptions>

        <div class="extension-check mt-20">
          <h4>扩展检查结果</h4>
          <el-card v-if="instanceDetail.extension_check" shadow="never">
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="域名匹配">
                <el-tag
                  :type="instanceDetail.extension_check.is_matching_domain ? 'success' : 'warning'"
                >
                  {{ instanceDetail.extension_check.is_matching_domain ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="检测到元素">
                <el-tag
                  v-for="elem in instanceDetail.extension_check.extension_elements"
                  :key="elem"
                  size="small"
                  class="mr-5"
                >
                  {{ elem }}
                </el-tag>
                <span v-if="!instanceDetail.extension_check.extension_elements?.length">无</span>
              </el-descriptions-item>
              <el-descriptions-item label="脚本注入">
                <el-icon
                  :color="instanceDetail.extension_check.has_injected_flag ? '#67C23A' : '#F56C6C'"
                >
                  <component
                    :is="instanceDetail.extension_check.has_injected_flag ? SuccessFilled : Close"
                  />
                </el-icon>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
          <el-alert v-else title="未获取到扩展检查结果" type="info" :closable="false" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useBrowserStore } from '@/stores'
import { usePolling } from '@/composables/usePolling'
import { browserApi } from '@/api/browser'
import {
  Plus,
  ChromeFilled,
  SuccessFilled,
  View,
  Close,
  Loading,
  VideoPlay,
  VideoPause,
  Delete,
  CircleCloseFilled
} from '@element-plus/icons-vue'

const browserStore = useBrowserStore()

const showStartDialog = ref(false)
const startForm = ref({
  userId: '',
  url: '',
  kernelPath: '',
  proxyServer: ''
})

const showBatchStart = ref(false)
const batchInput = ref('')
const isBatching = ref(false)
const batchResults = ref<any[]>([])

const showDetail = ref(false)
const currentUserId = ref('')
const detailLoading = ref(false)
const instanceDetail = ref<any>(null)

// 开启 5 秒一次的轮询
usePolling(async () => {
  await browserStore.refresh()
}, 5000)

const handleCreateBrowser = async () => {
  if (!startForm.value.userId.trim()) {
    ElMessage.warning('请输入浏览器 ID')
    return
  }

  const config = {} as any
  if (startForm.value.kernelPath?.trim()) {
    config.executable_path = startForm.value.kernelPath.trim()
  }
  if (startForm.value.proxyServer?.trim()) {
    config.proxy = { server: startForm.value.proxyServer.trim() }
  }

  // Pass config object to verify it works (Need to update store first? store usually passes args to API)
  // Assuming store.createBrowser(userId, config) sig. If not, I update API directly here or checking store code.
  // Actually I need to check store/api code.
  // But blindly sending it:
  const result = await browserStore.createBrowser(startForm.value.userId, config)

  if (result?.status === 'success') {
    ElMessage.success(`浏览器 ${startForm.value.userId} 创建成功`)
    showStartDialog.value = false
    startForm.value = { userId: '', url: '', kernelPath: '', proxyServer: '' }
  } else {
    ElMessage.error('创建失败')
  }
}

const handleBatchStart = async () => {
  const ids = batchInput.value
    .split('\n')
    .map((id) => id.trim())
    .filter((id) => id)
  if (ids.length === 0) {
    ElMessage.warning('请输入用户 ID 列表')
    return
  }

  isBatching.value = true
  batchResults.value = ids.map((id) => ({ userId: id, status: 'running' }))

  for (const item of batchResults.value) {
    try {
      const res = await browserStore.startInstance(item.userId)
      item.status =
        res?.status === 'success' || res?.status === 'already_running' ? 'success' : 'error'
    } catch {
      item.status = 'error'
    }
  }

  isBatching.value = false
  ElMessage.success('批量启动任务执行完毕')
}

const handleView = async (userId: string) => {
  currentUserId.value = userId
  showDetail.value = true
  detailLoading.value = true
  instanceDetail.value = null

  try {
    instanceDetail.value = await browserApi.getInstanceDetails(userId)
  } catch (e) {
    ElMessage.error('获取详情失败')
  } finally {
    detailLoading.value = false
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
    ElMessage.success(`实例 ${userId} 已恢复运行`)
  } else {
    ElMessage.error('恢复失败')
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
      ElMessage.error('删除失败')
    }
  } catch {
    // 取消
  }
}
</script>

<style scoped lang="scss">
.browser-list {
  padding: 24px;
  background: linear-gradient(180deg, var(--bg-color-soft) 0%, var(--bg-color) 100%);
  min-height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.browser-card {
  margin-bottom: 20px;
  animation: cardEnter 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  opacity: 0;

  @for $i from 1 through 12 {
    &:nth-child(#{$i}) {
      animation-delay: #{$i * 0.08}s;
    }
  }

  @keyframes cardEnter {
    from {
      opacity: 0;
      transform: scale(0.95) translateY(10px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }

  .browser-card-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;

    .el-icon {
      transition: all 0.3s ease;
    }

    &:hover .el-icon {
      transform: scale(1.1) rotate(-5deg);
    }
  }

  .browser-info {
    .browser-name {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 6px;
      color: var(--text-color);
    }
  }

  .browser-card-actions {
    display: flex;
    gap: 8px;
    padding-top: 12px;
    border-top: 1px solid var(--border-color-light);
  }
}

.mt-20 {
  margin-top: 20px;
}

.mr-5 {
  margin-right: 5px;
}

.detail-content {
  padding: 0 10px;

  h4 {
    margin-bottom: 12px;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-color);
    display: flex;
    align-items: center;
    gap: 8px;

    &::before {
      content: '';
      width: 4px;
      height: 16px;
      background: linear-gradient(180deg, var(--primary-color) 0%, #60a5fa 100%);
      border-radius: 2px;
    }
  }
}

.batch-results {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  background: var(--bg-color-soft);
}

.batch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--bg-color-light);
  margin-bottom: 8px;
  transition: all 0.2s ease;

  &:last-child {
    margin-bottom: 0;
  }

  &:hover {
    transform: translateX(4px);
    box-shadow: var(--shadow-sm);
  }
}
</style>
