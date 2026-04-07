import { ChevronRight, Home, Settings as SettingsIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

export function AppHeader({ breadcrumbs = [] }) {
  return (
    <header className="border-b border-gray-800 px-6 py-4 bg-[#0f1117]">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <nav className="flex items-center gap-1 text-sm">
          <Link to="/" className="text-gray-400 hover:text-white flex items-center gap-1">
            <Home className="w-3.5 h-3.5" />
            Home
          </Link>
          {breadcrumbs.map((item, index) => (
            <span key={`${item.label}-${index}`} className="flex items-center gap-1">
              <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
              {item.to ? (
                <Link to={item.to} className="text-gray-400 hover:text-white">
                  {item.label}
                </Link>
              ) : (
                <span className="text-white font-medium">{item.label}</span>
              )}
            </span>
          ))}
        </nav>
        <Link to="/settings" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white">
          <SettingsIcon className="w-4 h-4" />
          Settings
        </Link>
      </div>
    </header>
  )
}
