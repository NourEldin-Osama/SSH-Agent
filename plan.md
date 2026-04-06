---

# 🧠 SSH Agent Commander

---

## 📋 Project Overview

Build a **local web application** called **"SSH Agent Commander"** that allows a user to:
- Manage SSH servers
- Chat with AI agents (via ACP protocol)
- Let the AI execute commands on SSH servers via MCP tools
- Visually see commands as interactive node cards in a graph
- Approve/deny commands before execution (human-in-the-loop)
- Manage whitelists/blacklists, memories per server, and session history

The app runs **fully locally** on the user's machine and is accessed via browser.

---

## 🗂️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| SSH Execution | Paramiko |
| Encryption | Python `cryptography` library (Fernet) |
| Database | SQLite via SQLAlchemy ORM |
| ACP Server | Spun up by the app itself on startup |
| MCP Tools | Exposed by FastAPI to the ACP agent |
| WebSockets | FastAPI WebSockets (for real-time command status updates) |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React (Vite) |
| UI Components | ShadCN UI |
| Styling | TailwindCSS |
| Graph/Nodes | React Flow |
| HTTP Client | Axios |
| State Management | Zustand |
| Notifications | Sonner (toast) + Browser Notification API |

---

## 📁 Folder Structure

```
ssh-agent-commander/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── acp_server.py            # ACP server setup and lifecycle
│   ├── mcp_tools.py             # MCP tool definitions
│   ├── ssh_executor.py          # SSH command execution via Paramiko
│   ├── encryption.py            # Fernet encryption/decryption helpers
│   ├── database.py              # SQLAlchemy setup and session
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic schemas
│   ├── routers/
│   │   ├── servers.py           # Server CRUD endpoints
│   │   ├── sessions.py          # Session management endpoints
│   │   ├── commands.py          # Command endpoints
│   │   ├── agents.py            # Agent configuration endpoints
│   │   ├── memories.py          # Server memories endpoints
│   │   ├── permissions.py       # Whitelist/blacklist endpoints
│   │   └── chat.py              # Chat history endpoints
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── store/
│   │   │   ├── useServerStore.js
│   │   │   ├── useSessionStore.js
│   │   │   ├── useCommandStore.js
│   │   │   ├── useChatStore.js
│   │   │   └── usePermissionStore.js
│   │   ├── pages/
│   │   │   ├── Home.jsx              # Server list + management
│   │   │   ├── WorkspacePage.jsx     # Main 2-panel workspace
│   │   │   ├── SessionsPage.jsx      # Old sessions browser
│   │   │   └── SettingsPage.jsx      # Settings
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.jsx
│   │   │   │   ├── Sidebar.jsx            # Collapsible sessions sidebar
│   │   │   │   └── PanelLayout.jsx        # 2-panel split layout
│   │   │   ├── servers/
│   │   │   │   ├── ServerCard.jsx
│   │   │   │   ├── ServerForm.jsx
│   │   │   │   └── ServerList.jsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatPanel.jsx          # Left panel
│   │   │   │   ├── ChatMessage.jsx
│   │   │   │   ├── ChatInput.jsx
│   │   │   │   ├── AgentSelector.jsx
│   │   │   │   ├── ModelSelector.jsx
│   │   │   │   └── DangerModeToggle.jsx
│   │   │   ├── commands/
│   │   │   │   ├── CommandGraph.jsx       # React Flow graph
│   │   │   │   ├── CommandCard.jsx        # Individual command node
│   │   │   │   ├── CommandGroup.jsx       # Grouped commands node
│   │   │   │   └── CommandCardFooter.jsx  # Approve/Deny buttons
│   │   │   ├── memories/
│   │   │   │   ├── MemoriesTab.jsx
│   │   │   │   ├── MemoryItem.jsx
│   │   │   │   └── MemoryApprovalPrompt.jsx
│   │   │   └── permissions/
│   │   │       ├── WhitelistBlacklistManager.jsx
│   │   │       └── PermissionRuleForm.jsx
│   │   └── lib/
│   │       ├── api.js                # Axios API calls
│   │       ├── websocket.js          # WebSocket connection manager
│   │       └── utils.js
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
```

---

## 🗄️ Database Schema

