import { useState, useEffect } from 'react'
import { agents, permissions } from '../lib/api'
import { usePermissionStore } from '../store/usePermissionStore'
import { useServerStore } from '../store/useServerStore'
import { Plus, Trash2, Edit, Save, X, Bot, ShieldAlert, Globe, Server as ServerIcon, KeyRound } from 'lucide-react'
import { AppHeader } from '../components/layout/AppHeader'

export function Settings() {
  return (
    <div className="min-h-screen bg-[#0f1117]">
      <AppHeader breadcrumbs={[{ label: 'Settings' }]} />
      <main className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        <AgentConfigs />
        <WhitelistBlacklistManager />
      </main>
    </div>
  )
}

function AgentConfigs() {
  const [agentList, setAgentList] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ agent_name: '', api_key: '', base_url: '', is_active: true })
  const [localInstalled, setLocalInstalled] = useState({})

  useEffect(() => {
    agents.list().then(({ data }) => setAgentList(data))
    agents.localInstalled().then(({ data }) => {
      const map = {}
      ;(data.agents || []).forEach((a) => {
        map[a.agent_name] = a
      })
      setLocalInstalled(map)
    }).catch(() => setLocalInstalled({}))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (editing) {
      await agents.update(editing.id, form)
    } else {
      await agents.create(form)
    }
    const { data } = await agents.list()
    setAgentList(data)
    setShowForm(false)
    setEditing(null)
    setForm({ agent_name: '', api_key: '', base_url: '', is_active: true })
  }

  const handleEdit = (agent) => {
    setEditing(agent)
    setForm({ agent_name: agent.agent_name, api_key: '', base_url: agent.base_url || '', is_active: agent.is_active })
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (confirm('Delete this agent?')) {
      await agents.remove(id)
      const { data } = await agents.list()
      setAgentList(data)
    }
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2"><Bot className="w-5 h-5 text-cyan-300" />Agent Configurations</h2>
        <button
          onClick={() => { setShowForm(true); setEditing(null); setForm({ agent_name: '', api_key: '', base_url: '', is_active: true }) }}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          Add Agent
        </button>
      </div>
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-[#1a1d27] border border-gray-700 rounded-xl p-4 mb-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Agent Name</label>
              <select
                value={form.agent_name}
                onChange={(e) => setForm({ ...form, agent_name: e.target.value })}
                className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                required
              >
                <option value="">Select...</option>
                <option value="claude-code">Claude Code</option>
                <option value="opencode">OpenCode</option>
                <option value="codex">Codex</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">API Key</label>
              <input
                type="password"
                value={form.api_key}
                onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                required={!editing && !localInstalled[form.agent_name]?.installed}
                placeholder={editing ? 'Leave blank to keep current' : ''}
              />
              {localInstalled[form.agent_name]?.installed && (
                <p className="text-[11px] text-green-400 mt-1">
                  Local executable detected: {localInstalled[form.agent_name]?.executable}. API key optional.
                </p>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              placeholder="Base URL (optional)"
              className="flex-1 bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1">
              <Save className="w-4 h-4" />
              {editing ? 'Update' : 'Save'}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm">
              <X className="w-4 h-4" />
            </button>
          </div>
        </form>
      )}
      <div className="space-y-2">
        {agentList.map((agent) => (
          <div key={agent.id} className="bg-[#1a1d27] border border-gray-800 rounded-lg px-4 py-3 flex items-center justify-between">
            <div>
              <span className="text-white font-medium text-sm">{agent.agent_name}</span>
              {agent.base_url && <span className="text-xs text-gray-500 ml-2">{agent.base_url}</span>}
              <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${agent.is_active ? 'bg-green-900/50 text-green-400' : 'bg-gray-800 text-gray-500'}`}>
                {agent.is_active ? 'Active' : 'Inactive'}
              </span>
              {agent.installed_local && (
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-cyan-900/40 text-cyan-300">Local</span>
              )}
            </div>
            <div className="flex gap-1">
              <button onClick={() => handleEdit(agent)} className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded">
                <Edit className="w-4 h-4" />
              </button>
              <button onClick={() => handleDelete(agent.id)} className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
        {agentList.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-4">No agents configured</p>
        )}
      </div>
    </section>
  )
}

function WhitelistBlacklistManager() {
  const { rules, fetchRules, addRule, updateRule, deleteRule } = usePermissionStore()
  const { servers, fetchServers } = useServerStore()
  const [form, setForm] = useState({ rule_type: 'blacklist', match_type: 'exact', command_value: '', scope: 'global', server_id: null })
  const [editingId, setEditingId] = useState(null)

  useEffect(() => {
    fetchRules()
    fetchServers()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.scope === 'server' && !form.server_id) {
      alert('Please select a server for server-scoped rule')
      return
    }
    if (editingId) {
      await updateRule(editingId, form)
      setEditingId(null)
    } else {
      await addRule(form)
    }
    setForm({ ...form, command_value: '' })
  }

  const globalRules = rules.filter((r) => r.scope === 'global')
  const perServerRules = rules.filter((r) => r.scope === 'server')

  const renderRuleRow = (rule) => (
    <div key={rule.id} className="bg-[#1a1d27] border border-gray-800 rounded-lg px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className={`text-xs px-2 py-0.5 rounded-full ${
          rule.rule_type === 'blacklist' ? 'bg-red-900/50 text-red-400' : 'bg-green-900/50 text-green-400'
        }`}>
          {rule.rule_type}
        </span>
        <code className="text-sm text-gray-300 font-mono">{rule.command_value}</code>
        <span className="text-xs text-gray-500">({rule.match_type}, {rule.scope})</span>
        {rule.scope === 'server' && (
          <span className="text-xs text-blue-300">[{servers.find((s) => s.id === rule.server_id)?.label || `Server ${rule.server_id}`}]</span>
        )}
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => {
            setEditingId(rule.id)
            setForm({
              rule_type: rule.rule_type,
              match_type: rule.match_type,
              command_value: rule.command_value,
              scope: rule.scope,
              server_id: rule.server_id || null,
            })
          }}
          className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded"
        >
          <Edit className="w-4 h-4" />
        </button>
        <button onClick={() => deleteRule(rule.id)} className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )

  return (
    <section>
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><ShieldAlert className="w-5 h-5 text-amber-300" />Whitelist / Blacklist Rules</h2>
      <form onSubmit={handleSubmit} className="bg-[#1a1d27] border border-gray-700 rounded-xl p-4 mb-4 space-y-3">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Rule Type</label>
            <select
              value={form.rule_type}
              onChange={(e) => setForm({ ...form, rule_type: e.target.value })}
              className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="blacklist">Blacklist</option>
              <option value="whitelist">Whitelist</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Match Type</label>
            <select
              value={form.match_type}
              onChange={(e) => setForm({ ...form, match_type: e.target.value })}
              className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="exact">Exact</option>
              <option value="pattern">Pattern</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Scope</label>
            <select
              value={form.scope}
              onChange={(e) => setForm({ ...form, scope: e.target.value })}
              className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="global">Global</option>
              <option value="server">Per Server</option>
            </select>
          </div>
          {form.scope === 'server' && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">Server</label>
              <select
                value={form.server_id || ''}
                onChange={(e) => setForm({ ...form, server_id: e.target.value ? Number(e.target.value) : null })}
                className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                required
              >
                <option value="">Select server</option>
                {servers.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Command / Pattern</label>
            <input
              type="text"
              value={form.command_value}
              onChange={(e) => setForm({ ...form, command_value: e.target.value })}
              className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="rm -rf *"
              required
            />
          </div>
        </div>
        <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1">
          <Plus className="w-4 h-4" />
          {editingId ? 'Update Rule' : 'Add Rule'}
        </button>
      </form>
      <div className="space-y-4">
        <div>
          <h3 className="text-sm text-gray-400 mb-2 flex items-center gap-2"><Globe className="w-4 h-4" />Global Rules</h3>
          <div className="space-y-2">
            {globalRules.map(renderRuleRow)}
            {globalRules.length === 0 && <p className="text-sm text-gray-600">No global rules</p>}
          </div>
        </div>
        <div>
          <h3 className="text-sm text-gray-400 mb-2 flex items-center gap-2"><ServerIcon className="w-4 h-4" />Per-Server Rules</h3>
          <div className="space-y-2">
            {perServerRules.map(renderRuleRow)}
            {perServerRules.length === 0 && <p className="text-sm text-gray-600">No per-server rules</p>}
          </div>
        </div>
        {rules.length === 0 && <p className="text-sm text-gray-500 text-center py-4">No rules configured</p>}
      </div>
    </section>
  )
}
