import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Home } from './pages/Home'
import { Workspace } from './pages/WorkspacePage'
import { Settings } from './pages/SettingsPage'
import { SessionsPage } from './pages/SessionsPage'
import { Toaster } from 'sonner'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/workspace/:serverId" element={<Workspace />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/sessions/:serverId" element={<SessionsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster position="top-right" theme="dark" />
    </BrowserRouter>
  )
}

export default App
