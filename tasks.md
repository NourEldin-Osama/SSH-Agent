# SSH Agent Commander - Tasks

## Phase 1: Foundation

- [ ] 1.1 Set up project directory structure (backend/, frontend/)
- [ ] 1.2 Create `requirements.txt` with all backend dependencies
- [ ] 1.3 Create `database.py` — SQLAlchemy setup and session management
- [ ] 1.4 Create `models.py` — All ORM models (servers, sessions, chat_messages, commands, server_memories, permission_rules, agent_configs)
- [ ] 1.5 Create `schemas.py` — All Pydantic schemas for request/response validation
- [ ] 1.6 Create `encryption.py` — Fernet key generation, encryption/decryption helpers
- [ ] 1.7 Create `init_db.py` — Database initialization script
- [ ] 1.8 Create FastAPI app skeleton in `main.py` with basic startup
- [ ] 1.9 Create `routers/servers.py` — Server CRUD endpoints (GET, POST, GET/{id}, PUT/{id}, DELETE/{id}, GET/{id}/status)
- [ ] 1.10 Create `.env.example` with environment variables template

## Phase 2: SSH Execution

- [ ] 2.1 Create `ssh_executor.py` — Paramiko SSH connection management
- [ ] 2.2 Implement SSH command execution with timeout handling (30s default)
- [ ] 2.3 Implement server reachability check (ping/SSH connect test)
- [ ] 2.4 Handle SSH key, password, and passphrase authentication methods
- [ ] 2.5 Add error handling for unreachable servers, timeouts, connection failures

## Phase 3: Agent Integration

- [ ] 3.1 Research and understand ACP (Agent Client Protocol) — see `Docs/` folder
- [ ] 3.2 Create `acp_server.py` — ACP server setup and lifecycle management
- [ ] 3.3 Create `mcp_tools.py` — Implement all 4 MCP tools:
  - [ ] 3.3.1 `execute_command` tool
  - [ ] 3.3.2 `read_server_memory` tool
  - [ ] 3.3.3 `write_server_memory` tool
  - [ ] 3.3.4 `get_current_server_info` tool
- [ ] 3.4 Set up WebSocket manager in `main.py` for real-time updates
- [ ] 3.5 Implement WebSocket endpoint `/ws/session/{session_id}`
- [ ] 3.6 Define and emit all WebSocket events (command_created, command_status_updated, command_output_updated, memory_approval_required, session_title_generated, agent_message, command_failed_ask_user)

## Phase 4: Permission System

- [ ] 4.1 Create `routers/permissions.py` — Permission rule CRUD endpoints
- [ ] 4.2 Implement permission check logic (blacklist → whitelist → session-allow → danger mode → default pending)
- [ ] 4.3 Implement session-allow command tracking
- [ ] 4.4 Implement danger mode toggle logic
- [ ] 4.5 Add permission check integration into `execute_command` MCP tool

## Phase 5: Frontend Foundation

- [ ] 5.1 Initialize Vite + React project in `frontend/`
- [ ] 5.2 Install and configure TailwindCSS
- [ ] 5.3 Set up ShadCN UI components
- [ ] 5.4 Install React Router, React Flow, Zustand, Axios, Sonner, Lucide React
- [ ] 5.5 Create `main.jsx` and `App.jsx` with routing setup
- [ ] 5.6 Create Zustand stores:
  - [ ] 5.6.1 `useServerStore.js`
  - [ ] 5.6.2 `useSessionStore.js`
  - [ ] 5.6.3 `useCommandStore.js`
  - [ ] 5.6.4 `useChatStore.js`
  - [ ] 5.6.5 `usePermissionStore.js`
- [ ] 5.7 Create `lib/api.js` — Axios API helper functions
- [ ] 5.8 Create `lib/websocket.js` — WebSocket connection manager
- [ ] 5.9 Create `lib/utils.js` — Utility functions

## Phase 6: Home Page

- [ ] 6.1 Create `pages/Home.jsx` — Server list page
- [ ] 6.2 Create `components/servers/ServerCard.jsx` — Server card with status indicator
- [ ] 6.3 Create `components/servers/ServerForm.jsx` — Add/Edit server modal form
- [ ] 6.4 Create `components/servers/ServerList.jsx` — Server list container
- [ ] 6.5 Implement server reachability ping on page load
- [ ] 6.6 Add "Open Workspace" button on each server card

## Phase 7: Workspace Page

