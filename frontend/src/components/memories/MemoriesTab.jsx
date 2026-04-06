import { useEffect, useState } from 'react'
import { memories } from '../../lib/api'
import { MemoryItem } from './MemoryItem'

export function MemoriesTab({ serverId }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    if (!serverId) return
    memories.list(serverId).then(({ data }) => setItems(data))
  }, [serverId])

  const refresh = async () => {
    const { data } = await memories.list(serverId)
    setItems(data)
  }

  return (
    <div className="space-y-3">
      {items.map((m) => (
        <MemoryItem
          key={m.id}
          memory={m}
          onDelete={async () => { await memories.remove(m.id); refresh() }}
          onApprove={async () => { await memories.approve(m.id); refresh() }}
        />
      ))}
      {!items.length && <p className="text-sm text-gray-500">No memories for this server</p>}
    </div>
  )
}