### Table: `servers`
```sql
id                  INTEGER PRIMARY KEY
label               TEXT NOT NULL
hostname            TEXT NOT NULL
port                INTEGER DEFAULT 22
username            TEXT NOT NULL
auth_method         TEXT NOT NULL  -- "password" | "ssh_key" | "ssh_key_passphrase"
encrypted_password  TEXT           -- nullable
encrypted_ssh_key   TEXT           -- nullable
encrypted_passphrase TEXT          -- nullable
tags                TEXT           -- JSON array string ["prod", "db"]
created_at          DATETIME
updated_at          DATETIME
```

### Table: `sessions`
```sql
id                  INTEGER PRIMARY KEY
server_id           INTEGER REFERENCES servers(id)
title               TEXT           -- auto-generated by AI, editable
created_at          DATETIME
ended_at            DATETIME       -- nullable, set when session ends
```

### Table: `chat_messages`
```sql
id                  INTEGER PRIMARY KEY
session_id          INTEGER REFERENCES sessions(id)
role                TEXT NOT NULL  -- "user" | "agent" | "system"
content             TEXT NOT NULL
created_at          DATETIME
```

### Table: `commands`
```sql
id                  INTEGER PRIMARY KEY
session_id          INTEGER REFERENCES sessions(id)
server_id           INTEGER REFERENCES servers(id)
parent_id           INTEGER REFERENCES commands(id)  -- for tree structure
group_id            TEXT           -- nullable, UUID to group parallel commands
position_in_group   INTEGER        -- nullable, order within group
title               TEXT NOT NULL
description         TEXT NOT NULL
command             TEXT NOT NULL
expected_output     TEXT           -- nullable
rollback_steps      TEXT           -- nullable
status              TEXT NOT NULL  -- "pending"|"approved"|"executing"|"success"|"failed"|"denied"|"blocked"
actual_output       TEXT           -- nullable, filled after execution
is_risky            BOOLEAN DEFAULT FALSE
edited_by_user      BOOLEAN DEFAULT FALSE
original_command    TEXT           -- nullable, stores original if edited
node_position_x     REAL           -- React Flow node x position
node_position_y     REAL           -- React Flow node y position
created_at          DATETIME
executed_at         DATETIME       -- nullable
```

### Table: `server_memories`
```sql
id                  INTEGER PRIMARY KEY
server_id           INTEGER REFERENCES servers(id)
content             TEXT NOT NULL
source              TEXT NOT NULL  -- "ai" | "manual"
approved            BOOLEAN DEFAULT FALSE  -- for AI memories pending approval
created_at          DATETIME
updated_at          DATETIME
```

### Table: `permission_rules`
```sql
id                  INTEGER PRIMARY KEY
rule_type           TEXT NOT NULL  -- "whitelist" | "blacklist"
match_type          TEXT NOT NULL  -- "exact" | "pattern"
command_value       TEXT NOT NULL  -- the command string or pattern
scope               TEXT NOT NULL  -- "global" | "server"
server_id           INTEGER REFERENCES servers(id)  -- nullable if global
created_at          DATETIME
```

### Table: `agent_configs`
```sql
id                  INTEGER PRIMARY KEY
agent_name          TEXT NOT NULL  -- "claude-code" | "opencode" | "codex"
encrypted_api_key   TEXT NOT NULL
base_url            TEXT           -- nullable for local agents
is_active           BOOLEAN DEFAULT TRUE
created_at          DATETIME
```

---

## 🔌 API Endpoints

### Servers
```
GET    /api/servers                    # list all servers
POST   /api/servers                    # create server
GET    /api/servers/{id}               # get single server
PUT    /api/servers/{id}               # update server
DELETE /api/servers/{id}               # delete server
GET    /api/servers/{id}/status        # ping server (reachable check)
```

### Sessions
```
GET    /api/servers/{server_id}/sessions          # list sessions for server
POST   /api/servers/{server_id}/sessions          # create new session
GET    /api/sessions/{id}                         # get session details
PUT    /api/sessions/{id}                         # update session (edit title)
DELETE /api/sessions/{id}                         # delete session
POST   /api/sessions/{id}/end                     # end session (trigger AI memory write)
```

### Chat
```
GET    /api/sessions/{session_id}/messages        # get chat history
POST   /api/sessions/{session_id}/messages        # send message to agent
```

