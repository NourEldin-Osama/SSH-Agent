import { CheckCheck } from 'lucide-react'

export function MemoryApprovalPrompt({ memories, onApproveAll, onReview, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#1a1d27] border border-gray-700 rounded-xl w-full max-w-2xl mx-4 p-6">
        <h3 className="text-lg font-semibold text-white mb-2">Session Ended</h3>
        <p className="text-sm text-gray-400 mb-4">
          AI found {memories.length} thing{memories.length !== 1 ? 's' : ''} to remember
        </p>
        <div className="space-y-2 mb-4 max-h-72 overflow-y-auto">
          {memories.map((m, i) => (
            <div key={m.id || i} className="bg-[#0f1117] rounded-lg px-3 py-2 text-sm text-gray-300 flex items-start justify-between gap-3">
              <div className="flex-1">{m.content}</div>
              <div className="flex gap-2">
                <button onClick={() => onReview?.(m, true)} className="bg-green-700 hover:bg-green-600 text-white text-xs px-2 py-1 rounded">Approve</button>
                <button onClick={() => onReview?.(m, false)} className="bg-red-700 hover:bg-red-600 text-white text-xs px-2 py-1 rounded">Reject</button>
              </div>
            </div>
          ))}
          {memories.length === 0 && <div className="text-sm text-gray-500">No pending memory items.</div>}
        </div>
        <div className="flex gap-3">
          <button
            onClick={onApproveAll}
            className="flex-1 flex items-center justify-center gap-2 bg-green-700 hover:bg-green-600 text-white py-2 rounded-lg text-sm font-medium"
          >
            <CheckCheck className="w-4 h-4" />
            Approve All
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
