import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { servers } from '../../lib/api'
import { Edit, Trash2, ExternalLink, Wifi, WifiOff } from 'lucide-react'

export function ServerCard({ server, onEdit, onDelete }) {
  const [status, setStatus] = useState('unknown')

  useEffect(() => {
    const check = async () => {
      try {
        const { data } = await servers.status(server.id)
        setStatus(data.status)
      } catch {
        setStatus('unreachable')
      }
    }
    check()
  }, [server.id])

  return (
    <div className="bg-[#1a1d27] border border-gray-800 rounded-xl p-5 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-white font-semibold">{server.label}</h3>
          <p className="text-sm text-gray-400">{server.hostname}:{server.port}</p>
        </div>
        <div className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${
          status === 'reachable' ? 'bg-green-900/50 text-green-400' :
          status === 'unreachable' ? 'bg-red-900/50 text-red-400' :
          'bg-gray-800 text-gray-500'
        }`}>
          {status === 'reachable' ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          {status === 'reachable' ? 'Reachable' : status === 'unreachable' ? 'Offline' : '...'}
        </div>
      </div>
      <div className="flex flex-wrap gap-1 mb-4">
        {server.tags?.map((tag) => (
          <span key={tag} className="bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded text-xs">{tag}</span>
        ))}
      </div>
      {status === 'reachable' && (
        <p className="text-xs text-cyan-400 mb-3">Host/port reachable. SSH auth is validated when first command runs.</p>
      )}
      {status === 'unreachable' && (
        <p className="text-xs text-amber-400 mb-3">Server unreachable — check network, host, or port</p>
      )}
      <div className="flex items-center gap-2">
        <Link
          to={`/workspace/${server.id}`}
          className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          Open Workspace
        </Link>
        <button onClick={onEdit} className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
          <Edit className="w-4 h-4" />
        </button>
        <button onClick={onDelete} className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition-colors">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
