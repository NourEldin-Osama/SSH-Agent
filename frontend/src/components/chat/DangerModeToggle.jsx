import { ShieldAlert } from 'lucide-react'

export function DangerModeToggle({ enabled, onChange, disabled = false }) {
  return (
    <button
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      className={`flex items-center gap-2 text-xs px-2.5 py-1 rounded-full transition-colors ${
        enabled
          ? 'bg-red-900/50 text-red-400 border border-red-800'
          : 'bg-gray-800 text-gray-500 border border-gray-700 hover:text-gray-400'
      } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
    >
      <ShieldAlert className="w-3 h-3" />
      {enabled ? 'Danger Mode ON' : 'Danger Mode OFF'}
    </button>
  )
}
