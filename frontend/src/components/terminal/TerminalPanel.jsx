import { useState } from 'react'
import { Play, Terminal as TerminalIcon, Trash2 } from 'lucide-react'

export function TerminalPanel({ serverId, sessionId, disabled, onExecute }) {
  const [command, setCommand] = useState('ls -la')
  const [running, setRunning] = useState(false)
  const [history, setHistory] = useState([])

  const runCommand = async (e) => {
    e.preventDefault()
    if (!command.trim() || disabled || running) return
    setRunning(true)
    try {
      const result = await onExecute({
        server_id: serverId,
        session_id: sessionId || null,
        command: command.trim(),
      })
      setHistory((prev) => [
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          command: command.trim(),
          output: result.output || '',
          exit_status: result.exit_status,
          executed_at: result.executed_at,
        },
        ...prev,
      ])
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-[#0b0f1a] border-l border-gray-800">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-cyan-300">
          <TerminalIcon className="w-4 h-4" />
          Manual Terminal
        </div>
        <button
          onClick={() => setHistory([])}
          className="text-xs text-gray-400 hover:text-white flex items-center gap-1"
        >
          <Trash2 className="w-3 h-3" />
          Clear
        </button>
      </div>

      <form onSubmit={runCommand} className="p-3 border-b border-gray-800 flex gap-2">
        <input
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          disabled={disabled || running}
          className="flex-1 bg-[#111827] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 disabled:opacity-50"
          placeholder="Run command directly over SSH (no AI)..."
        />
        <button
          type="submit"
          disabled={disabled || running || !command.trim()}
          className="bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white px-3 py-2 rounded-lg text-sm flex items-center gap-1"
        >
          <Play className="w-4 h-4" />
          Run
        </button>
      </form>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {history.map((item) => (
          <div key={item.id} className="bg-[#111827] border border-gray-800 rounded-lg p-3">
            <div className="text-xs text-cyan-300 font-mono mb-2">$ {item.command}</div>
            <pre className="text-xs text-gray-200 whitespace-pre-wrap break-all bg-[#0b1220] rounded p-2 max-h-56 overflow-auto">
              {item.output || '(no output)'}
            </pre>
            <div className="text-[11px] text-gray-500 mt-2">
              exit={item.exit_status} • {new Date(item.executed_at).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {history.length === 0 && (
          <p className="text-xs text-gray-500">No terminal commands yet. Run one to see output here.</p>
        )}
      </div>
    </div>
  )
}
