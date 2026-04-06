import { useState, useEffect } from 'react'
import { Send } from 'lucide-react'

export function ChatInput({ onSend, disabled }) {
  const [input, setInput] = useState('')

  useEffect(() => {
    const handler = (event) => {
      const cmd = event.detail
      if (cmd?.title) {
        setInput(`Tell me more about: ${cmd.title}`)
      }
    }
    window.addEventListener('ask-ai', handler)
    return () => window.removeEventListener('ask-ai', handler)
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || disabled) return
    onSend(input.trim())
    setInput('')
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-800 p-3">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Send a message..."
          disabled={disabled}
          className="flex-1 bg-[#1a1d27] border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white p-2 rounded-lg transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </form>
  )
}