### Commands
```
GET    /api/sessions/{session_id}/commands        # get all commands for session (with tree structure)
POST   /api/commands/{id}/approve                 # approve command
POST   /api/commands/{id}/deny                    # deny command
POST   /api/commands/{id}/edit                    # edit command + optionally notify AI
POST   /api/commands/{id}/reexecute               # re-execute a command
POST   /api/commands/{id}/allow-session           # allow this command for rest of session
```

### Memories
```
GET    /api/servers/{server_id}/memories          # get all memories for server
POST   /api/servers/{server_id}/memories          # create manual memory
PUT    /api/memories/{id}                         # edit memory
DELETE /api/memories/{id}                         # delete memory
POST   /api/memories/{id}/approve                 # approve AI-suggested memory
POST   /api/memories/batch-approve                # approve multiple AI memories
```

### Permissions
```
GET    /api/permissions                            # get all rules
POST   /api/permissions                            # create rule
PUT    /api/permissions/{id}                       # update rule
DELETE /api/permissions/{id}                       # delete rule
GET    /api/permissions/check                      # check if command matches any rule
```

### Agents
```
GET    /api/agents                                 # list configured agents
POST   /api/agents                                 # add agent config
PUT    /api/agents/{id}                            # update agent config
DELETE /api/agents/{id}                            # delete agent config
GET    /api/agents/{name}/models                   # get available models for agent
```

### WebSocket
```
WS     /ws/session/{session_id}                   # real-time updates for command status
```

---

## 🛠️ MCP Tools Definition

The app exposes the following MCP tools to the AI agent:

### Tool 1: `execute_command`
```json
{
  "name": "execute_command",
  "description": "Execute a shell command on the currently selected SSH server. Always provide meaningful title, description, expected output. Mark as risky and provide rollback steps if the command modifies the system.",
  "parameters": {
    "title": "string — short human-readable title for the command",
    "description": "string — explain what this command does and why",
    "command": "string — the exact shell command to execute",
    "expected_output": "string — what output is expected if successful",
    "rollback_steps": "string | null — steps to undo if something goes wrong (required if risky)",
    "is_risky": "boolean — true if command modifies files, services, or system state",
    "group_id": "string | null — if this command is part of a parallel group, provide shared UUID",
    "position_in_group": "integer | null — order within the group",
    "parent_command_id": "integer | null — ID of the parent command in the tree"
  }
}
```

### Tool 2: `read_server_memory`
```json
{
  "name": "read_server_memory",
  "description": "Read all stored memories and notes for the current server. Call this at the start of every session to get context about the server.",
  "parameters": {}
}
```

### Tool 3: `write_server_memory`
```json
{
  "name": "write_server_memory",
  "description": "Write a memory or finding about the current server to be remembered in future sessions. Use this to store important discoveries, configurations, or warnings.",
  "parameters": {
    "content": "string — the memory content to store",
    "source": "ai"
  }
}
```

### Tool 4: `get_current_server_info`
```json
{
  "name": "get_current_server_info",
  "description": "Get information about the currently selected server (label, hostname, port, tags). Does not return credentials.",
  "parameters": {}
}
```

---

## 🖥️ UI Pages & Behavior

### Page 1: Home (`/`)
- Shows list of all servers as cards
- Each server card shows: Label, Hostname, Port, Tags, Status indicator (reachable/unreachable)
- Button to **Add Server** (opens form modal)
- Each card has **Edit** and **Delete** buttons
- Each card has a **"Open Workspace"** button → navigates to `/workspace/{server_id}`
- Server form fields: Label, Hostname, Port, Username, Auth Method (dropdown), Password / SSH Key / Passphrase (conditional on auth method), Tags (multi-input)
- On page load: ping all servers and show reachability status
- If server is unreachable show warning badge: *"Server unreachable — check your connection"*

### Page 2: Workspace (`/workspace/{server_id}`)

#### Top Bar
- Shows selected server name + status badge
- **Danger Mode toggle** (red toggle, requires confirmation dialog to activate)
- Notification bell icon

