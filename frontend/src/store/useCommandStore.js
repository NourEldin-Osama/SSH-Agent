import { create } from 'zustand'
import { commands } from '../lib/api'
import { toast } from 'sonner'

export const useCommandStore = create((set, get) => ({
  commands: [],
  loading: false,
  fetchCommands: async (sessionId) => {
    set({ loading: true })
    try {
      const { data } = await commands.list(sessionId)
      set({ commands: data, loading: false })
    } catch {
      set({ loading: false })
    }
  },
  addCommand: (cmd) => set((state) => ({ commands: [...state.commands, cmd] })),
  updateCommand: (id, updates) =>
    set((state) => ({
      commands: state.commands.map((c) => (c.id === id ? { ...c, ...updates } : c)),
    })),
  approveCommand: async (id) => {
    try {
      const { data } = await commands.approve(id)
      get().updateCommand(id, data)
      toast.success('Command approved')
    } catch {
      toast.error('Failed to approve command')
    }
  },
  denyCommand: async (id) => {
    try {
      const { data } = await commands.deny(id)
      get().updateCommand(id, data)
      toast.success('Command denied')
    } catch {
      toast.error('Failed to deny command')
    }
  },
  editCommand: async (id, data) => {
    try {
      const { data: updated } = await commands.edit(id, data)
      get().updateCommand(id, updated)
      toast.success('Command updated')
    } catch {
      toast.error('Failed to edit command')
    }
  },
  reexecuteCommand: async (id) => {
    try {
      const { data } = await commands.reexecute(id)
      get().updateCommand(id, data)
      toast.success('Command re-executed')
    } catch {
      toast.error('Failed to re-execute command')
    }
  },
  allowSession: async (id) => {
    try {
      const { data } = await commands.allowSession(id)
      toast.success('Allowed for session')
      return data
    } catch {
      toast.error('Failed to allow command for session')
      return null
    }
  },
}))
