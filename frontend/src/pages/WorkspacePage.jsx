import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { acp, memories, settings, chat as chatApi } from '../lib/api'
import { wsManager } from '../lib/websocket'
import { ChatPanel } from '../components/chat/ChatPanel'
import { CommandGraph } from '../components/commands/CommandGraph'
import { Navbar } from '../components/layout/Navbar'
import { PanelLayout } from '../components/layout/PanelLayout'
import { Sidebar } from '../components/layout/Sidebar'
import { MemoryApprovalPrompt } from '../components/memories/MemoryApprovalPrompt'
import { useChatStore } from '../store/useChatStore'
import { useCommandStore } from '../store/useCommandStore'
import { useServerStore } from '../store/useServerStore'
import { useSessionStore } from '../store/useSessionStore'

function notifyBrowser(title, body) {
  if (!('Notification' in window)) return
  if (Notification.permission === 'granted') {
    new Notification(title, { body })
  } else if (Notification.permission === 'default') {
    Notification.requestPermission()
  }
}

export function Workspace() {
  const { serverId } = useParams()
  const location = useLocation()
  const numericServerId = Number(serverId)

  const { servers, fetchServers } = useServerStore()
  const {
    sessions: sessionList,
    activeSession,
    readOnly,
    fetchSessions,
    createSession,
    setActiveSession,
    updateSessionTitle,
    deleteSession,
    endSession,
  } = useSessionStore()
  const { commands, fetchCommands, addCommand, updateCommand } = useCommandStore()
  const { messages, fetchMessages, appendMessage } = useChatStore()

  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [dangerMode, setDangerMode] = useState(false)
  const [memoryPrompt, setMemoryPrompt] = useState(null)
  const [acpStatus, setAcpStatus] = useState(null)
  const [failedCommandError, setFailedCommandError] = useState('')
  const [noAgentConfigured, setNoAgentConfigured] = useState(false)
  const [debugMode, setDebugMode] = useState(false)

  const server = useMemo(() => servers.find((s) => s.id === numericServerId), [servers, numericServerId])

  const refreshDanger = useCallback(async (sessionId) => {
    if (!sessionId) {
      setDangerMode(false)
      return
    }
    try {
      const { data } = await settings.getDangerMode(sessionId)
      setDangerMode(Boolean(data.enabled))
    } catch {
      setDangerMode(false)
    }
  }, [])

  const loadSession = useCallback(async (session) => {
    setActiveSession(session)
    await Promise.all([fetchCommands(session.id), fetchMessages(session.id)])
    wsManager.connect(String(session.id), handleWSMessage)
    await refreshDanger(session.id)
  }, [fetchCommands, fetchMessages, setActiveSession, refreshDanger])

  const startNewSession = useCallback(async () => {
    const created = await createSession(numericServerId, null)
    await fetchSessions(numericServerId)
    await loadSession(created)
    toast.success('Session started')
  }, [createSession, fetchSessions, loadSession, numericServerId])

  const handleWSMessage = useCallback((data) => {
    switch (data.event) {
      case 'command_created':
        addCommand(data.data)
        notifyBrowser('Command Created', data.data?.title || 'New command created')
        break
      case 'command_status_updated':
        updateCommand(data.data.id, { status: data.data.status })
        break
      case 'command_output_updated':
        updateCommand(data.data.id, { actual_output: data.data.actual_output })
        break
      case 'agent_message':
        appendMessage(data.data)
        break
      case 'agent_progress': {
        if (!debugMode) break
        const stage = data.data?.stage || 'thinking'
        const details = data.data?.details || {}
        const content = stage === 'tool_call'
          ? `Tool: ${details.tool}\n${JSON.stringify(details.result ?? {}, null, 2)}`
          : stage === 'debug'
          ? `Debug\n${JSON.stringify(details, null, 2)}`
          : stage === 'error'
          ? `Provider error\n${JSON.stringify(details, null, 2)}`
          : details.message || stage
        appendMessage({
          id: `progress-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          role: 'progress',
          content,
          created_at: new Date().toISOString(),
        })
        break
      }
      case 'memory_approval_required':
        setMemoryPrompt(data.data)
        notifyBrowser('Memory Approval Required', 'AI generated memory candidates')
        break
      case 'command_failed_ask_user':
        window.dispatchEvent(new CustomEvent('command-failed-prompt'))
        setFailedCommandError(data.data?.error || 'Unknown error')
        appendMessage({
          id: `failed-${Date.now()}`,
          role: 'system',
          content: `Command failed - send error to AI for suggestions?\nError: ${data.data?.error || 'Unknown error'}`,
          created_at: new Date().toISOString(),
        })
        toast.error('Command failed')
        notifyBrowser('Command Failed', 'A command failed and needs attention')
        break
      case 'acp_status':
        setAcpStatus(data.data)
        break
      case 'session_title_generated':
        if (activeSession?.id === data.data?.session_id) {
          updateSessionTitle(activeSession.id, data.data.title)
        }
        break
      default:
        break
    }
  }, [activeSession?.id, addCommand, appendMessage, updateCommand, updateSessionTitle])

  useEffect(() => {
    fetchServers()
    fetchSessions(numericServerId)
    fetch('/api/agents/').then((res) => res.json()).then((agents) => setNoAgentConfigured(!agents.length)).catch(() => setNoAgentConfigured(true))
    settings.getDebugMode().then(({ data }) => setDebugMode(Boolean(data.enabled))).catch(() => setDebugMode(false))
    acp.status().then(({ data }) => {
      setAcpStatus(data)
      if (data.failed) {
        toast.error('Agent server failed to start - check logs')
      }
    }).catch(() => {
      setAcpStatus({ running: false, failed: true, failure_reason: 'Unable to fetch ACP status' })
    })
  }, [fetchServers, fetchSessions, numericServerId])

  useEffect(() => {
    if (sessionList.length > 0 && !activeSession) {
      const requested = Number(new URLSearchParams(location.search).get('session_id'))
      const target = Number.isFinite(requested)
        ? sessionList.find((s) => s.id === requested) || sessionList[0]
        : sessionList[0]
      loadSession(target)
    }
  }, [sessionList, activeSession, loadSession, location.search])

  useEffect(() => {
    const handler = (event) => {
      if (!activeSession?.id || readOnly) return
      const cmd = event.detail
      appendMessage({
        id: `edit-${Date.now()}`,
        role: 'user',
        content: `I edited command '${cmd?.title || 'unknown'}'. Please adjust future steps accordingly.`,
        created_at: new Date().toISOString(),
      })
    }
    window.addEventListener('notify-ai-edit', handler)
    return () => window.removeEventListener('notify-ai-edit', handler)
  }, [activeSession?.id, appendMessage, readOnly])

  useEffect(() => {
    return () => wsManager.disconnect()
  }, [])

  const handleDangerToggle = useCallback(async () => {
    if (!activeSession?.id || readOnly) {
      toast.error('Danger mode can only be changed in an active session')
      return
    }
    const next = !dangerMode
    await settings.setDangerMode(next, activeSession.id)
    setDangerMode(next)
    toast.success(next ? 'Danger mode enabled' : 'Danger mode disabled')
  }, [activeSession?.id, dangerMode, readOnly])

  const handleSendFailureToAI = useCallback(async () => {
    if (!activeSession?.id || !failedCommandError) return
    await chatApi.sendMessage(activeSession.id, {
      role: 'user',
      content: `Command failed. Please suggest fix. Error: ${failedCommandError}`,
    })
    await fetchMessages(activeSession.id)
    toast.success('Sent failure details to AI')
  }, [activeSession?.id, failedCommandError, fetchMessages])

  const handleEndSession = useCallback(async () => {
    if (!activeSession?.id) return
    await endSession(activeSession.id)
    await fetchSessions(numericServerId)
    toast.success('Session ended')
  }, [activeSession?.id, endSession, fetchSessions, numericServerId])

  const handleApproveAllMemories = useCallback(async () => {
    const ids = (memoryPrompt?.memories || []).map((m) => m.id)
    if (ids.length) {
      await memories.batchApprove(ids)
      toast.success('Memories approved')
    }
    setMemoryPrompt(null)
  }, [memoryPrompt])

  const handleReviewMemories = useCallback(async (memory, approve) => {
    if (!memory?.id) return
    try {
      if (approve) {
        await memories.approve(memory.id)
      } else {
        await memories.reject(memory.id)
      }
      setMemoryPrompt((prev) => {
        const next = (prev?.memories || []).filter((m) => m.id !== memory.id)
        if (next.length === 0) return null
        return { ...prev, memories: next }
      })
    } catch {
      toast.error('Failed to update memory item')
    }
  }, [])

  const handleSendUserMessage = useCallback(async (content) => {
    if (!activeSession?.id) return
    const optimisticId = `optimistic-${Date.now()}`
    appendMessage({
      id: optimisticId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    })
    await chatApi.sendMessage(activeSession.id, { role: 'user', content })
    await fetchMessages(activeSession.id)
  }, [activeSession?.id, appendMessage, fetchMessages])

  if (!server) {
    return <div className="min-h-screen bg-[#0f1117] flex items-center justify-center text-gray-400">Loading...</div>
  }

  return (
    <div className="h-screen flex flex-col bg-[#0f1117]">
      <Navbar
        server={server}
        dangerMode={dangerMode}
        debugMode={debugMode}
        onDangerModeToggle={handleDangerToggle}
        onDebugModeChange={setDebugMode}
      />

      {acpStatus?.failed && (
        <div className="bg-red-900/40 border-b border-red-700 text-red-200 text-sm px-4 py-2">
          Agent server failed to start - check logs
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        <PanelLayout
          left={
            <ChatPanel
              server={server}
              session={activeSession}
              readOnly={readOnly}
              onStartSession={startNewSession}
              onSend={handleSendUserMessage}
              onEndSession={handleEndSession}
              messages={messages}
              noAgentConfigured={noAgentConfigured}
              onSendFailureToAI={handleSendFailureToAI}
            />
          }
          right={
            <CommandGraph
              commands={commands}
              session={activeSession}
              readOnly={readOnly}
              onStartSession={startNewSession}
            />
          }
        />
        <Sidebar
          sessions={sessionList.filter((s) => s.server_id === numericServerId)}
          activeSession={activeSession}
          onSelectSession={loadSession}
          onRenameSession={updateSessionTitle}
          onCreateSession={startNewSession}
          onDeleteSession={deleteSession}
          open={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />
      </div>

      {memoryPrompt && (
        <MemoryApprovalPrompt
          memories={memoryPrompt.memories || []}
          onApproveAll={handleApproveAllMemories}
          onReview={handleReviewMemories}
          onClose={() => setMemoryPrompt(null)}
        />
      )}
    </div>
  )
}