#### Left Panel — Chat Interface
- **Agent selector** dropdown (list from configured agents)
- **Model selector** dropdown (fetched from `/api/agents/{name}/models`)
- Chat message history (user messages + agent responses)
- When a command fails and AI should be notified: show **inline message in chat**:
  *"Command failed — send error to AI for suggestions?"* with **[Yes]** and **[No]** buttons
- Chat input box with send button
- On session start: auto-call `read_server_memory` tool to inject context
- Session ends when user navigates away or clicks "End Session"
- On session end: trigger AI memory writing flow

#### Right Panel — Command Graph
- React Flow canvas
- Each command = one **CommandCard node**
- Cards connected by edges showing execution order/hierarchy
- Graph clears on new session start
- Supports pan and zoom

#### CommandCard Node
- **Header**: Status colored badge (Pending/Approved/Executing/Success/Failed/Denied/Blocked)
- **Body** (collapsible — collapsed shows only Title + Command):
  - Title
  - Description
  - Command (monospace, copyable)
  - Expected Output
  - Rollback Steps (only shown if `is_risky = true`)
  - Actual Output (shown after execution, collapsible)
- **Colored border**: Yellow=Pending, Blue=Approved, Orange=Executing, Green=Success, Red=Failed, Gray=Denied, Dark=Blocked
- **Footer** (only shown when status = Pending):
  - [Approve] [Deny] buttons
  - [Edit Command] button → opens inline edit input
    - After editing: shows *"Notify AI of changes?"* [Yes] [No] inline
  - [Ask AI] button → pre-fills chat input with *"Tell me more about: {command title}"*
  - [Allow for Session] button → approves this command pattern for the whole session

#### Grouped Commands
- Rendered as a **group node** containing multiple CommandCards side by side
- Connected with arrows between cards in the group
- Group node has a label/border to visually wrap them

#### Right Sidebar — Sessions List (Collapsible)
- Toggle button to collapse/expand
- Shows sessions for the **currently selected server** only
- Each session item shows:
  - Auto-generated title (editable inline on click)
  - Date + time
  - Number of commands executed
- Clicking a session: **replaces** current graph and chat with that session's data
- Current active session highlighted

### Page 3: Settings (`/settings`)
- **Agent Configurations** section:
  - List of configured agents
  - Add/Edit/Delete agent (name, API key, base URL)
- **Whitelist / Blacklist Rules** section:
  - List of all rules (grouped by global / per-server)
  - Add rule form: Rule Type (whitelist/blacklist), Match Type (exact/pattern), Command Value, Scope (global/server), Server (if server scope)
  - Edit / Delete rules

#### Per-Server Memories Tab
- Accessible from the workspace or server card
- Shows all memories for the server (AI-generated + manual)
- AI memories pending approval shown with [Approve] [Reject] buttons
- Manual memories: text input to add new, edit/delete existing
- Memory items show: content, source badge (AI/Manual), date

---

## ⚙️ Permission System Logic (Backend)

On every `execute_command` tool call, before creating the command card:

```
1. Check blacklist rules (global first, then server-specific)
   → If matched: set status = "blocked", notify agent via tool response
   
2. Check whitelist rules (global first, then server-specific)
   → If matched: set status = "approved", auto-execute, skip human approval

3. Check session-allowed commands
   → If matched: set status = "approved", auto-execute

4. Check danger mode
   → If ON: set status = "approved", auto-execute

5. Default: set status = "pending"
   → Send card to frontend via WebSocket
   → Wait for user to approve or deny
```

---

## 🔐 Encryption Strategy

- On first app start: generate a **Fernet encryption key** and store it in a local `.key` file (outside the DB)
- All sensitive fields encrypted before storing in SQLite:
  - Server passwords
  - SSH keys
  - Passphrases
  - Agent API keys
- Encryption/decryption happens only in the backend, never exposed to frontend
- The `.key` file location is configurable via environment variable `ENCRYPTION_KEY_PATH`

---

## 🤖 ACP Server Setup

- On FastAPI startup: **spawn the ACP server** as a subprocess or async task
- ACP server runs on a configurable port (default: `8001`)
- ACP server is registered with the MCP tools listed above
- The AI agent connects to the ACP server to access tools
- The ACP server communicates with FastAPI backend to:
  - Create command entries in DB
  - Send WebSocket updates to frontend
  - Execute SSH commands via Paramiko
  - Read/write server memories

