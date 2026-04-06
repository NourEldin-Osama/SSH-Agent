import { Handle, Position } from 'reactflow'
import { useState } from 'react'
import { CommandCardFooter } from './CommandCardFooter'
import { ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'

const statusColors = {
  pending: 'bg-yellow-900/50 text-yellow-400 border-yellow-800',
  approved: 'bg-blue-900/50 text-blue-400 border-blue-800',
  executing: 'bg-orange-900/50 text-orange-400 border-orange-800',
  success: 'bg-green-900/50 text-green-400 border-green-800',
  failed: 'bg-red-900/50 text-red-400 border-red-800',
  denied: 'bg-gray-800 text-gray-400 border-gray-700',
  blocked: 'bg-gray-900 text-gray-600 border-gray-800',
}

export function CommandCard({ data }) {
  const { command, readOnly } = data
  const [collapsed, setCollapsed] = useState(true)
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(command.command)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleAskAI = () => {
    window.dispatchEvent(new CustomEvent('ask-ai', { detail: command }))
  }

  return (
    <div className={`command-card bg-[#1a1d27] border border-gray-700 rounded-xl shadow-xl status-${command.status}`}>
      <Handle type="target" position={Position.Top} className="!bg-gray-600 !w-3 !h-3" />
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${statusColors[command.status] || statusColors.pending}`}>
              {command.status}
            </span>
            {command.is_risky && (
              <span className="text-xs bg-red-900/50 text-red-400 px-2 py-0.5 rounded-full">Risky</span>
            )}
          </div>
          <button onClick={() => setCollapsed(!collapsed)} className="text-gray-500 hover:text-gray-300">
            {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </button>
        </div>
        <h4 className="text-white font-medium text-sm mb-1">{command.title}</h4>
        {!collapsed && (
          <>
            <p className="text-xs text-gray-400 mb-3">{command.description}</p>
            <div className="bg-[#0f1117] rounded-lg p-3 mb-3 relative group">
              <code className="text-xs text-green-400 font-mono break-all">{command.command}</code>
              <button
                onClick={handleCopy}
                className="absolute top-2 right-2 p-1 opacity-0 group-hover:opacity-100 transition-opacity text-gray-500 hover:text-white"
              >
                {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
            {command.expected_output && (
              <div className="mb-3">
                <span className="text-xs text-gray-500">Expected:</span>
                <p className="text-xs text-gray-300 mt-0.5">{command.expected_output}</p>
              </div>
            )}
            {command.is_risky && command.rollback_steps && (
              <div className="mb-3">
                <span className="text-xs text-red-400">Rollback:</span>
                <p className="text-xs text-gray-300 mt-0.5">{command.rollback_steps}</p>
              </div>
            )}
            {command.actual_output && (
              <div className="mb-3">
                <span className="text-xs text-gray-500">Output:</span>
                <pre className="text-xs text-gray-300 mt-0.5 bg-[#0f1117] p-2 rounded-lg overflow-auto max-h-32 font-mono">
                  {command.actual_output}
                </pre>
              </div>
            )}
            {command.edited_by_user && command.original_command && (
              <div className="mb-3">
                <span className="text-xs text-amber-400">Original:</span>
                <code className="text-xs text-amber-300 block mt-0.5 bg-amber-900/20 p-2 rounded font-mono">
                  {command.original_command}
                </code>
              </div>
            )}
          </>
        )}
        {command.status === 'pending' && !readOnly && <CommandCardFooter command={command} />}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-600 !w-3 !h-3" />
    </div>
  )
}
