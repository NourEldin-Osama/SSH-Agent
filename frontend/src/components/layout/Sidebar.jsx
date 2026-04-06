import { useState } from 'react'
import { ChevronLeft, ChevronRight, Pencil } from 'lucide-react'

export function Sidebar({ sessions, activeSession, onSelectSession, onRenameSession, readOnly, open, onToggle }) {
  const [editingId, setEditingId] = useState(null)
  const [title, setTitle] = useState('')

  const startEdit = (session) => {
    setEditingId(session.id)
    setTitle(session.title || '')
  }

  const saveEdit = async (session) => {
    if (onRenameSession) {
      await onRenameSession(session.id, title)
    }
    setEditingId(null)
  }

  return (
    <div className={`border-l border-gray-800 bg-[#141620] transition-all duration-200 flex flex-col ${open ? 'w-72' : 'w-10'}`}>
      <button onClick={onToggle} className="p-2 text-gray-400 hover:text-white border-b border-gray-800 flex items-center justify-center">
        {open ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
      {open && (
        <div className="flex-1 overflow-y-auto">
          <div className="px-3 py-2 text-xs text-gray-500 uppercase font-medium">Sessions</div>
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`w-full text-left px-3 py-2.5 text-sm border-b border-gray-800/50 transition-colors ${
                activeSession?.id === session.id
                  ? 'bg-blue-900/30 text-blue-400 border-l-2 border-l-blue-500'
                  : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                {editingId === session.id ? (
                  <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onBlur={() => saveEdit(session)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveEdit(session)
                    }}
                    className="bg-[#0f1117] border border-gray-700 rounded px-2 py-1 text-xs text-white w-full"
                    autoFocus
                  />
                ) : (
                  <button onClick={() => onSelectSession(session)} className="truncate font-medium text-left flex-1">
                    {session.title || 'Untitled Session'}
                  </button>
                )}
                <button onClick={() => startEdit(session)} className="text-gray-500 hover:text-gray-300">
                  <Pencil className="w-3 h-3" />
                </button>
              </div>
              {session.ended_at && (
                <div className="text-[10px] text-amber-400 mt-1">Read-only</div>
              )}
              <div className="text-xs text-gray-600 mt-0.5 flex items-center justify-between">
                <span>{new Date(session.created_at).toLocaleString()}</span>
                <span>{session.command_count || 0} cmds</span>
              </div>
            </div>
          ))}
          {sessions.length === 0 && <div className="px-3 py-4 text-xs text-gray-600 text-center">No sessions yet</div>}
        </div>
      )}
    </div>
  )
}
