import { create } from 'zustand'
import { permissions } from '../lib/api'

export const usePermissionStore = create((set) => ({
  rules: [],
  loading: false,
  fetchRules: async () => {
    set({ loading: true })
    try {
      const { data } = await permissions.list()
      set({ rules: data, loading: false })
    } catch {
      set({ loading: false })
    }
  },
  addRule: async (data) => {
    const { data: rule } = await permissions.create(data)
    set((state) => ({ rules: [...state.rules, rule] }))
  },
  updateRule: async (id, data) => {
    const { data: rule } = await permissions.update(id, data)
    set((state) => ({ rules: state.rules.map((r) => (r.id === id ? rule : r)) }))
  },
  deleteRule: async (id) => {
    await permissions.remove(id)
    set((state) => ({ rules: state.rules.filter((r) => r.id !== id) }))
  },
  checkCommand: async (command, serverId, sessionId) => {
    const { data } = await permissions.check(command, serverId, sessionId)
    return data.result
  },
}))
