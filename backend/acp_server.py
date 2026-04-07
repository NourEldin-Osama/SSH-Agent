import asyncio
import json
import os
import re
import shlex
import time
from typing import Any, Awaitable, Callable

from acp import (
    Agent,
    InitializeResponse,
    NewSessionResponse,
    PROTOCOL_VERSION,
    PromptResponse,
    run_agent,
    spawn_agent_process,
    text_block,
    update_agent_message,
)
from acp.interfaces import Client
from acp.schema import (
    AllowedOutcome,
    ClientCapabilities,
    CreateTerminalResponse,
    HttpMcpServer,
    Implementation,
    McpServerStdio,
    ReadTextFileResponse,
    RequestPermissionResponse,
    SseMcpServer,
    TerminalOutputResponse,
    TextContentBlock,
    WaitForTerminalExitResponse,
)

from database import SessionLocal
from mcp_tools import (
    ToolContext,
    execute_command_tool,
    get_current_server_info_tool,
    get_tool_definitions,
    read_server_memory_tool,
    write_server_memory_tool,
)
from loguru import logger


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


def _resolve_model(preferred_model: str | None) -> str:
    return preferred_model or os.getenv("ACP_MODEL_NAME", "")


def _resolve_provider_kind(base_url: str | None) -> str:
    return "local-agent"


def _resolve_agent_executable(agent_name: str) -> str:
    env_key = f"{agent_name.upper().replace('-', '_')}_EXECUTABLE"
    if env_key in os.environ and os.environ[env_key].strip():
        return os.environ[env_key].strip()
    if agent_name == "claude-code":
        return os.getenv("CLAUDE_CODE_EXECUTABLE", "claude")
    if agent_name == "opencode":
        return os.getenv("OPENCODE_EXECUTABLE", "opencode")
    return agent_name


def _resolve_agent_acp_args(agent_name: str) -> list[str]:
    specific_key = f"{agent_name.upper().replace('-', '_')}_ACP_ARGS"
    raw = os.getenv(specific_key, "").strip() or os.getenv("ACP_AGENT_ARGS", "").strip()
    return shlex.split(raw) if raw else []


def _build_agent_prompt(content: str, memory_info: dict[str, Any]) -> str:
    return (
        "You are SSH Agent Commander assistant. "
        "Server connection details are already configured internally. "
        "Never ask for host, username, or port. "
        "When execution is needed, use execute_command MCP tool.\n\n"
        f"User request: {content}\n"
        f"Memory context: {json.dumps(memory_info, ensure_ascii=True)}\n"
        "If command execution is needed, explicitly state the command intent."
    )


async def _run_local_agent_command(
    agent_name: str,
    model: str,
    prompt: str,
) -> tuple[str, str, int, list[str]]:
    executable = _resolve_agent_executable(agent_name)
    cmd = [executable, "-p", prompt]
    if model:
        cmd.extend(["--model", model])

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    return stdout, stderr, int(process.returncode or 0), cmd


def _infer_mcp_command(user_text: str) -> str | None:
    lowered = (user_text or "").strip().lower()
    if not lowered:
        return None

    direct_match = re.search(r"\b(?:run|execute)\s+(.+)$", lowered)
    if direct_match:
        candidate = direct_match.group(1).strip()
        if candidate.startswith("command "):
            candidate = candidate[len("command ") :].strip()
        if candidate:
            return candidate

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
    if lowered == "ls" or lowered.startswith("ls "):
        return lowered
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


