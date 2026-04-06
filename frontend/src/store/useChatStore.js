import { create } from 'zustand'
import { chat } from '../lib/api'

export const useChatStore = create((set) => ({
  messages: [],
  loading: false,
  fetchMessages: async (sessionId) => {
    set({ loading: true })
    try {
      const { data } = await chat.getMessages(sessionId)
      set({ messages: data, loading: false })
    } catch {
      set({ loading: false })
    }
  },
  addMessage: async (sessionId, role, content) => {
    const { data } = await chat.sendMessage(sessionId, { role, content })
    set((state) => ({ messages: [...state.messages, data] }))
    return data
  },
  appendMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
}))
