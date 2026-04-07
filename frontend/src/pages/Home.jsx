import { useEffect, useState } from 'react'
import { useServerStore } from '../store/useServerStore'
import { ServerList } from '../components/servers/ServerList'
import { ServerForm } from '../components/servers/ServerForm'
import { Plus, Server, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { AppHeader } from '../components/layout/AppHeader'

export function Home() {
  const { servers, fetchServers } = useServerStore()
  const [showForm, setShowForm] = useState(false)
  const [editingServer, setEditingServer] = useState(null)

  useEffect(() => {
    fetchServers()
  }, [])

  const handleEdit = (server) => {
    setEditingServer(server)
    setShowForm(true)
  }

  const handleCloseForm = () => {
    setShowForm(false)
    setEditingServer(null)
  }

  return (
    <div className="min-h-screen bg-[#0f1117]">
      <AppHeader breadcrumbs={[{ label: 'Servers' }]} />
      <section className="border-b border-gray-800 bg-gradient-to-r from-cyan-900/20 via-blue-900/10 to-transparent">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Server className="w-7 h-7 text-cyan-400" />
              <h1 className="text-2xl font-bold text-white">SSH Agent Commander</h1>
            </div>
            <p className="text-sm text-gray-400">Manage servers, run AI-assisted sessions, or execute manual SSH terminal commands.</p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Server
          </button>
        </div>
      </section>
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-gray-400">{servers.length} server{servers.length !== 1 ? 's' : ''} configured</p>
          <Link to="/settings" className="text-sm text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1">
            Global Settings
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        <ServerList servers={servers} onEdit={handleEdit} />
      </main>
      {showForm && (
        <ServerForm
          server={editingServer}
          onClose={handleCloseForm}
          isEdit={!!editingServer}
        />
      )}
    </div>
  )
}
