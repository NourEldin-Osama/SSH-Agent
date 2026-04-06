import { Handle, Position } from 'reactflow'
import { useState } from 'react'
import { CommandCardFooter } from './CommandCardFooter'

const statusColors = {
  pending: 'bg-yellow-900/50 text-yellow-400 border-yellow-800',
  approved: 'bg-blue-900/50 text-blue-400 border-blue-800',
  executing: 'bg-orange-900/50 text-orange-400 border-orange-800',
  success: 'bg-green-900/50 text-green-400 border-green-800',
  failed: 'bg-red-900/50 text-red-400 border-red-800',
  denied: 'bg-gray-800 text-gray-400 border-gray-700',
  blocked: 'bg-gray-900 text-gray-600 border-gray-800',
}

export function CommandGroup({ data }) {
  const { groupId, commands, readOnly } = data
  const [expanded, setExpanded] = useState({})

  return (
    <div className="bg-[#1a1d27] border-2 border-dashed border-blue-800 rounded-xl p-4 min-w-[420px]">
      <Handle type="target" position={Position.Top} className="!bg-gray-600 !w-3 !h-3" />
      <div className="text-xs text-blue-400 font-medium mb-3">Group {groupId?.slice(0, 8)}</div>
      <div className="flex gap-3 items-start">
        {commands.map((cmd, idx) => {
          const leftHandleId = `g-${cmd.id}`
          const rightHandleId = idx < commands.length - 1 ? `g-${commands[idx + 1].id}` : undefined
          return (
            <div key={cmd.id} className="bg-[#0f1117] border border-gray-700 rounded-lg p-3 min-w-[220px] relative">
              <div className="flex items-center justify-between mb-1">
                <div className="text-xs text-gray-500">#{cmd.position_in_group ?? idx + 1}</div>
                <span className={`text-[10px] px-1.5 py-0.5 rounded border ${statusColors[cmd.status] || statusColors.pending}`}>
                  {cmd.status}
                </span>
              </div>
              <div className="text-sm text-white font-medium truncate">{cmd.title}</div>
              <code className="text-xs text-green-400 block mt-1 break-all">{cmd.command}</code>
              <button onClick={() => setExpanded((s) => ({ ...s, [cmd.id]: !s[cmd.id] }))} className="text-xs text-blue-400 mt-2">
                {expanded[cmd.id] ? 'Hide details' : 'Show details'}
              </button>
              {expanded[cmd.id] && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-400">{cmd.description}</p>
                  {cmd.expected_output ? <p className="text-xs text-gray-300"><span className="text-gray-500">Expected:</span> {cmd.expected_output}</p> : null}
                  {cmd.rollback_steps ? <p className="text-xs text-amber-300"><span className="text-amber-500">Rollback:</span> {cmd.rollback_steps}</p> : null}
                  {cmd.actual_output ? <pre className="text-xs text-gray-300 bg-[#1a1d27] p-2 rounded max-h-24 overflow-auto">{cmd.actual_output}</pre> : null}
                  {cmd.edited_by_user && cmd.original_command ? <p className="text-xs text-amber-300">Original: {cmd.original_command}</p> : null}
                </div>
              )}
              {cmd.status === 'pending' && !readOnly ? <CommandCardFooter command={cmd} /> : null}
              <Handle
                id={leftHandleId}
                type="target"
                position={Position.Left}
                className="!w-2 !h-2 !bg-gray-600"
              />
              {rightHandleId ? (
                <Handle
                  id={rightHandleId}
                  type="source"
                  position={Position.Right}
                  className="!w-2 !h-2 !bg-gray-600"
                />
              ) : null}
              {idx < commands.length - 1 && (
                <div className="absolute right-[-10px] top-1/2 text-gray-500">→</div>
              )}
            </div>
          )
        })}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-600 !w-3 !h-3" />
    </div>
  )
}
