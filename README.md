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

2. Install backend dependencies (uv):

```bash
uv sync --project backend
```

3. Install frontend dependencies:

```bash
cd frontend && pnpm install
```

## Run App

From project root:

```bash
./start.sh
```

Manual backend run with uv:

```bash
uv run --project backend uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend
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

### Debug Mode

- Enable Debug in workspace navbar to stream internal agent progress events.
- Debug events include provider call metadata, MCP tool invocation results, and fallback reasons.

## First Server Setup

1. Open Home page.
2. Click `Add Server`.
3. Fill label/host/port/user/auth method.
4. Provide password or SSH key/passphrase based on auth type.
5. Save and use `Open Workspace`.

## Agent Configuration

1. Open `Settings`.
2. Add an agent configuration (name, local agents do not require API key/base URL).
3. Keep at least one active agent for live agent-response mode.
4. If no agent is configured, chat falls back to a clear system response.

For local CLI agents:

- `claude-code` uses `CLAUDE_CODE_EXECUTABLE` (default: `claude`)
- `opencode` uses `OPENCODE_EXECUTABLE` (default: `opencode`)

If the executable is available in PATH, API key/base URL are not required.

## Notes

- ACP runtime status is available at `GET /api/acp/status`.
- Command tool calls can be exercised via `POST /api/acp/tools/{tool_name}`.

## Logging (Loguru)

- Backend logging uses `loguru`.
- Configure with env vars:
  - `LOG_LEVEL=TRACE|DEBUG|INFO|WARNING|ERROR`
  - `LOG_FILE=/path/to/logfile.log` (optional)
- If `LOG_FILE` is set, logs rotate at 10 MB, retain 7 days, and are compressed.

For full runtime telemetry (agent progress + provider/tool details), use:

```bash
LOG_LEVEL=DEBUG uv run --project backend uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend
```
