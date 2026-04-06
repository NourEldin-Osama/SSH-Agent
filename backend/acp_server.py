import asyncio
import json
import logging
import os
from typing import Any, Awaitable, Callable

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
    ClientCapabilities,
    HttpMcpServer,
    Implementation,
    McpServerStdio,
    SseMcpServer,
    TextContentBlock,
)

from database import SessionLocal
from encryption import decrypt_value
from mcp_tools import (
    ToolContext,
    execute_command_tool,
    get_current_server_info_tool,
    get_tool_definitions,
    read_server_memory_tool,
    write_server_memory_tool,
)

logger = logging.getLogger("ssh-agent-commander.acp")


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_debug_enabled() -> bool:
    db = SessionLocal()
    try:
        from models import AppSetting  # local import to avoid cycles

        setting = db.query(AppSetting).filter(AppSetting.key == "debug_mode").first()
        return bool(setting and _truthy(setting.value))
    finally:
        db.close()


def _infer_mcp_command(user_text: str) -> str | None:
    lowered = (user_text or "").strip().lower()
    if not lowered:
        return None

    if "list" in lowered and (
        "folder" in lowered
        or "directory" in lowered
        or "directories" in lowered
        or "files" in lowered
    ):
        return "ls -la"
    if "pwd" in lowered or "current path" in lowered:
        return "pwd"
    if "disk" in lowered and ("usage" in lowered or "space" in lowered):
        return "df -h"
    if "memory" in lowered and "usage" in lowered:
        return "free -h"
    if "uptime" in lowered:
        return "uptime"
    if "whoami" in lowered:
        return "whoami"
    if "use mcp" in lowered or "execute_command" in lowered:
        return "ls -la"
    return None


class ACPToolingService:
    async def invoke(
        self,
        tool_name: str,
        session_id: int,
        server_id: int,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        args = arguments or {}
        ctx = ToolContext(session_id=session_id, server_id=server_id)
        db = SessionLocal()
        try:
            if tool_name == "execute_command":
                required = {"title", "description", "command"}
                missing = required - set(args.keys())
                if missing:
                    return {
                        "ok": False,
                        "error": f"Missing required args: {', '.join(sorted(missing))}",
                    }
                return await execute_command_tool(db, ctx, args)
            if tool_name == "read_server_memory":
                return await read_server_memory_tool(db, ctx)
            if tool_name == "write_server_memory":
                content = args.get("content")
                if not content:
                    return {"ok": False, "error": "Missing required arg: content"}
                return await write_server_memory_tool(
                    db,
                    ctx,
                    content=content,
                    source=args.get("source", "ai"),
                    approved=bool(args.get("approved", False)),
                )
            if tool_name == "get_current_server_info":
                return await get_current_server_info_tool(db, ctx)
            return {"ok": False, "error": f"Unknown tool: {tool_name}"}
        finally:
            db.close()


class SSHAgentCommanderAgent(Agent):
    _conn: Client

    def __init__(self, tooling: ACPToolingService):
        super().__init__()
        self._next_session_id = 1
        self._tooling = tooling

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
            protocol_version=protocol_version,
            agent_info=Implementation(
                name="ssh-agent-commander", title="SSH Agent Commander", version="0.1.0"
            ),
        )

    async def new_session(
        self,
        cwd: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio],
        **kwargs: Any,
    ) -> NewSessionResponse:
        session_id = str(self._next_session_id)
        self._next_session_id += 1
        return NewSessionResponse(session_id=session_id)

    async def prompt(
        self,
        prompt: list[TextContentBlock],
        session_id: str,
        **kwargs: Any,
    ) -> PromptResponse:
        text_parts: list[str] = []
        for block in prompt:
            text = (
                block.get("text", "")
                if isinstance(block, dict)
                else getattr(block, "text", "")
            )
            if text:
                text_parts.append(text)

        response_text = "\n".join(text_parts) if text_parts else ""
        await self._conn.session_update(
            session_id=session_id,
            update=update_agent_message(text_block(response_text)),
            source="ssh-agent-commander",
        )
        return PromptResponse(stop_reason="end_turn")

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method not in {
            "tools/call",
            "mcp/tools/call",
            "ssh-agent-commander/tools/call",
        }:
            return {"ok": False, "error": f"Unsupported method: {method}"}

        tool_name = params.get("tool_name")
        session_id = params.get("session_id")
        server_id = params.get("server_id")
        arguments = params.get("arguments") or {}

        if not isinstance(tool_name, str):
            return {"ok": False, "error": "tool_name is required"}
        if not isinstance(session_id, int) or not isinstance(server_id, int):
            return {
                "ok": False,
                "error": "session_id and server_id are required integers",
            }

        return await self._tooling.invoke(
            tool_name=tool_name,
            session_id=session_id,
            server_id=server_id,
            arguments=arguments,
        )


