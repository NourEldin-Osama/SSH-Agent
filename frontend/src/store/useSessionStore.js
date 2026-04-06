import { create } from 'zustand'
import { sessions } from '../lib/api'

export const useSessionStore = create((set) => ({
  sessions: [],
  activeSession: null,
  readOnly: false,
  loading: false,
  fetchSessions: async (serverId) => {
    set({ loading: true })
    try {
      const { data } = await sessions.list(serverId)
      set({ sessions: data, loading: false })
    } catch {
      set({ loading: false })
    }
  },
  createSession: async (serverId, title) => {
    const { data } = await sessions.create(serverId, { title })
    set((state) => ({
      sessions: [data, ...state.sessions],
      activeSession: data,
      readOnly: false,
    }))
    return data
  },
  setActiveSession: (session) => set({ activeSession: session, readOnly: Boolean(session?.ended_at) }),
  endSession: async (id) => {
    const { data } = await sessions.end(id)
    set((state) => ({
      sessions: state.sessions.map((s) => (s.id === id ? data : s)),
      activeSession: state.activeSession?.id === id ? data : state.activeSession,
      readOnly: state.activeSession?.id === id ? true : state.readOnly,
    }))
  },
  updateSessionTitle: async (id, title) => {
    const { data } = await sessions.update(id, { title })
    set((state) => ({
      sessions: state.sessions.map((s) => (s.id === id ? data : s)),
    }))
  },
}))
