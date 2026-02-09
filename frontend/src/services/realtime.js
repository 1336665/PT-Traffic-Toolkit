import { ref } from 'vue'

const connected = ref(false)
const lastError = ref(null)
const listeners = new Map()
let socket = null
let reconnectTimer = null
let reconnectDelay = 1000

function getWebSocketUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const base = `${protocol}://${window.location.host}/api/ws/realtime`
  const token = localStorage.getItem('token')
  const url = new URL(base)
  if (token) {
    url.searchParams.set('token', token)
  }
  return url.toString()
}

function emit(event, payload) {
  const handlers = listeners.get(event)
  if (!handlers) return
  for (const handler of handlers) {
    handler(payload)
  }
}

function connect() {
  if (socket && socket.readyState === WebSocket.OPEN) return
  if (socket && socket.readyState === WebSocket.CONNECTING) return

  const url = getWebSocketUrl()
  socket = new WebSocket(url)

  socket.onopen = () => {
    connected.value = true
    lastError.value = null
    reconnectDelay = 1000
  }

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      emit(data.type, data.payload)
    } catch (error) {
      console.error('Failed to parse realtime message', error)
    }
  }

  socket.onclose = () => {
    connected.value = false
    scheduleReconnect()
  }

  socket.onerror = (error) => {
    lastError.value = error
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    reconnectDelay = Math.min(reconnectDelay * 2, 10000)
    connect()
  }, reconnectDelay)
}

function subscribe(event, handler) {
  if (!listeners.has(event)) {
    listeners.set(event, new Set())
  }
  listeners.get(event).add(handler)
  return () => {
    listeners.get(event)?.delete(handler)
  }
}

function disconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (socket) {
    socket.close()
  }
  socket = null
  connected.value = false
}

export function useRealtime() {
  return {
    connected,
    lastError,
    connect,
    disconnect,
    subscribe,
  }
}
