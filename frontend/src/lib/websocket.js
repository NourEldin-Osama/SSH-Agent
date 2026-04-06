class WSManager {
  constructor() {
    this.ws = null
    this.sessionId = null
    this.listeners = new Map()
  }

  connect(sessionId, onMessage) {
    if (this.ws && this.sessionId === sessionId) return
    this.disconnect()
    this.sessionId = sessionId
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/session/${sessionId}`)
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (onMessage) onMessage(data)
      const typeListeners = this.listeners.get(data.event) || []
      typeListeners.forEach((fn) => fn(data.data))
    }
    this.ws.onclose = () => {
      setTimeout(() => {
        if (this.sessionId === sessionId) this.connect(sessionId, onMessage)
      }, 3000)
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) this.listeners.set(event, [])
    this.listeners.get(event).push(callback)
  }

  off(event, callback) {
    const list = this.listeners.get(event)
    if (list) {
      this.listeners.set(event, list.filter((fn) => fn !== callback))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.listeners.clear()
    this.sessionId = null
  }
}

export const wsManager = new WSManager()
export default wsManager
