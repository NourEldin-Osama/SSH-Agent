import { useState } from 'react'

export function PermissionRuleForm({ onSubmit, onCancel }) {
  const [form, setForm] = useState({ rule_type: 'blacklist', match_type: 'exact', command_value: '', scope: 'global', server_id: null })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <select
          value={form.rule_type}
          onChange={(e) => setForm({ ...form, rule_type: e.target.value })}
          className="bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
        >
          <option value="blacklist">Blacklist</option>
          <option value="whitelist">Whitelist</option>
        </select>
        <select
          value={form.match_type}
          onChange={(e) => setForm({ ...form, match_type: e.target.value })}
          className="bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
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
        className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
        required
      />
      <div className="flex gap-2">
        <button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium">
          Save
        </button>
        <button type="button" onClick={onCancel} className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm font-medium">
          Cancel
        </button>
      </div>
    </form>
  )
}
