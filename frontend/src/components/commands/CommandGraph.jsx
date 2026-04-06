import ReactFlow, { Background, Controls, MiniMap, MarkerType } from 'reactflow'
import 'reactflow/dist/style.css'
import { Play } from 'lucide-react'

import { CommandCard } from './CommandCard'
import { CommandGroup } from './CommandGroup'

const nodeTypes = {
  commandCard: CommandCard,
  commandGroup: CommandGroup,
}

function statusColor(status) {
  const colors = {
    pending: '#eab308',
    approved: '#3b82f6',
    executing: '#f97316',
    success: '#22c55e',
    failed: '#ef4444',
    denied: '#6b7280',
    blocked: '#1f2937',
  }
  return colors[status] || '#6b7280'
}

export function CommandGraph({ commands, session, onStartSession, readOnly = false }) {
  if (!session) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500 p-8">
        <p className="text-lg mb-2">No active session</p>
        <p className="text-sm mb-4">Commands will appear here as a graph</p>
        <button
          onClick={onStartSession}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          <Play className="w-4 h-4" />
          Start New Session
        </button>
      </div>
    )
  }

  const grouped = new Map()
  const singles = []

  commands.forEach((cmd) => {
    if (cmd.group_id) {
      if (!grouped.has(cmd.group_id)) grouped.set(cmd.group_id, [])
      grouped.get(cmd.group_id).push(cmd)
    } else {
      singles.push(cmd)
    }
  })

  const nodes = []
  const commandNodeIdByCommandId = new Map()

  singles.forEach((cmd, i) => {
    const nodeId = `cmd-${cmd.id}`
    commandNodeIdByCommandId.set(cmd.id, nodeId)
    nodes.push({
      id: nodeId,
      type: 'commandCard',
      position: {
        x: cmd.node_position_x ?? (i % 3) * 340 + 20,
        y: cmd.node_position_y ?? Math.floor(i / 3) * 250 + 20,
      },
      data: { command: cmd, readOnly },
    })
  })

  Array.from(grouped.entries()).forEach(([groupId, cmds], i) => {
    const sorted = [...cmds].sort((a, b) => (a.position_in_group || 0) - (b.position_in_group || 0))
    const groupNodeId = `group-${groupId}`

    sorted.forEach((cmd) => commandNodeIdByCommandId.set(cmd.id, groupNodeId))

    nodes.push({
      id: groupNodeId,
      type: 'commandGroup',
      position: {
        x: sorted[0].node_position_x ?? (i % 2) * 520 + 20,
        y: sorted[0].node_position_y ?? Math.floor(i / 2) * 280 + 20,
      },
      data: { groupId, commands: sorted, readOnly },
    })
  })

  const edges = []
  const edgeIds = new Set()

  commands
    .filter((cmd) => cmd.parent_id)
    .forEach((cmd) => {
      const source = commandNodeIdByCommandId.get(cmd.parent_id)
      const target = commandNodeIdByCommandId.get(cmd.id)
      if (!source || !target || source === target) return
      const edgeId = `edge-parent-${cmd.parent_id}-${cmd.id}`
      if (edgeIds.has(edgeId)) return
      edgeIds.add(edgeId)
      edges.push({
        id: edgeId,
        source,
        target,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#4b5563' },
        style: { stroke: '#4b5563', strokeWidth: 2 },
      })
    })

  Array.from(grouped.entries()).forEach(([groupId, cmds]) => {
    const sorted = [...cmds].sort((a, b) => (a.position_in_group || 0) - (b.position_in_group || 0))
    for (let i = 0; i < sorted.length - 1; i += 1) {
      const edgeId = `edge-group-${groupId}-${sorted[i].id}-${sorted[i + 1].id}`
      if (edgeIds.has(edgeId)) continue
      edgeIds.add(edgeId)
      edges.push({
        id: edgeId,
        source: `group-${groupId}`,
        target: `group-${groupId}`,
        sourceHandle: `g-${sorted[i].id}`,
        targetHandle: `g-${sorted[i + 1].id}`,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6b7280' },
        style: { stroke: '#6b7280', strokeWidth: 1.5 },
      })
    }
  })

  return (
    <div className="h-full bg-[#0f1117]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        defaultEdgeOptions={{
          markerEnd: { type: MarkerType.ArrowClosed, color: '#4b5563' },
          style: { stroke: '#4b5563', strokeWidth: 2 },
        }}
      >
        <Background color="#1f2937" gap={20} size={1} />
        <Controls className="!bg-[#1a1d27] !border-gray-700" />
        <MiniMap
          nodeStrokeColor="#374151"
          nodeColor={(n) => {
            if (n.id.startsWith('group-')) return '#1f2937'
            return statusColor(n.data?.command?.status)
          }}
          maskColor="rgba(0,0,0,0.3)"
          className="!bg-[#1a1d27] !border-gray-700"
        />
      </ReactFlow>
    </div>
  )
}