class _ACPBridgeClient:
    def __init__(self) -> None:
        self._conn: Client | None = None
        self._agent_messages: list[str] = []
        self._config_options: list[dict[str, Any]] = []

    def on_connect(self, conn: Client) -> None:
        self._conn = conn

    @property
    def config_options(self) -> list[dict[str, Any]]:
        return list(self._config_options)

    def reset_messages(self) -> None:
        self._agent_messages = []

    def joined_messages(self) -> str:
        return "\n".join(part for part in self._agent_messages if part).strip()

    async def request_permission(
        self, options, session_id: str, tool_call, **kwargs: Any
    ):
        chosen = options[0].option_id if options else "allow_once"
        return RequestPermissionResponse(
            outcome=AllowedOutcome(outcome="selected", option_id=chosen)
        )

    async def session_update(self, session_id: str, update, **kwargs: Any) -> None:
        kind = getattr(update, "session_update", None)
        if kind == "agent_message_chunk":
            content = getattr(update, "content", None)
            text = getattr(content, "text", "") if content else ""
            if text:
                self._agent_messages.append(text)
            return

        if kind == "config_option_update":
            options = getattr(update, "config_options", None) or []
            self._config_options = [
                o.model_dump(by_alias=True, exclude_none=True) for o in options
            ]

    async def write_text_file(
        self, content: str, path: str, session_id: str, **kwargs: Any
    ):
        return None

    async def read_text_file(
        self,
        path: str,
        session_id: str,
        limit: int | None = None,
        line: int | None = None,
        **kwargs: Any,
    ):
        return ReadTextFileResponse(content="")

    async def create_terminal(
        self,
        command: str,
        session_id: str,
        args: list[str] | None = None,
        cwd: str | None = None,
        env: list[Any] | None = None,
        output_byte_limit: int | None = None,
        **kwargs: Any,
    ):
        return CreateTerminalResponse(terminal_id="unsupported")

    async def terminal_output(self, session_id: str, terminal_id: str, **kwargs: Any):
        return TerminalOutputResponse(output="", truncated=False)

    async def release_terminal(self, session_id: str, terminal_id: str, **kwargs: Any):
        return None

    async def wait_for_terminal_exit(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ):
        return WaitForTerminalExitResponse(exit_code=0)

    async def kill_terminal(self, session_id: str, terminal_id: str, **kwargs: Any):
        return None

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"ok": False, "error": f"Unsupported client ext method: {method}"}

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        return None


