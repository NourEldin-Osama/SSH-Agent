import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { sessions as sessionsApi } from '../lib/api'
import { AppHeader } from '../components/layout/AppHeader'

export function SessionsPage() {
  const { serverId } = useParams()
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    if (!serverId) return
    sessionsApi.list(serverId).then(({ data }) => setSessions(data)).catch(() => setSessions([]))
  }, [serverId])

  return (
    <div className="min-h-screen bg-[#0f1117] text-white p-6">
      <AppHeader breadcrumbs={[{ label: 'Sessions' }]} />
      <div className="max-w-4xl mx-auto pt-6">
      <h1 className="text-xl font-bold mb-4">Sessions</h1>
      <div className="space-y-2">
        {sessions.map((s) => (
          <div key={s.id} className="bg-[#1a1d27] border border-gray-800 rounded-lg px-4 py-3 flex justify-between">
            <div>
              <div className="font-medium">{s.title || 'Untitled Session'}</div>
              <div className="text-xs text-gray-500">{new Date(s.created_at).toLocaleString()} • {s.command_count || 0} cmds</div>
            </div>
            <Link className="text-blue-400 text-sm" to={`/workspace/${s.server_id}?session_id=${s.id}`}>Open</Link>
          </div>
        ))}
      </div>
      </div>
    </div>
  )
}
