import { useState, useEffect } from 'react'
import { useServerStore } from '../../store/useServerStore'
import { X } from 'lucide-react'

export function ServerForm({ server, onClose, isEdit }) {
  const { addServer, updateServer, fetchServers } = useServerStore()
  const [form, setForm] = useState({
    label: '',
    hostname: '',
    port: 22,
    username: '',
    auth_method: 'password',
    password: '',
    ssh_key: '',
    passphrase: '',
    tags: [],
  })
  const [tagInput, setTagInput] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (server) {
      setForm({
        label: server.label || '',
        hostname: server.hostname || '',
        port: server.port || 22,
        username: server.username || '',
        auth_method: server.auth_method || 'password',
        password: '',
        ssh_key: '',
        passphrase: '',
        tags: server.tags || [],
      })
    }
  }, [server])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (isEdit) {
        await updateServer(server.id, form)
      } else {
        await addServer(form)
      }
      await fetchServers()
      onClose()
    } catch (err) {
      console.error(err)
    }
    setSaving(false)
  }

  const addTag = () => {
    if (tagInput && !form.tags.includes(tagInput)) {
      setForm({ ...form, tags: [...form.tags, tagInput] })
      setTagInput('')
    }
  }

  const removeTag = (tag) => {
    setForm({ ...form, tags: form.tags.filter((t) => t !== tag) })
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#1a1d27] rounded-xl border border-gray-700 w-full max-w-lg mx-4 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">{isEdit ? 'Edit Server' : 'Add Server'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Label</label>
            <input
              type="text"
              value={form.label}
              onChange={(e) => setForm({ ...form, label: e.target.value })}
              className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Hostname</label>
              <input
                type="text"
                value={form.hostname}
                onChange={(e) => setForm({ ...form, hostname: e.target.value })}
                className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Port</label>
              <input
                type="number"
                value={form.port}
                onChange={(e) => setForm({ ...form, port: parseInt(e.target.value) })}
                className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Username</label>
            <input
              type="text"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Auth Method</label>
            <select
              value={form.auth_method}
              onChange={(e) => setForm({ ...form, auth_method: e.target.value })}
              className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="password">Password</option>
              <option value="ssh_key">SSH Key</option>
              <option value="ssh_key_passphrase">SSH Key + Passphrase</option>
            </select>
          </div>
          {form.auth_method === 'password' && (
            <div>
              <label className="block text-sm text-gray-400 mb-1">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                required={!isEdit}
              />
            </div>
          )}
          {form.auth_method.includes('ssh_key') && (
            <div>
              <label className="block text-sm text-gray-400 mb-1">SSH Key Path</label>
              <input
                type="text"
                value={form.ssh_key}
                onChange={(e) => setForm({ ...form, ssh_key: e.target.value })}
                className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="~/.ssh/id_rsa"
                required={!isEdit}
              />
            </div>
          )}
          {form.auth_method === 'ssh_key_passphrase' && (
            <div>
              <label className="block text-sm text-gray-400 mb-1">Passphrase</label>
              <input
                type="password"
                value={form.passphrase}
                onChange={(e) => setForm({ ...form, passphrase: e.target.value })}
                className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                required={!isEdit}
              />
            </div>
          )}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Tags</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTag() } }}
                className="flex-1 bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="Add tag..."
              />
              <button type="button" onClick={addTag} className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm">
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {form.tags.map((tag) => (
                <span key={tag} className="bg-blue-900/50 text-blue-300 px-2 py-1 rounded text-xs flex items-center gap-1">
                  {tag}
                  <button type="button" onClick={() => removeTag(tag)} className="hover:text-white">×</button>
                </span>
              ))}
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm font-medium">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium disabled:opacity-50">
              {saving ? 'Saving...' : isEdit ? 'Update' : 'Add Server'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