class ACPClientBridge:
    async def negotiate(
        self,
        agent_name: str,
        preferred_model: str | None = None,
        prompt_text: str | None = None,
    ) -> dict[str, Any]:
        executable = _resolve_agent_executable(agent_name)
        args = _resolve_agent_acp_args(agent_name)
        client = _ACPBridgeClient()

        async with spawn_agent_process(client, executable, *args) as (conn, process):
            await conn.initialize(
                protocol_version=PROTOCOL_VERSION,
                client_capabilities=ClientCapabilities(),
                client_info=Implementation(
                    name="ssh-agent-commander-client",
                    title="SSH Agent Commander Client",
                    version="0.1.0",
                ),
            )

            session = await conn.new_session(cwd=os.getcwd(), mcp_servers=[])
            session_id = session.session_id

            config_options = [
                o.model_dump(by_alias=True, exclude_none=True)
                for o in (session.config_options or [])
            ]

            if (not config_options) and getattr(session, "models", None):
                model_state = session.models
                available = [
                    {
                        "value": m.model_id,
                        "name": m.name,
                        "description": m.description,
                    }
                    for m in (model_state.available_models or [])
                ]
                config_options = [
                    {
                        "id": "model",
                        "name": "Model",
                        "category": "model",
                        "type": "select",
                        "currentValue": model_state.current_model_id,
                        "options": available,
                    }
                ]

            target_model = preferred_model or os.getenv("ACP_MODEL_NAME", "")
            if target_model:
                model_option = next(
                    (
                        opt
                        for opt in config_options
                        if opt.get("category") == "model" or opt.get("id") == "model"
                    ),
                    None,
                )

                if model_option and model_option.get("id"):
                    try:
                        set_result = await conn.set_config_option(
                            config_id=str(model_option.get("id")),
                            session_id=session_id,
                            value=target_model,
                        )
                        config_options = [
                            o.model_dump(by_alias=True, exclude_none=True)
                            for o in (set_result.config_options or [])
                        ]
                    except Exception:
                        logger.debug(
                            "ACP set_config_option failed agent={} config_id={} model={}",
                            agent_name,
                            model_option.get("id"),
                            target_model,
                        )
                else:
                    try:
                        await conn.set_session_model(
                            model_id=target_model,
                            session_id=session_id,
                        )
                    except Exception:
                        logger.debug(
                            "ACP set_session_model failed agent={} model={}",
                            agent_name,
                            target_model,
                        )

            response_text = ""
            if prompt_text:
                client.reset_messages()
                await conn.prompt(
                    prompt=[text_block(prompt_text)], session_id=session_id
                )
                response_text = client.joined_messages()

            try:
                await conn.close_session(session_id=session_id)
            except Exception:
                pass

            return {
                "session_id": session_id,
                "config_options": client.config_options or config_options,
                "response_text": response_text,
            }


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
        self._acp_client_bridge = ACPClientBridge()

    async def _agent_generate_response(
        self,
        session_id: int,
        server_id: int,
        content: str,
        agent_name: str | None = None,
        model: str | None = None,
        progress_cb: Callable[[str, dict[str, Any] | None], Awaitable[None]]
        | None = None,
    ) -> str:
        async def emit(stage: str, details: dict[str, Any] | None = None) -> None:
            if progress_cb is not None:
                await progress_cb(stage, details)

        async def call_tool(
            tool_name: str,
            args: dict[str, Any] | None = None,
            *,
            debug_enabled: bool,
        ) -> dict[str, Any]:
            payload = args or {}
            if debug_enabled:
                await emit(
                    "debug",
                    {
                        "phase": "tool_call_start",
                        "tool": tool_name,
                        "arguments": payload,
                    },
                )
            result = await self._tooling.invoke(
                tool_name=tool_name,
                session_id=session_id,
                server_id=server_id,
                arguments=payload,
            )
            if debug_enabled:
                await emit(
                    "debug",
                    {
                        "phase": "tool_call_end",
                        "tool": tool_name,
                        "result": result,
                    },
                )
            return result

        db = SessionLocal()
        try:
            from models import AgentConfig  # local import to avoid cycles

            debug_enabled = _is_debug_enabled()
            if debug_enabled:
                await emit(
                    "debug",
                    {
                        "phase": "agent_request_start",
                        "session_id": session_id,
                        "server_id": server_id,
                        "user_input": content,
                        "runtime_mode": self._mode,
                        "acp_real_model_enabled": _truthy(
                            os.getenv("ACP_REAL_MODEL_ENABLED", "false")
                        ),
                        "model": os.getenv("ACP_MODEL_NAME", "gpt-4o-mini"),
                    },
                )

            active_agent = (
                db.query(AgentConfig)
                .filter(AgentConfig.is_active.is_(True))
                .order_by(AgentConfig.created_at.desc())
                .first()
            )
            if agent_name:
                preferred_agent = (
                    db.query(AgentConfig)
                    .filter(AgentConfig.agent_name == agent_name)
                    .order_by(AgentConfig.created_at.desc())
                    .first()
                )
                if preferred_agent:
                    active_agent = preferred_agent
            if active_agent is None:
                if debug_enabled:
                    await emit(
                        "debug",
                        {
                            "phase": "agent_request_end",
                            "outcome": "no_active_agent",
                        },
                    )
                return "No active agent configured."

            logger.info(
                "Agent request start session_id={} server_id={} selected_agent={} requested_model={}",
                session_id,
                server_id,
                active_agent.agent_name,
                model,
            )

            await emit("thinking", {"message": "Reading server context"})

            server_info = await call_tool(
                "get_current_server_info",
                {},
                debug_enabled=debug_enabled,
            )
            await emit(
                "tool_call", {"tool": "get_current_server_info", "result": server_info}
            )

            await emit("thinking", {"message": "Reading server memory"})
            memory_info = await call_tool(
                "read_server_memory",
                {},
                debug_enabled=debug_enabled,
            )
            await emit(
                "tool_call", {"tool": "read_server_memory", "result": memory_info}
            )

            selected_model = _resolve_model(model)
            provider_kind = _resolve_provider_kind(active_agent.base_url)
            if debug_enabled:
                await emit(
                    "debug",
                    {
                        "phase": "agent_selection",
                        "selected_agent": active_agent.agent_name,
                        "provider_kind": provider_kind,
                        "selected_model": selected_model,
                        "requested_agent": agent_name,
                        "requested_model": model,
                    },
                )

            await emit(
                "thinking",
                {
                    "message": "Running local agent executable",
                    "agent": active_agent.agent_name,
                    "model": selected_model,
                },
            )

            prompt_text = _build_agent_prompt(content, memory_info)

            if _truthy(os.getenv("ACP_CLIENT_ENABLED", "false")):
                try:
                    await emit(
                        "thinking",
                        {
                            "message": "Negotiating ACP session",
                            "agent": active_agent.agent_name,
                            "model": selected_model,
                        },
                    )
                    bridge_result = await self._acp_client_bridge.negotiate(
                        agent_name=active_agent.agent_name,
                        preferred_model=selected_model,
                        prompt_text=prompt_text,
                    )
                    bridge_response = (bridge_result.get("response_text") or "").strip()
                    if bridge_response:
                        await emit("completed", {"message": "ACP response received"})
                        logger.info(
                            "ACP client prompt succeeded session_id={} server_id={} agent={} model={}",
                            session_id,
                            server_id,
                            active_agent.agent_name,
                            selected_model,
                        )
                        return bridge_response
                    logger.warning(
                        "ACP client prompt completed with empty response session_id={} server_id={} agent={}",
                        session_id,
                        server_id,
                        active_agent.agent_name,
                    )
                except Exception as exc:
                    logger.warning(
                        "ACP client negotiation failed; falling back to local command mode agent={} error={}",
                        active_agent.agent_name,
                        exc,
                    )
                    if debug_enabled:
                        await emit(
                            "debug",
                            {
                                "phase": "acp_client_fallback",
                                "agent": active_agent.agent_name,
                                "error": str(exc),
                            },
                        )

            started = time.perf_counter()
            (
                stdout_text,
                stderr_text,
                return_code,
                command_parts,
            ) = await _run_local_agent_command(
                active_agent.agent_name,
                selected_model,
                prompt_text,
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)

            if debug_enabled:
                await emit(
                    "debug",
                    {
                        "phase": "local_agent_exec",
                        "command": " ".join(shlex.quote(p) for p in command_parts),
                        "return_code": return_code,
                        "elapsed_ms": elapsed_ms,
                        "stdout_preview": stdout_text[:1000],
                        "stderr_preview": stderr_text[:1000],
                    },
                )

            logger.info(
                "Local agent execution finished session_id={} server_id={} agent={} model={} rc={} elapsed_ms={}",
                session_id,
                server_id,
                active_agent.agent_name,
                selected_model,
                return_code,
                elapsed_ms,
            )

            if return_code != 0:
                await emit(
                    "error",
                    {
                        "message": "Local agent command failed",
                        "return_code": return_code,
                        "stderr": stderr_text[:2000],
                    },
                )

            inferred = _infer_mcp_command(content)
            if inferred:
                if debug_enabled:
                    await emit(
                        "debug",
                        {
                            "phase": "mcp_inference",
                            "inferred_command": inferred,
                            "reason": "fallback_path",
                        },
                    )
                await emit(
                    "thinking",
                    {
                        "message": "Fallback mode: auto-running MCP execute_command",
                        "command": inferred,
                    },
                )
                exec_result = await call_tool(
                    "execute_command",
                    {
                        "title": "Auto MCP command",
                        "description": "Fallback auto-detected user intent",
                        "command": inferred,
                        "expected_output": "Command output",
                        "is_risky": False,
                    },
                    debug_enabled=debug_enabled,
                )
                await emit(
                    "tool_call",
                    {
                        "tool": "execute_command",
                        "result": exec_result,
                    },
                )
            result_text = (stdout_text or stderr_text or "").strip()
            if not result_text:
                result_text = "No response from local agent executable."

            await emit("completed", {"message": "Local agent response received"})
            if debug_enabled:
                await emit(
                    "debug",
                    {
                        "phase": "agent_request_end",
                        "outcome": "local_agent_response",
                        "return_code": return_code,
                    },
                )
            return result_text
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
        logger.info("ACP runtime started on port {}", self.port)
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
                logger.exception("ACP runtime crashed: {}", exc)
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
            "acp_client_enabled": _truthy(os.getenv("ACP_CLIENT_ENABLED", "false")),
            "current_model": os.getenv("ACP_MODEL_NAME", ""),
            "tools": [t["name"] for t in get_tool_definitions()],
        }

    async def fetch_agent_config_options(
        self,
        agent_name: str,
        preferred_model: str | None = None,
    ) -> list[dict[str, Any]]:
        if not _truthy(os.getenv("ACP_CLIENT_ENABLED", "false")):
            return []
        result = await self._acp_client_bridge.negotiate(
            agent_name=agent_name,
            preferred_model=preferred_model,
            prompt_text=None,
        )
        return result.get("config_options") or []

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
        agent_name: str | None = None,
        model: str | None = None,
        progress_cb: Callable[[str, dict[str, Any] | None], Awaitable[None]]
        | None = None,
    ) -> str:
        return await self._agent_generate_response(
            session_id,
            server_id,
            content,
            agent_name=agent_name,
            model=model,
            progress_cb=progress_cb,
        )


def tool_result_to_text(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=True)
