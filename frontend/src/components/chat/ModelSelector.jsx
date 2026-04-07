import { useEffect, useState } from 'react'
import { agents } from '../../lib/api'
import { ChevronDown } from 'lucide-react'

export function ModelSelector({ agentName, value, onChange }) {
  const [models, setModels] = useState([])
  const [currentModel, setCurrentModel] = useState(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (agentName) {
      agents.acpConfigOptions(agentName).then(({ data }) => {
        const option = (data.configOptions || []).find((o) => o.category === 'model')
        const list = (option?.options || []).map((o) => o.value).filter(Boolean)
        setModels(list)
        setCurrentModel(option?.currentValue || null)
      }).catch(async () => {
        try {
          const { data } = await agents.models(agentName)
          setModels(data.models || [])
          setCurrentModel(data.current_model || null)
        } catch {
          setModels([])
          setCurrentModel(null)
        }
      })
    }
  }, [agentName])

  useEffect(() => {
    if ((!value || value === 'claude-sonnet-4-20250514') && currentModel) {
      onChange(currentModel)
    }
  }, [currentModel, onChange, value])

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 bg-[#1a1d27] border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 hover:border-gray-600"
      >
        {value || currentModel || 'Select model'}
        <ChevronDown className="w-3 h-3" />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 bg-[#1a1d27] border border-gray-700 rounded-lg shadow-xl z-10 min-w-[200px]">
          {currentModel && !models.includes(currentModel) && (
            <button
              onClick={() => { onChange(currentModel); setOpen(false) }}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-700 ${
                currentModel === value ? 'text-blue-400' : 'text-gray-300'
              }`}
            >
              {currentModel} (current)
            </button>
          )}
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
