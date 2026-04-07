import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { sessions as sessionsApi } from '../lib/api'
import { AppHeader } from '../components/layout/AppHeader'
import { CalendarDays, Command, ExternalLink } from 'lucide-react'

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
              <div className="text-xs text-gray-500 flex items-center gap-3">
                <span className="inline-flex items-center gap-1"><CalendarDays className="w-3.5 h-3.5" />{new Date(s.created_at).toLocaleString()}</span>
                <span className="inline-flex items-center gap-1"><Command className="w-3.5 h-3.5" />{s.command_count || 0} cmds</span>
              </div>
            </div>
            <Link className="text-blue-400 text-sm inline-flex items-center gap-1" to={`/workspace/${s.server_id}?session_id=${s.id}`}>
              Open
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        ))}
      </div>
      </div>
    </div>
  )
}
