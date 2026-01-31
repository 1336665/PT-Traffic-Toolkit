import { ref, reactive } from 'vue'

const toasts = reactive([])
let toastId = 0

export function useToast() {
  const addToast = (options) => {
    const id = ++toastId
    const toast = {
      id,
      type: options.type || 'info',
      title: options.title || '',
      message: options.message || '',
      duration: options.duration ?? 4000,
      progress: 100,
    }

    toasts.push(toast)

    if (toast.duration > 0) {
      const startTime = Date.now()
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime
        const remaining = toast.duration - elapsed
        const toastItem = toasts.find(t => t.id === id)
        if (toastItem) {
          toastItem.progress = Math.max(0, (remaining / toast.duration) * 100)
        }

        if (remaining <= 0) {
          clearInterval(interval)
          removeToast(id)
        }
      }, 50)
    }

    return id
  }

  const removeToast = (id) => {
    const index = toasts.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.splice(index, 1)
    }
  }

  const success = (message, options = {}) => addToast({ ...options, type: 'success', message })
  const error = (message, options = {}) => addToast({ ...options, type: 'error', message })
  const warning = (message, options = {}) => addToast({ ...options, type: 'warning', message })
  const info = (message, options = {}) => addToast({ ...options, type: 'info', message })

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info,
  }
}

// Singleton instance for global use
let globalToast = null

export function getToast() {
  if (!globalToast) {
    globalToast = useToast()
  }
  return globalToast
}

export default useToast
