export function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const isAgent = message.role === 'agent'
  const isSystem = message.role === 'system'
  const isProgress = message.role === 'progress'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-xl px-4 py-3 text-sm ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : isAgent
            ? 'bg-[#1a1d27] text-gray-200 border border-gray-800 rounded-bl-sm'
            : isProgress
            ? 'bg-indigo-900/20 text-indigo-200 border border-indigo-800/40 rounded-bl-sm'
            : 'bg-amber-900/20 text-amber-300 border border-amber-800/50 rounded-bl-sm'
        }`}
      >
        {isSystem && <div className="text-xs font-medium text-amber-400 mb-1">System</div>}
        {isProgress && <div className="text-xs font-medium text-indigo-300 mb-1">Agent Progress</div>}
        <div className="whitespace-pre-wrap">{message.content}</div>
        <div className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-600'}`}>
          {new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
