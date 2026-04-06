import { useState } from 'react'
import { useServerStore } from '../../store/useServerStore'
import { ServerCard } from './ServerCard'

export function ServerList({ servers, onEdit }) {
  const { deleteServer, fetchServers } = useServerStore()
  const [statuses, setStatuses] = useState({})

  const handleDelete = async (id) => {
    if (confirm('Delete this server?')) {
      await deleteServer(id)
      await fetchServers()
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {servers.map((server) => (
        <ServerCard
          key={server.id}
          server={server}
          onEdit={() => onEdit(server)}
          onDelete={() => handleDelete(server.id)}
        />
      ))}
      {servers.length === 0 && (
        <div className="col-span-full text-center py-16 text-gray-500">
          <p className="text-lg">No servers configured</p>
          <p className="text-sm mt-1">Click "Add Server" to get started</p>
        </div>
      )}
    </div>
  )
}
