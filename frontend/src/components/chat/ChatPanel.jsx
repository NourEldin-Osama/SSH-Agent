import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, Play } from 'lucide-react'
import { Link } from 'react-router-dom'

import { AgentSelector } from './AgentSelector'
import { ChatInput } from './ChatInput'
import { ChatMessage } from './ChatMessage'
import { ModelSelector } from './ModelSelector'

export function ChatPanel({
  session,
  onStartSession,
  onSend,
  onEndSession,
  messages,
  readOnly,
  noAgentConfigured,
  onSendFailureToAI,
}) {
  const [selectedAgent, setSelectedAgent] = useState('claude-code')
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-20250514')
  const [failedCommandPrompt, setFailedCommandPrompt] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    const handler = () => setFailedCommandPrompt(true)
    window.addEventListener('command-failed-prompt', handler)
    return () => window.removeEventListener('command-failed-prompt', handler)
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!session) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500 p-8">
        <p className="text-lg mb-2">No active session</p>
        <p className="text-sm mb-4">Start a new session to begin chatting with the AI agent</p>
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

  return (
    <div className="h-full flex flex-col bg-[#0f1117]">
      <div className="border-b border-gray-800 p-3 space-y-2">
        <div className="flex gap-2">
          <AgentSelector value={selectedAgent} onChange={setSelectedAgent} />
          <ModelSelector agentName={selectedAgent} value={selectedModel} onChange={setSelectedModel} />
        </div>
        <div className="flex items-center justify-end">
          <button
            onClick={onEndSession}
            disabled={readOnly}
            className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-3 py-1.5 rounded disabled:opacity-50"
          >
            End Session
          </button>
        </div>
        {noAgentConfigured && (
          <div className="text-xs text-amber-300 bg-amber-900/20 border border-amber-800 rounded p-2">
            No agent configured - go to <Link className="underline" to="/settings">Settings</Link> to add one.
          </div>
        )}
        {readOnly && (
          <div className="text-xs text-amber-400">Read-only mode: historical session</div>
        )}
      </div>

      {failedCommandPrompt && (
        <div className="px-4 py-2 bg-amber-900/20 border-b border-amber-800 text-sm text-amber-300 flex items-center justify-between">
          <span className="flex items-center gap-2"><AlertTriangle className="w-4 h-4" />Command failed - send error to AI for suggestions?</span>
          <div className="flex gap-2">
            <button className="px-2 py-1 bg-blue-600 rounded" onClick={() => { onSendFailureToAI?.(); setFailedCommandPrompt(false) }}>Yes</button>
            <button className="px-2 py-1 bg-gray-700 rounded" onClick={() => setFailedCommandPrompt(false)}>No</button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <ChatMessage key={msg.id || `${msg.role}-${msg.created_at}`} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={onSend} disabled={!session || readOnly || noAgentConfigured} />
    </div>
  )
}
