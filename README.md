# SSH Agent Commander

Local-first web app to manage SSH servers, run AI-assisted command sessions, and enforce human-in-the-loop approvals.

## Tech Notes

- ACP implementation uses the Zed Agent Client Protocol standard (`agent-client-protocol` Python package).
- Sensitive fields (server passwords/keys/passphrases and agent API keys) are encrypted via Fernet in backend storage.

## Prerequisites

- Python 3.10+
- Node 18+
- `npm` available in PATH

## Setup

1. Copy env template:

```bash
cp .env.example .env
```

2. Install backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

3. Install frontend dependencies:

```bash
cd frontend && npm install
```

## Run App

From project root:

```bash
./start.sh
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### ACP Runtime Mode

- Default is `ACP_STDIO_ENABLED=false` (`http-bridge` mode): robust local backend tool bridge used by workspace flows.
- Set `ACP_STDIO_ENABLED=true` to enable Zed ACP stdio server runtime path.
- Check mode/status at `GET /api/acp/status`.
- Optional real model response path:
  - `ACP_REAL_MODEL_ENABLED=true`
  - `ACP_MODEL_NAME=<model>`
  - Active agent must have `base_url` configured (OpenAI-compatible chat completions endpoint).

## First Server Setup

1. Open Home page.
2. Click `Add Server`.
3. Fill label/host/port/user/auth method.
4. Provide password or SSH key/passphrase based on auth type.
5. Save and use `Open Workspace`.

## Agent Configuration

1. Open `Settings`.
2. Add an agent configuration (name, API key, optional base URL).
3. Keep at least one active agent for live agent-response mode.
4. If no agent is configured, chat falls back to a clear system response.

## Notes

- ACP runtime status is available at `GET /api/acp/status`.
- Command tool calls can be exercised via `POST /api/acp/tools/{tool_name}`.
