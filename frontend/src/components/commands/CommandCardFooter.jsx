import { useCommandStore } from '../../store/useCommandStore'
import { Check, X, Edit3, MessageSquare, Shield } from 'lucide-react'
import { useState } from 'react'

export function CommandCardFooter({ command }) {
  const { approveCommand, denyCommand, editCommand, allowSession } = useCommandStore()
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(command.command)

  const handleApprove = () => approveCommand(command.id)
  const handleDeny = () => denyCommand(command.id)

  const handleEdit = async () => {
    if (editValue !== command.command) {
      await editCommand(command.id, { command: editValue })
      const shouldNotify = window.confirm('Notify AI of changes?')
      if (shouldNotify) {
        window.dispatchEvent(new CustomEvent('notify-ai-edit', { detail: command }))
      }
    }
    setEditing(false)
  }

  const handleAllowSession = async () => {
    await allowSession(command.id)
  }

  if (editing) {
    return (
      <div className="mt-3 pt-3 border-t border-gray-700">
        <textarea
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="w-full bg-[#0f1117] border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-green-400 font-mono focus:outline-none focus:border-blue-500 resize-none"
          rows={2}
        />
        <div className="flex gap-2 mt-2">
          <button onClick={handleEdit} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-1.5 rounded text-xs font-medium">
            Save
          </button>
          <button onClick={() => setEditing(false)} className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-1.5 rounded text-xs font-medium">
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-700 flex flex-wrap gap-1.5">
      <button
        onClick={handleApprove}
        className="flex items-center gap-1 bg-green-700 hover:bg-green-600 text-white px-2.5 py-1.5 rounded text-xs font-medium transition-colors"
      >
        <Check className="w-3 h-3" />
        Approve
      </button>
      <button
        onClick={handleDeny}
        className="flex items-center gap-1 bg-red-700 hover:bg-red-600 text-white px-2.5 py-1.5 rounded text-xs font-medium transition-colors"
      >
        <X className="w-3 h-3" />
        Deny
      </button>
      <button
        onClick={() => setEditing(true)}
        className="flex items-center gap-1 bg-gray-700 hover:bg-gray-600 text-white px-2.5 py-1.5 rounded text-xs font-medium transition-colors"
      >
        <Edit3 className="w-3 h-3" />
        Edit
      </button>
      <button onClick={() => window.dispatchEvent(new CustomEvent('ask-ai', { detail: command }))} className="flex items-center gap-1 bg-gray-700 hover:bg-gray-600 text-white px-2.5 py-1.5 rounded text-xs font-medium transition-colors">
        <MessageSquare className="w-3 h-3" />
        Ask AI
      </button>
      <button
        onClick={handleAllowSession}
        className="flex items-center gap-1 bg-gray-700 hover:bg-gray-600 text-white px-2.5 py-1.5 rounded text-xs font-medium transition-colors"
      >
        <Shield className="w-3 h-3" />
        Allow Session
      </button>
    </div>
  )
}
