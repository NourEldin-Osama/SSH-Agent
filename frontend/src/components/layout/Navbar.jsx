import { AlertTriangle, Bell, ChevronRight, Home } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

export function Navbar({ server, dangerMode, onDangerModeToggle }) {
  const [showConfirm, setShowConfirm] = useState(false)

  const handleNotificationClick = async () => {
    if (!('Notification' in window)) return
    if (Notification.permission === 'default') {
      await Notification.requestPermission()
    }
  }

  const handleDangerToggle = () => {
    if (!dangerMode) {
      setShowConfirm(true)
    } else {
      onDangerModeToggle()
    }
  }

  return (
    <>
      <header className="bg-[#1a1d27] border-b border-gray-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <nav className="flex items-center gap-1 text-sm">
            <Link to="/" className="text-gray-400 hover:text-white flex items-center gap-1">
              <Home className="w-3.5 h-3.5" />
              Home
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
            <Link to={`/sessions/${server.id}`} className="text-gray-400 hover:text-white">
              Sessions
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
            <span className="text-gray-500">Workspace</span>
            <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
            <h2 className="text-white font-semibold">{server.label}</h2>
          </nav>
          <span className="bg-green-900/50 text-green-400 text-xs px-2 py-1 rounded-full">
            {server.hostname}:{server.port}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleDangerToggle}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              dangerMode
                ? 'bg-red-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-red-400 hover:bg-red-900/30'
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            Danger Mode
          </button>
          <button onClick={handleNotificationClick} className="p-2 text-gray-400 hover:text-white transition-colors relative">
            <Bell className="w-5 h-5" />
          </button>
        </div>
      </header>
      {showConfirm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-[#1a1d27] border border-red-800 rounded-xl p-6 max-w-md mx-4">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-red-400" />
              <h3 className="text-lg font-semibold text-white">Enable Danger Mode?</h3>
            </div>
            <p className="text-gray-400 text-sm mb-6">
              All commands will execute without approval. This can cause irreversible changes to your server. Are you sure?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={() => { onDangerModeToggle(); setShowConfirm(false) }}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 rounded-lg text-sm font-medium"
              >
                Enable Danger Mode
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
