import { createPinia } from 'pinia';
import { useAppStore } from './modules/app';
import { useBrowserStore } from './modules/browser';
import { useSchedulerStore } from './modules/scheduler';
import { useExtensionStore } from './modules/extension';
import { useSettingsStore } from './modules/settings';

// 创建 Pinia 实例
const pinia = createPinia();

// 导出 store 实例
export {
  pinia,
  useAppStore,
  useBrowserStore,
  useSchedulerStore,
  useExtensionStore,
  useSettingsStore
};

export default pinia;