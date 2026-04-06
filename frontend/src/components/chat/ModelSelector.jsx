import { useEffect, useState } from 'react'
import { agents } from '../../lib/api'
import { ChevronDown } from 'lucide-react'

export function ModelSelector({ agentName, value, onChange }) {
  const [models, setModels] = useState([])
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (agentName) {
      agents.models(agentName).then(({ data }) => setModels(data.models || [])).catch(() => setModels([]))
    }
  }, [agentName])

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 bg-[#1a1d27] border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 hover:border-gray-600"
      >
        {value}
        <ChevronDown className="w-3 h-3" />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 bg-[#1a1d27] border border-gray-700 rounded-lg shadow-xl z-10 min-w-[200px]">
          {models.map((m) => (
            <button
              key={m}
              onClick={() => { onChange(m); setOpen(false) }}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-700 ${
                m === value ? 'text-blue-400' : 'text-gray-300'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
