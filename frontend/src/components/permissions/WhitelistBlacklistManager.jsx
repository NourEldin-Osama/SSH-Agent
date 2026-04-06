import { useState } from 'react'
import { Plus, Trash2, Edit } from 'lucide-react'

export function WhitelistBlacklistManager({ rules, onAdd, onUpdate, onDelete }) {
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ rule_type: 'blacklist', match_type: 'exact', command_value: '', scope: 'global', server_id: null })

  const handleSubmit = (e) => {
    e.preventDefault()
    onAdd(form)
    setForm({ rule_type: 'blacklist', match_type: 'exact', command_value: '', scope: 'global', server_id: null })
    setShowForm(false)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-md font-semibold text-white">Permission Rules</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          Add Rule
        </button>
      </div>
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-[#1a1d27] border border-gray-700 rounded-xl p-4 mb-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <select
              value={form.rule_type}
              onChange={(e) => setForm({ ...form, rule_type: e.target.value })}
              className="bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="blacklist">Blacklist</option>
              <option value="whitelist">Whitelist</option>
            </select>
            <select
              value={form.match_type}
              onChange={(e) => setForm({ ...form, match_type: e.target.value })}
              className="bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="exact">Exact</option>
              <option value="pattern">Pattern</option>
            </select>
          </div>
          <input
            type="text"
            value={form.command_value}
            onChange={(e) => setForm({ ...form, command_value: e.target.value })}
            placeholder="Command or pattern"
            className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            required
          />
          <select
            value={form.scope}
            onChange={(e) => setForm({ ...form, scope: e.target.value })}
            className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="global">Global</option>
            <option value="server">Per Server</option>
          </select>
          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium">
            Add Rule
          </button>
        </form>
      )}
      <div className="space-y-2">
        {rules?.map((rule) => (
          <div key={rule.id} className="bg-[#1a1d27] border border-gray-800 rounded-lg px-4 py-3 flex items-center justify-between">
            <div>
              <span className={`text-xs px-2 py-0.5 rounded-full mr-2 ${
                rule.rule_type === 'blacklist' ? 'bg-red-900/50 text-red-400' : 'bg-green-900/50 text-green-400'
              }`}>
                {rule.rule_type}
              </span>
              <code className="text-sm text-gray-300 font-mono">{rule.command_value}</code>
              <span className="text-xs text-gray-500 ml-2">({rule.scope})</span>
            </div>
            <button onClick={() => onDelete(rule.id)} className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