---

## 🔄 WebSocket Events

All real-time events sent to frontend via WebSocket `/ws/session/{session_id}`:

```json
{ "event": "command_created", "data": { ...command object... } }
{ "event": "command_status_updated", "data": { "id": 1, "status": "executing" } }
{ "event": "command_output_updated", "data": { "id": 1, "actual_output": "..." } }
{ "event": "memory_approval_required", "data": { "memories": [...] } }
{ "event": "session_title_generated", "data": { "title": "..." } }
{ "event": "agent_message", "data": { "role": "agent", "content": "..." } }
{ "event": "command_failed_ask_user", "data": { "command_id": 1, "error": "..." } }
```

---

## 🧠 AI Memory Flow (End of Session)

```
1. User ends session (navigates away or clicks End Session)
2. Backend sends all session commands + chat summary to AI
3. AI calls write_server_memory tool for each finding
4. Backend saves memories with approved = false
5. WebSocket sends "memory_approval_required" event to frontend
6. Frontend shows: "Session ended — AI found X things to remember"
   with list of memories and [Approve All] [Review Each] buttons
7. User approves/rejects each memory
8. Approved memories saved with approved = true
```

---

## 🚨 Edge Cases & Error Handling

| Scenario | Behavior |
|---|---|
| Server unreachable | Show warning badge on server card. Show error in command card actual output |
| Command times out | After 30 seconds, mark as failed, show timeout message in actual output |
| Agent sends blacklisted command | Card appears with "Blocked" status, AI notified via tool response |
| Command fails | Inline chat message: "Command failed — send error to AI?" [Yes] [No] |
| User edits command | Store original command in `original_command` field, set `edited_by_user = true` |
| Dangerous mode activated | Confirmation dialog: "You are enabling Dangerous Mode. All commands will execute without approval. Are you sure?" |
| Multiple commands in group | Render as group node, execute sequentially in position order after all approved |
| Session replaced by old session | Current graph and chat replaced, read-only mode for old sessions |
| ACP server fails to start | Show error banner in UI: "Agent server failed to start — check logs" |
| No agent configured | Show prompt on workspace: "No agent configured — go to Settings to add one" |

---

## 📦 Dependencies

### Backend use `uv add`
```
fastapi
uvicorn
sqlalchemy
paramiko
cryptography
websockets
pydantic
python-dotenv
acp-sdk
httpx
```

### Frontend (`package.json` dependencies)
```
react
react-dom
react-router-dom
reactflow
zustand
axios
sonner
@shadcn/ui
tailwindcss
vite
lucide-react
```

---

## 🚀 Startup Instructions to Generate

The AI generating this project should also produce:
1. `start.sh` — script that starts both backend and frontend
2. `README.md` — setup instructions, how to add first server, how to configure agents
3. `.env.example` — environment variables template
4. `init_db.py` — script to initialize the SQLite database on first run

---

## 🎯 Implementation Order (Suggested for AI)

```
Phase 1: Foundation
  - Database models + migrations
  - Encryption setup
  - FastAPI app skeleton
  - Server CRUD endpoints

Phase 2: SSH Execution
  - Paramiko integration
  - SSH executor service
  - Server reachability check

Phase 3: Agent Integration
  - ACP server setup
  - MCP tools implementation
  - WebSocket setup

Phase 4: Permission System
  - Whitelist/blacklist logic
  - Session-allow logic
  - Danger mode logic

Phase 5: Frontend Foundation
  - Vite + React + ShadCN + TailwindCSS setup
  - Routing (Home, Workspace, Settings)
  - Zustand stores

Phase 6: Home Page
  - Server list
  - Server form (add/edit)
  - Server status ping

Phase 7: Workspace Page
  - 2-panel layout
  - Chat panel
  - Agent + Model selectors
  - Command Graph with React Flow
  - CommandCard node component
  - Sessions sidebar

Phase 8: Settings Page
  - Agent configurations
  - Whitelist/Blacklist manager

Phase 9: Memories
  - Memories tab per server
  - AI memory approval flow

Phase 10: Polish
  - Notifications (toast + browser)
  - Error handling
  - Edge cases
```

---

This is the complete requirements document. Use this to build the full working application from scratch following the implementation order phase by phase.