- [ ] 7.1 Create `pages/WorkspacePage.jsx` — Main 2-panel workspace layout
- [ ] 7.2 Create `components/layout/Navbar.jsx` — Top bar with server name, danger mode toggle, notifications
- [ ] 7.3 Create `components/layout/PanelLayout.jsx` — Resizable 2-panel split layout
- [ ] 7.4 Create `components/layout/Sidebar.jsx` — Collapsible sessions sidebar
- [ ] 7.5 Create `components/chat/ChatPanel.jsx` — Left panel chat container
- [ ] 7.6 Create `components/chat/ChatMessage.jsx` — Individual chat message
- [ ] 7.7 Create `components/chat/ChatInput.jsx` — Chat input with send button
- [ ] 7.8 Create `components/chat/AgentSelector.jsx` — Agent dropdown selector
- [ ] 7.9 Create `components/chat/ModelSelector.jsx` — Model dropdown selector
- [ ] 7.10 Create `components/chat/DangerModeToggle.jsx` — Danger mode toggle with confirmation
- [ ] 7.11 Create `components/commands/CommandGraph.jsx` — React Flow canvas
- [ ] 7.12 Create `components/commands/CommandCard.jsx` — Command node with status, body, footer
- [ ] 7.13 Create `components/commands/CommandGroup.jsx` — Grouped commands node
- [ ] 7.14 Create `components/commands/CommandCardFooter.jsx` — Approve/Deny/Edit/Ask AI/Allow buttons
- [ ] 7.15 Implement WebSocket integration for real-time command updates
- [ ] 7.16 Implement session creation and auto-title generation
- [ ] 7.17 Implement command approve/deny/edit/re-execute flows
- [ ] 7.18 Implement "command failed — send error to AI?" inline prompt
- [ ] 7.19 Create `pages/SessionsPage.jsx` — Old sessions browser

## Phase 8: Settings Page

- [ ] 8.1 Create `pages/SettingsPage.jsx` — Settings page container
- [ ] 8.2 Create `routers/agents.py` — Agent configuration CRUD endpoints
- [ ] 8.3 Implement agent configuration UI (add/edit/delete agents with name, API key, base URL)
- [ ] 8.4 Implement model fetching from `/api/agents/{name}/models`
- [ ] 8.5 Create `components/permissions/WhitelistBlacklistManager.jsx`
- [ ] 8.6 Create `components/permissions/PermissionRuleForm.jsx`
- [ ] 8.7 Implement whitelist/blacklist rule management UI

## Phase 9: Memories

- [ ] 9.1 Create `routers/memories.py` — Memory CRUD endpoints
- [ ] 9.2 Create `components/memories/MemoriesTab.jsx` — Memories tab container
- [ ] 9.3 Create `components/memories/MemoryItem.jsx` — Individual memory display
- [ ] 9.4 Create `components/memories/MemoryApprovalPrompt.jsx` — AI memory approval prompt
- [ ] 9.5 Implement AI memory flow on session end (send commands + chat summary to AI, store memories, prompt for approval)
- [ ] 9.6 Implement batch approve memories functionality
- [ ] 9.7 Implement manual memory creation per server

## Phase 10: Polish

- [ ] 10.1 Implement toast notifications with Sonner
- [ ] 10.2 Implement Browser Notification API integration
- [ ] 10.3 Add comprehensive error handling across all endpoints
- [ ] 10.4 Handle all edge cases from the plan (unreachable server, timeout, blacklisted command, etc.)
- [x] 10.5 Create `start.sh` — Script to start both backend and frontend
- [x] 10.6 Create `README.md` — Setup instructions, first server guide, agent configuration guide
- [ ] 10.7 Test full flow: add server → open workspace → chat with agent → execute commands → end session → review memories

## Pre-Task

- [x] 0.1 Research ACP (Agent Client Protocol) and save findings in `Docs/`
- [x] 0.2 Research MCP (Model Context Protocol) tools implementation in Python

## Completion Update (Current)

- [x] A) ACP/MCP real integration with tool handlers and ACP runtime lifecycle
- [x] B) execute_command decision pipeline order implemented (blacklist -> whitelist -> session allow -> danger -> pending)
- [x] C) Group execution order enforced by `position_in_group` after approvals
- [x] D) Chat route persists user+agent messages and emits `agent_message` websocket updates
- [x] E) Session memory flow wired on start/end with approval event + frontend Approve All/Review Each
- [x] F) Settings permission rules support add/edit/delete, server scope selection, grouped display
- [x] G) Old session list/server scoping/title editing/date+count + read-only loading behavior
- [x] H) Toasts, browser notification hooks, blocked/failed command and ACP failure UI signal handling
- [x] I) Startup/docs/env finalized (`start.sh`, `README.md`, `.env.example`)
- [x] J) Validation run: frontend build, backend smoke, API e2e checklist coverage
- [x] K) ACP model/config options now sourced via ACP session negotiation when enabled, with safe local fallback
