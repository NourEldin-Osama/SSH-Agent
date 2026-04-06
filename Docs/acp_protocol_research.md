# Agent Client Protocol (ACP) - Comprehensive Research Findings

> **IMPORTANT NOTE:** There are **TWO distinct protocols** both abbreviated as "ACP" in the AI agent ecosystem. This document covers both.

---

## Table of Contents

1. [Protocol #1: Agent Client Protocol (Zed Industries)](#protocol-1-agent-client-protocol-zed-industries)
2. [Protocol #2: Agent Communication Protocol (IBM/BeeAI)](#protocol-2-agent-communication-protocol-ibmbeeai)
3. [ACP-MCP Bridge Packages](#acp-mcp-bridge-packages)
4. [Key Differences Between the Two ACPs](#key-differences-between-the-two-acps)
5. [Adoption and Ecosystem](#adoption-and-ecosystem)

---

## Protocol #1: Agent Client Protocol (Zed Industries)

### Overview

The **Agent Client Protocol (ACP)** is a standard introduced by **Zed Industries** in September 2025 that standardizes communication between **code editors/IDEs (clients)** and **AI coding agents (servers)**. It solves the M×N integration problem — every ACP-compatible agent works with every ACP-compatible editor.

- **Official site:** https://agentclientprotocol.com/
- **Specification:** JSON-RPC 2.0 over stdio (HTTP support in progress)
- **Analogy:** Like LSP (Language Server Protocol) but for AI agents instead of language servers
- **Re-uses MCP JSON representations** where possible, with custom types for coding UX (diffs, etc.)
- **Default text format:** Markdown

### Architecture

```
┌─────────────┐     stdio (JSON-RPC)     ┌──────────────┐
│   Client     │ ◄─────────────────────► │    Agent      │
│ (IDE/Editor) │                          │  (AI Coding   │
│  Zed, etc.   │                          │   Agent)      │
└─────────────┘                          └──────────────┘
```

**Flow:**
1. Client spawns agent as child process (stdio transport)
2. Client creates one or more **sessions** (specifying cwd + MCP servers)
3. Client sends prompts; agent streams progress updates
4. Agent can request permission for tool calls
5. Agent signals completion; client can continue conversation

### Python SDK: `agent-client-protocol`

#### Installation

```bash
pip install agent-client-protocol
# or
uv add agent-client-protocol
```

#### Package Details

| Field | Value |
|-------|-------|
| **PyPI** | https://pypi.org/project/agent-client-protocol/ |
| **Latest Version** | 0.9.0 (Mar 26, 2026) |
| **Python** | >=3.10, <3.15 |
| **License** | Apache-2.0 |
| **Author** | Chojan Shang (psiace@apache.org) |
| **GitHub** | https://github.com/agentclientprotocol/python-sdk |
| **Stars** | 211 |
| **Docs** | https://agentclientprotocol.github.io/python-sdk/ |
| **Zulip Chat** | https://agentclientprotocol.zulipchat.com/ |

#### SDK Structure

```
src/acp/
├── agent.py          # Agent base class
├── client.py         # Client base class
├── transports/       # stdio JSON-RPC plumbing
├── helpers/          # Content blocks, tool calls, permissions
├── schema/           # Generated Pydantic models from ACP spec
├── contrib/          # Experimental utilities
└── interfaces.py     # Client interface definitions
```

#### Key Components

- **`acp.schema`** — Generated Pydantic models tracking every ACP release
- **`acp.Agent`** — Async base class for building agents
- **`acp.Client`** — Async base class for building clients
- **`acp.helpers`** — Builders for content blocks, tool calls, permissions, notifications
- **`acp.contrib`** — Session accumulators, permission brokers, tool call trackers

### Code Example: Creating an ACP Agent

#### Minimal Echo Agent

```python
# /// script
# requires-python = ">=3.10,<3.15"
# dependencies = ["agent-client-protocol"]
# ///

import asyncio
from typing import Any
from uuid import uuid4

from acp import (
    Agent,
    InitializeResponse,
    NewSessionResponse,
    PromptResponse,
    run_agent,
    text_block,
    update_agent_message,
)
from acp.interfaces import Client
from acp.schema import (
    AudioContentBlock,
    ClientCapabilities,
    EmbeddedResourceContentBlock,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    McpServerStdio,
    ResourceContentBlock,
    SseMcpServer,
    TextContentBlock,
)


class EchoAgent(Agent):
    _conn: Client

    def on_connect(self, conn: Client) -> None:
        self._conn = conn

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        return InitializeResponse(protocol_version=protocol_version)

    async def new_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], **kwargs: Any
    ) -> NewSessionResponse:
        return NewSessionResponse(session_id=uuid4().hex)

    async def prompt(
        self,
        prompt: list[
            TextContentBlock
            | ImageContentBlock
            | AudioContentBlock
            | ResourceContentBlock
            | EmbeddedResourceContentBlock
        ],
        session_id: str,
        **kwargs: Any,
    ) -> PromptResponse:
        for block in prompt:
            text = block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
            chunk = update_agent_message(text_block(text))
            await self._conn.session_update(session_id=session_id, update=chunk, source="echo_agent")
        return PromptResponse(stop_reason="end_turn")


async def main() -> None:
    await run_agent(EchoAgent())

if __name__ == "__main__":
    asyncio.run(main())
```

#### Full-Featured Agent (with all lifecycle hooks)

```python
import asyncio
import logging
from typing import Any

from acp import (
    PROTOCOL_VERSION,
    Agent,
    AuthenticateResponse,
    InitializeResponse,
    LoadSessionResponse,
    NewSessionResponse,
    PromptResponse,
    SetSessionModeResponse,
    run_agent,
    text_block,
    update_agent_message,
)
from acp.interfaces import Client
from acp.schema import (
    AgentCapabilities,
    AgentMessageChunk,
    ClientCapabilities,
    HttpMcpServer,
    Implementation,
    McpServerStdio,
    SseMcpServer,
    TextContentBlock,
)


class ExampleAgent(Agent):
    _conn: Client

    def __init__(self) -> None:
        self._next_session_id = 0
        self._sessions: set[str] = set()

    def on_connect(self, conn: Client) -> None:
        self._conn = conn

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        return InitializeResponse(
            protocol_version=PROTOCOL_VERSION,
            agent_capabilities=AgentCapabilities(),
            agent_info=Implementation(name="example-agent", title="Example Agent", version="0.1.0"),
        )

    async def authenticate(self, method_id: str, **kwargs: Any) -> AuthenticateResponse | None:
        return AuthenticateResponse()

    async def new_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], **kwargs: Any
    ) -> NewSessionResponse:
        session_id = str(self._next_session_id)
        self._next_session_id += 1
        self._sessions.add(session_id)
        return NewSessionResponse(session_id=session_id, modes=None)

    async def load_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio],
        session_id: str, **kwargs: Any
    ) -> LoadSessionResponse | None:
        self._sessions.add(session_id)
        return LoadSessionResponse()

    async def prompt(
        self,
        prompt: list[TextContentBlock],
        session_id: str,
        **kwargs: Any,
    ) -> PromptResponse:
        if session_id not in self._sessions:
            self._sessions.add(session_id)
        for block in prompt:
            update = update_agent_message(block)
            await self._conn.session_update(session_id, update)
        return PromptResponse(stop_reason="end_turn")

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        logging.info("Received cancel for session %s", session_id)

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"example": "response"}

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        logging.info("Received extension notification: %s", method)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await run_agent(ExampleAgent())

if __name__ == "__main__":
    asyncio.run(main())
```

### Code Example: Creating an ACP Client

```python
import asyncio
import sys
from pathlib import Path
from typing import Any

from acp import spawn_agent_process, text_block
from acp.interfaces import Client


class SimpleClient(Client):
    async def request_permission(
        self, options, session_id, tool_call, **kwargs: Any
    ):
        return {"outcome": {"outcome": "cancelled"}}

    async def session_update(self, session_id, update, **kwargs):
        print("update:", session_id, update)


async def main() -> None:
    script = Path("examples/echo_agent.py")
    async with spawn_agent_process(SimpleClient(), sys.executable, str(script)) as (conn, _proc):
        await conn.initialize(protocol_version=1)
        session = await conn.new_session(cwd=str(script.parent), mcp_servers=[])
        await conn.prompt(
            session_id=session.session_id,
            prompt=[text_block("Hello from spawn!")],
        )

asyncio.run(main())
```

### Helper Builders (acp.helpers)

```python
from acp import start_tool_call, update_tool_call, text_block, tool_content

# Start a tool call
start_update = start_tool_call("call-42", "Open file", kind="read", status="pending")

# Complete a tool call
finish_update = update_tool_call(
    "call-42",
    status="completed",
    content=[tool_content(text_block("File opened."))],
)
```

### Connecting from Zed Editor

Add to Zed's `settings.json`:

```json
{
  "agent_servers": {
    "My Python Agent": {
      "type": "custom",
      "command": "/abs/path/to/python",
      "args": ["/abs/path/to/my_agent.py"]
    }
  }
}
```

Or with `uv`:

```json
{
  "agent_servers": {
    "My Python Agent": {
      "type": "custom",
      "command": "uv",
      "args": ["run", "/abs/path/to/my_agent.py"]
    }
  }
}
```

### MCP Server Integration

ACP agents receive MCP server configurations during session creation. The client passes MCP servers to the agent:

```python
# In the agent's new_session method:
async def new_session(
    self,
    cwd: str,
    mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio],
    **kwargs: Any,
) -> NewSessionResponse:
    # mcp_servers contains the MCP servers the client wants the agent to use
    # HttpMcpServer, SseMcpServer, McpServerStdio are the three transport types
    ...
```

### Developer Commands

```bash
make install      # Set up uv virtualenv and pre-commit hooks
make check        # Ruff formatting/linting, type analysis, dependency hygiene
make test         # Run pytest with doctests
make gen-all      # Regenerate schema artifacts (when ACP spec updates)
```

### Release History

| Version | Date |
|---------|------|
| 0.9.0 | Mar 26, 2026 |
| 0.8.1 | Feb 13, 2026 |
| 0.8.0 | Feb 7, 2026 |
| 0.7.1 | Dec 28, 2025 |
| 0.7.0 | Dec 4, 2025 |
| 0.6.3 | Nov 3, 2025 |
| 0.5.0 | Oct 25, 2025 |
| 0.0.1 | Sep 6, 2025 |

### Migration Guides

- [0.7 Migration Guide](https://agentclientprotocol.github.io/python-sdk/migration-guide-0.7/)
- [0.8 Migration Guide](https://agentclientprotocol.github.io/python-sdk/migration-guide-0.8/)

---

## Protocol #2: Agent Communication Protocol (IBM/BeeAI)

### Overview

The **Agent Communication Protocol (ACP)** is an open protocol by **IBM/BeeAI** (now part of **A2A under the Linux Foundation**) for communication between **AI agents, applications, and humans**. This is a **different protocol** from the Zed ACP — it uses **HTTP/REST** rather than stdio JSON-RPC.

**IMPORTANT UPDATE:** ACP is now part of A2A under the Linux Foundation. See migration guide: https://github.com/i-am-bee/beeai-platform/blob/main/docs/community-and-support/acp-a2a-migration-guide.mdx

- **GitHub (archived):** https://github.com/i-am-bee/acp (981 stars, archived Aug 2025)
- **Docs:** https://agentcommunicationprotocol.dev
- **DeepLearning.AI Course:** https://www.deeplearning.ai/short-courses/acp-agent-communication-protocol/

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Agent Manifest** | Describes agent's capabilities — name, description, metadata, status |
| **Run** | Single agent execution (sync or streaming) with input/output |
| **Message** | Core communication unit — sequence of ordered content components |
| **MessagePart** | Individual content units (text, image, JSON, etc.) |
| **Await** | Agents can pause to request info and resume |
| **Sessions** | Stateful conversation history across interactions |
| **Trajectory Metadata** | Track multi-step reasoning and tool calling |
| **Distributed Sessions** | Session continuity across server instances |

### Python SDK: `acp-sdk`

#### Installation

```bash
pip install acp-sdk
# or
uv add acp-sdk
```

#### Package Details

| Field | Value |
|-------|-------|
| **PyPI** | https://pypi.org/project/acp-sdk/ |
| **Latest Version** | 1.0.3 (Aug 21, 2025) |
| **Python** | >=3.11, <4.0 |
| **License** | Apache-2.0 |
| **Author** | IBM Corp. |
| **Maintainer** | Tomas Pilar |
| **GitHub** | https://github.com/i-am-bee/acp (archived) |

### Code Example: Creating an Agent Server

```python
# agent.py
import asyncio
from collections.abc import AsyncGenerator

from acp_sdk.models import Message
from acp_sdk.server import Context, RunYield, RunYieldResume, Server

server = Server()

@server.agent()
async def echo(
    input: list[Message], context: Context
) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Echoes everything"""
    for message in input:
        await asyncio.sleep(0.5)
        yield {"thought": "I should echo everything"}
        await asyncio.sleep(0.5)
        yield message

server.run()
```

Start the server:

```bash
uv run agent.py
# Server runs at http://localhost:8000
```

Verify agent availability:

```bash
curl http://localhost:8000/agents
# Response: {"agents": [{"name": "echo", "description": "Echoes everything", "metadata": {}}]}
```

Run the agent via HTTP:

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "echo",
    "input": [
      {
        "role": "user",
        "parts": [
          {
            "content": "Howdy!",
            "content_type": "text/plain"
          }
        ]
      }
    ]
  }'
```

### Code Example: Creating a Client

```python
# client.py
import asyncio

from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

async def example() -> None:
    async with Client(base_url="http://localhost:8000") as client:
        run = await client.run_sync(
            agent="echo",
            input=[
                Message(
                    role="user",
                    parts=[MessagePart(content="Howdy to echo from client!!", content_type="text/plain")]
                )
            ],
        )
        print(run.output)

if __name__ == "__main__":
    asyncio.run(example())
```

### IBM's Agent Connect Protocol SDK (`agntcy-acp`)

A separate IBM-maintained SDK for the **Agent Connect Protocol** (part of the Internet of Agents initiative):

| Field | Value |
|-------|-------|
| **PyPI** | https://pypi.org/project/agntcy-acp/ |
| **Latest Version** | 1.5.2 (Jun 16, 2025) |
| **GitHub** | https://github.com/agntcy/acp-sdk |
| **Stars** | 89 |
| **Docs** | https://docs.agntcy.org/pages/syntactic_sdk/agntcy_acp_sdk.html |
| **SDK Docs** | https://agntcy.github.io/acp-sdk |

This SDK is auto-generated from the OpenAPI ACP specification:

```bash
make generate_acp_client        # Generate sync client
make generate_acp_async_client  # Generate async client
make update_python_subpackage   # Update the agntcy_acp package
```

---

## ACP-MCP Bridge Packages

### `acp-mcp` (IBM)

| Field | Value |
|-------|-------|
| **PyPI** | https://pypi.org/project/acp-mcp/ |
| **Latest Version** | 0.4.1 |
| **Python** | >=3.11, <4.0 |
| **License** | Apache-2.0 |
| **Author** | IBM Corp. |
| **Maintainer** | Tomas Pilar |
| **Description** | Serve ACP agents over MCP |

```bash
pip install acp-mcp
```

This package bridges the Agent Communication Protocol (IBM/BeeAI) to MCP, allowing ACP agents to be consumed as MCP tools.

### Community ACP-MCP Bridges

| Project | Description |
|---------|-------------|
| [GongRzhe/ACP-MCP-Server](https://github.com/GongRzhe/ACP-MCP-Server) | Bridge ACP (Zed) agents with MCP clients (21 stars) |
| [Oortonaut/mcacp](https://github.com/Oortonaut/mcacp) | TypeScript MCP to ACP bridge (5 stars) |
| [ACP Bridge MCP](https://mcp.directory/servers/acp-bridge) | MCP.Directory listing for ACP bridge server |

---

## Key Differences Between the Two ACPs

| Feature | Agent Client Protocol (Zed) | Agent Communication Protocol (IBM/BeeAI) |
|---------|---------------------------|----------------------------------------|
| **Creator** | Zed Industries | IBM / BeeAI |
| **Purpose** | Connect IDEs to coding agents | Connect AI agents to each other |
| **Transport** | stdio (JSON-RPC 2.0) | HTTP/REST |
| **PyPI Package** | `agent-client-protocol` | `acp-sdk` |
| **Latest Version** | 0.9.0 (Mar 2026) | 1.0.3 (Aug 2025) |
| **Python Version** | >=3.10 | >=3.11 |
| **GitHub** | agentclientprotocol/python-sdk | i-am-bee/acp (archived) |
| **Status** | **Active development** | **Archived → migrated to A2A** |
| **MCP Relation** | Receives MCP server configs from client | Can bridge to MCP via acp-mcp |
| **Analogy** | Like LSP for AI agents | Like A2A for agent-to-agent |

---

## Adoption and Ecosystem

### Agent Client Protocol (Zed) — Supported Agents

The following coding agents support ACP (Zed's protocol):

- **Claude Agent** (via Zed's SDK adapter)
- **Codex CLI** (via Zed's adapter)
- **Cursor** (cursor.com/docs/cli/acp)
- **Gemini CLI** (--experimental-acp flag)
- **GitHub Copilot** (public preview)
- **Goose** (Block)
- **Kimi CLI** (MoonshotAI)
- **OpenCode** (sst/opencode)
- **OpenHands**
- **Qwen Code**
- **Cline**
- **Augment Code**
- **Docker's cagent**
- **fast-agent**
- **Junie by JetBrains**
- **Kiro CLI**
- **Mistral Vibe**
- **Qoder CLI**
- And more: https://agentclientprotocol.com/get-started/agents

### Agent Client Protocol (Zed) — Supported Clients (IDEs)

- **Zed** (native support)
- **JetBrains IDEs** (AI Assistant, Junie)
- Any editor implementing the ACP client spec

### Agent Communication Protocol (IBM/BeeAI) — Features

- Rich multimodal messages (text, code, files, media)
- Real-time, background, or streaming responses
- Agent discovery (manifests)
- Long-running task collaboration
- State sharing between agents
- High availability (Redis/PostgreSQL backends)
- Distributed sessions
- Trajectory metadata
- Citation metadata

---

## How MCP and ACP Relate

### MCP (Model Context Protocol)
- **Purpose:** Connect agents to external tools/data sources
- **Created by:** Anthropic (2024)
- **Direction:** Agent → Tools

### ACP (Agent Client Protocol, Zed)
- **Purpose:** Connect editors/IDEs to agents
- **Created by:** Zed Industries (2025)
- **Direction:** Editor → Agent
- **MCP Integration:** Clients pass MCP server configs to agents during session creation

### ACP (Agent Communication Protocol, IBM)
- **Purpose:** Connect agents to other agents
- **Created by:** IBM/BeeAI (2025)
- **Direction:** Agent → Agent
- **MCP Integration:** Can bridge via `acp-mcp` package

### A2A (Agent-to-Agent Protocol)
- **Purpose:** Agent-to-agent communication (Google's approach)
- **Created by:** Google (2025)
- **Note:** IBM's ACP is migrating into A2A under Linux Foundation

---

## Quick Reference: Which Package to Install

| Goal | Package | Command |
|------|---------|---------|
| Build an ACP agent for Zed/IDEs | `agent-client-protocol` | `pip install agent-client-protocol` |
| Build an ACP client for Zed agents | `agent-client-protocol` | `pip install agent-client-protocol` |
| Build an HTTP agent server (IBM style) | `acp-sdk` | `pip install acp-sdk` |
| Build an HTTP agent client (IBM style) | `acp-sdk` | `pip install acp-sdk` |
| Bridge ACP agents to MCP | `acp-mcp` | `pip install acp-mcp` |
| IBM Agent Connect Protocol | `agntcy-acp` | `pip install agntcy-acp` |

---

## Links Summary

### Agent Client Protocol (Zed Industries)
- **Website:** https://agentclientprotocol.com/
- **Python SDK GitHub:** https://github.com/agentclientprotocol/python-sdk
- **Python SDK Docs:** https://agentclientprotocol.github.io/python-sdk/
- **Python SDK PyPI:** https://pypi.org/project/agent-client-protocol/
- **Quickstart:** https://agentclientprotocol.github.io/python-sdk/quickstart/
- **Use Cases:** https://agentclientprotocol.github.io/python-sdk/use-cases/
- **Contrib Helpers:** https://agentclientprotocol.github.io/python-sdk/contrib/
- **Supported Agents List:** https://agentclientprotocol.com/get-started/agents
- **Introduction:** https://agentclientprotocol.com/get-started/introduction
- **Tool Calls Spec:** https://agentclientprotocol.com/protocol/tool-calls
- **Zulip Community:** https://agentclientprotocol.zulipchat.com/
- **JetBrains ACP Docs:** https://www.jetbrains.com/help/ai-assistant/acp.html
- **LangChain ACP Docs:** https://docs.langchain.com/oss/python/deepagents/acp

### Agent Communication Protocol (IBM/BeeAI)
- **GitHub (archived):** https://github.com/i-am-bee/acp
- **Docs:** https://agentcommunicationprotocol.dev
- **PyPI:** https://pypi.org/project/acp-sdk/
- **DeepLearning.AI Course:** https://www.deeplearning.ai/short-courses/acp-agent-communication-protocol/
- **A2A Migration Guide:** https://github.com/i-am-bee/beeai-platform/blob/main/docs/community-and-support/acp-a2a-migration-guide.mdx

### IBM Agent Connect Protocol (IoA)
- **GitHub:** https://github.com/agntcy/acp-sdk
- **PyPI:** https://pypi.org/project/agntcy-acp/
- **Docs:** https://docs.agntcy.org/pages/syntactic_sdk/agntcy_acp_sdk.html

### Bridge Packages
- **acp-mcp PyPI:** https://pypi.org/project/acp-mcp/
- **ACP-MCP-Server GitHub:** https://github.com/GongRzhe/ACP-MCP-Server
- **mcacp GitHub:** https://github.com/Oortonaut/mcacp

### Articles and Guides
- **Developer's Intro to ACP:** https://www.calummurray.ca/blog/intro-to-acp
- **Ultimate Guide:** https://techwithdavis.com/agent-client-protocol/
- **MCP vs ACP vs A2A:** https://medium.com/@kulakshay97/understanding-agentic-ai-protocols-mcp-vs-acp-vs-a2a-35db7f26f17e
- **IBM Tutorial:** https://www.ibm.com/think/tutorials/acp-ai-agent-interoperability-building-multi-agent-workflows
- **Heidloff Blog:** https://heidloff.net/article/mcp-acp/
