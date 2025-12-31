import { onMounted, onUnmounted, ref } from 'vue'

export function usePolling(fn: () => Promise<void>, interval = 5000) {
  const timer = ref<ReturnType<typeof setInterval> | null>(null)
  const isPolling = ref(false)

  const startRestartPolling = () => {
    stopPolling()
    isPolling.value = true
    // 立即执行一次
    fn()
    timer.value = setInterval(async () => {
      await fn()
    }, interval)
  }

  const stopPolling = () => {
    if (timer.value) {
      clearInterval(timer.value)
      timer.value = null
    }
    isPolling.value = false
  }

  onMounted(() => {
    startRestartPolling()
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    isPolling,
    startRestartPolling,
    stopPolling
  }
}
