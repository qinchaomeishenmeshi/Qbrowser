<template>
  <div class="settings-page">
    <el-card shadow="never">
      <template #header>
        <span>系统设置</span>
      </template>

      <el-form label-width="120px" style="max-width: 600px">
        <el-form-item label="后端地址">
          <el-input v-model="appStore.backendUrl" placeholder="http://127.0.0.1:8000" />
        </el-form-item>

        <el-form-item label="主题模式">
          <el-radio-group v-model="theme" @change="handleThemeChange">
            <el-radio-button value="light">浅色</el-radio-button>
            <el-radio-button value="dark">深色</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="语言">
          <el-select v-model="appStore.settings.language" disabled>
            <el-option value="zh-CN" label="简体中文" />
            <el-option value="en-US" label="English" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave">保存设置</el-button>
          <el-button @click="handleTest">测试连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" style="margin-top: 20px">
      <template #header>
        <span>关于</span>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="应用名称">QW-Browser</el-descriptions-item>
        <el-descriptions-item label="版本">1.0.0</el-descriptions-item>
        <el-descriptions-item label="技术栈">Tauri + Vue 3 + Element Plus</el-descriptions-item>
        <el-descriptions-item label="后端">FastAPI + Playwright</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores'

const appStore = useAppStore()
const theme = ref(appStore.settings.theme)

const handleThemeChange = (value: any) => {
  appStore.setTheme(value as 'light' | 'dark')
}

const handleSave = () => {
  ElMessage.success('设置已保存')
}

const handleTest = async () => {
  const connected = await appStore.checkBackendHealth()
  if (connected) {
    ElMessage.success('连接成功')
  } else {
    ElMessage.error('连接失败，请检查后端地址')
  }
}
</script>

<style scoped lang="scss">
.settings-page {
  padding: 24px;
  background: linear-gradient(180deg, var(--bg-color-soft) 0%, var(--bg-color) 100%);
  min-height: 100%;

  .el-card {
    margin-bottom: 24px;

    :deep(.el-card__header) {
      padding: 16px 20px;
      background: var(--bg-color-soft);
      font-weight: 600;
      border-bottom: 1px solid var(--border-color);
    }

    :deep(.el-card__body) {
      padding: 24px;
    }
  }

  /* 关于卡片装饰 */
  .el-card:last-child {
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: -50%;
      right: -20%;
      width: 200px;
      height: 200px;
      background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
      pointer-events: none;
    }
  }

  :deep(.el-form-item) {
    margin-bottom: 24px;
  }

  :deep(.el-descriptions) {
    .el-descriptions__label {
      font-weight: 500;
      color: var(--text-color-secondary);
    }

    .el-descriptions__content {
      color: var(--text-color);
    }
  }
}
</style>
