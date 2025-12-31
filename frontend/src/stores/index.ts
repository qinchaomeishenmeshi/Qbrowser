import { createPinia } from 'pinia'

export const pinia = createPinia()

export { useBrowserStore } from './browser'
export { useAppStore } from './app'
