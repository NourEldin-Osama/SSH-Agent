import { create } from 'zustand'
import { servers } from '../lib/api'

export const useServerStore = create((set) => ({
  servers: [],
  loading: false,
  selectedServer: null,
  fetchServers: async () => {
    set({ loading: true })
    try {
      const { data } = await servers.list()
      set({ servers: data, loading: false })
    } catch {
      set({ loading: false })
    }
  },
  setSelectedServer: (server) => set({ selectedServer: server }),
  addServer: async (data) => {
    const { data: server } = await servers.create(data)
    set((state) => ({ servers: [...state.servers, server] }))
    return server
  },
  updateServer: async (id, data) => {
    const { data: server } = await servers.update(id, data)
    set((state) => ({
      servers: state.servers.map((s) => (s.id === id ? server : s)),
    }))
  },
  deleteServer: async (id) => {
    await servers.remove(id)
    set((state) => ({ servers: state.servers.filter((s) => s.id !== id) }))
  },
}))
