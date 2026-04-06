import { useEffect, useState } from 'react'
import { useServerStore } from '../store/useServerStore'
import { ServerList } from '../components/servers/ServerList'
import { ServerForm } from '../components/servers/ServerForm'
import { Plus, Server } from 'lucide-react'
import { Link } from 'react-router-dom'

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
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Server className="w-7 h-7 text-blue-400" />
            <h1 className="text-xl font-bold text-white">SSH Agent Commander</h1>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/settings" className="text-sm text-gray-400 hover:text-white transition-colors px-3 py-2">
              Settings
            </Link>
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Server
            </button>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-8">
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
