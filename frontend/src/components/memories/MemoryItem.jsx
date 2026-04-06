import { Trash2, Check, X } from 'lucide-react'

export function MemoryItem({ memory, onDelete, onApprove }) {
  return (
    <div className={`bg-[#1a1d27] border rounded-lg px-4 py-3 ${
      memory.approved ? 'border-gray-800' : 'border-amber-800'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              memory.source === 'ai' ? 'bg-purple-900/50 text-purple-400' : 'bg-blue-900/50 text-blue-400'
            }`}>
              {memory.source.toUpperCase()}
            </span>
            {!memory.approved && memory.source === 'ai' && (
              <span className="text-xs bg-amber-900/50 text-amber-400 px-2 py-0.5 rounded-full">Pending Approval</span>
            )}
          </div>
          <p className="text-sm text-gray-300">{memory.content}</p>
          <p className="text-xs text-gray-600 mt-1">{new Date(memory.created_at).toLocaleString()}</p>
        </div>
        <div className="flex gap-1 ml-3">
          {!memory.approved && memory.source === 'ai' && (
            <>
              <button onClick={onApprove} className="p-1.5 text-gray-400 hover:text-green-400 hover:bg-gray-700 rounded">
                <Check className="w-4 h-4" />
              </button>
              <button onClick={onDelete} className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded">
                <X className="w-4 h-4" />
              </button>
            </>
          )}
          {memory.source === 'manual' && (
            <button onClick={onDelete} className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded">
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