class ACPServerRuntime:
    def __init__(self, port: int):
        self.port = port
        self._task: asyncio.Task | None = None
        self._active = False
        self._failed = False
        self._failure_reason: str | None = None
        self._mode = "http-bridge"
        self._tooling = ACPToolingService()

    async def _agent_generate_response(
        self,
        session_id: int,
        server_id: int,
        content: str,
        progress_cb: Callable[[str, dict[str, Any] | None], Awaitable[None]]
        | None = None,
    ) -> str:
        async def emit(stage: str, details: dict[str, Any] | None = None) -> None:
            if progress_cb is not None:
                await progress_cb(stage, details)

        db = SessionLocal()
        try:
            from models import AgentConfig  # local import to avoid cycles

            active_agent = (
                db.query(AgentConfig)
                .filter(AgentConfig.is_active.is_(True))
                .order_by(AgentConfig.created_at.desc())
                .first()
            )
            if active_agent is None:
                return "No active agent configured."

            await emit("thinking", {"message": "Reading server context"})

            server_info = await self._tooling.invoke(
                tool_name="get_current_server_info",
                session_id=session_id,
                server_id=server_id,
                arguments={},
            )
            await emit(
                "tool_call", {"tool": "get_current_server_info", "result": server_info}
            )

            await emit("thinking", {"message": "Reading server memory"})
            memory_info = await self._tooling.invoke(
                tool_name="read_server_memory",
                session_id=session_id,
                server_id=server_id,
                arguments={},
            )
            await emit(
                "tool_call", {"tool": "read_server_memory", "result": memory_info}
            )

            if active_agent.base_url and _truthy(
                os.getenv("ACP_REAL_MODEL_ENABLED", "false")
            ):
                try:
                    import httpx

                    debug_enabled = _is_debug_enabled()
                    await emit(
                        "thinking",
                        {
                            "message": "Calling model provider",
                            "provider": active_agent.base_url,
                            "model": os.getenv("ACP_MODEL_NAME", "gpt-4o-mini"),
                        },
                    )

                    api_key = decrypt_value(active_agent.encrypted_api_key)
                    payload = {
                        "model": os.getenv("ACP_MODEL_NAME", "gpt-4o-mini"),
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are SSH Agent Commander assistant. Use provided server and memory context.",
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"User: {content}\n"
                                    f"Server: {server_info}\n"
                                    f"Memory: {memory_info}\n"
                                    "Respond with concise operational guidance and next best command."
                                ),
                            },
                        ],
                    }
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": os.getenv(
                            "OPENROUTER_SITE_URL", "http://localhost:5173"
                        ),
                        "X-Title": os.getenv(
                            "OPENROUTER_APP_NAME", "SSH Agent Commander"
                        ),
                    }
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.post(
                            active_agent.base_url,
                            json=payload,
                            headers=headers,
                        )
                    if debug_enabled:
                        await emit(
                            "debug",
                            {
                                "agent": active_agent.agent_name,
                                "provider": active_agent.base_url,
                                "model": payload["model"],
                                "request_command": (
                                    f"POST {active_agent.base_url} "
                                    f"model={payload['model']} messages=[system,user]"
                                ),
                                "response_status": resp.status_code,
                            },
                        )
                    if resp.status_code < 400:
                        body = resp.json()
                        choices = body.get("choices") or []
                        if choices:
                            msg = choices[0].get("message") or {}
                            text = msg.get("content")
                            if text:
                                inferred = _infer_mcp_command(content)
                                if inferred:
                                    await emit(
                                        "thinking",
                                        {
                                            "message": "Auto-running MCP execute_command based on request",
                                            "command": inferred,
                                        },
                                    )
                                    exec_result = await self._tooling.invoke(
                                        tool_name="execute_command",
                                        session_id=session_id,
                                        server_id=server_id,
                                        arguments={
                                            "title": "Auto MCP command",
                                            "description": "Auto-detected user intent",
                                            "command": inferred,
                                            "expected_output": "Command output",
                                            "is_risky": False,
                                        },
                                    )
                                    await emit(
                                        "tool_call",
                                        {
                                            "tool": "execute_command",
                                            "result": exec_result,
                                        },
                                    )
                                await emit(
                                    "completed", {"message": "Model response received"}
                                )
                                return text
                    body_text = resp.text[:1000]
                    await emit(
                        "error",
                        {
                            "message": "Provider returned error response",
                            "status_code": resp.status_code,
                            "body": body_text,
                        },
                    )
                except Exception as exc:
                    logger.warning(
                        "Real model path failed; using local ACP tool synthesis: %s",
                        exc,
                    )
                    await emit("error", {"message": str(exc)})

            await emit("completed", {"message": "Using fallback response path"})
            inferred = _infer_mcp_command(content)
            if inferred:
                await emit(
                    "thinking",
                    {
                        "message": "Fallback mode: auto-running MCP execute_command",
                        "command": inferred,
                    },
                )
                exec_result = await self._tooling.invoke(
                    tool_name="execute_command",
                    session_id=session_id,
                    server_id=server_id,
                    arguments={
                        "title": "Auto MCP command",
                        "description": "Fallback auto-detected user intent",
                        "command": inferred,
                        "expected_output": "Command output",
                        "is_risky": False,
                    },
                )
                await emit(
                    "tool_call",
                    {
                        "tool": "execute_command",
                        "result": exec_result,
                    },
                )
            return (
                f"[{active_agent.agent_name}] Received: {content}\n"
                f"Server context: {server_info}\n"
                f"Memory context: {memory_info}\n"
                "Use execute_command MCP tool to propose actionable steps."
            )
        finally:
            db.close()

    async def start(self) -> None:
        if self._active:
            return
        self._failed = False
        self._failure_reason = None
        stdio_enabled = os.getenv("ACP_STDIO_ENABLED", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if stdio_enabled:
            self._mode = "zed-stdio"
            self._task = asyncio.create_task(self._run_forever())
        else:
            self._mode = "http-bridge"
            self._task = None
            logger.info(
                "ACP stdio server disabled; using tool bridge mode. "
                "Set ACP_STDIO_ENABLED=true to enable zed stdio server process."
            )
        self._active = True

    async def stop(self) -> None:
        self._active = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_forever(self) -> None:
        logger.info("ACP runtime started on port %s", self.port)
        while True:
            try:
                await run_agent(SSHAgentCommanderAgent(self._tooling), port=self.port)
                return
            except asyncio.CancelledError:
                logger.info("ACP runtime stopped")
                raise
            except Exception as exc:
                self._failed = True
                self._failure_reason = str(exc)
                logger.exception("ACP runtime crashed: %s", exc)
                await asyncio.sleep(3)

    def status_payload(self) -> dict[str, Any]:
        task_running = self._active and (
            self._task is None or (self._task and not self._task.done())
        )
        return {
            "running": task_running,
            "failed": self._failed,
            "failure_reason": self._failure_reason,
            "port": self.port,
            "mode": self._mode,
            "tools": [t["name"] for t in get_tool_definitions()],
        }

    async def invoke_tool(
        self,
        tool_name: str,
        session_id: int,
        server_id: int,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._tooling.invoke(tool_name, session_id, server_id, arguments)

    async def generate_agent_response(
        self,
        session_id: int,
        server_id: int,
        content: str,
        progress_cb: Callable[[str, dict[str, Any] | None], Awaitable[None]]
        | None = None,
    ) -> str:
        return await self._agent_generate_response(
            session_id,
            server_id,
            content,
            progress_cb=progress_cb,
        )


def tool_result_to_text(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=True)
