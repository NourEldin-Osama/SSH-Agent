import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from acp_server import ACPServerRuntime
from database import Base, engine
from logger import configure_logging
from routers import agents, chat, commands, memories, permissions, servers, sessions
from routers import terminal
from routers.settings import router as settings_router
from ws import active_connections, broadcast_to_session
from loguru import logger

load_dotenv()
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")

    acp_port = int(os.getenv("ACP_SERVER_PORT", "8001"))
    runtime = ACPServerRuntime(port=acp_port)
    app.state.acp_runtime = runtime
    await runtime.start()
    status = runtime.status_payload()
    if status.get("failed"):
        logger.error("ACP server startup failed: {}", status.get("failure_reason"))
    await broadcast_to_session("global", "acp_status", status)

    yield

    await runtime.stop()
    for conns in active_connections.values():
        for conn in conns:
            await conn.close()
    active_connections.clear()


app = FastAPI(title="SSH Agent Commander", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(servers.router)
app.include_router(sessions.router)
app.include_router(commands.router)
app.include_router(agents.router)
app.include_router(memories.router)
app.include_router(permissions.router)
app.include_router(chat.router)
app.include_router(settings_router)
app.include_router(terminal.router)


@app.get("/scalar", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        title="SSH Agent Commander API",
        openapi_url=app.openapi_url,
    )


@app.get("/api/acp/status")
def get_acp_status():
    runtime = getattr(app.state, "acp_runtime", None)
    if runtime is None:
        return {
            "running": False,
            "failed": True,
            "failure_reason": "ACP runtime not initialized",
            "port": int(os.getenv("ACP_SERVER_PORT", "8001")),
            "current_model": os.getenv("ACP_MODEL_NAME", ""),
            "tools": [],
        }
    return runtime.status_payload()


@app.post("/api/acp/tools/{tool_name}")
async def invoke_acp_tool(tool_name: str, payload: dict):
    runtime = getattr(app.state, "acp_runtime", None)
    if runtime is None:
        return {"ok": False, "error": "ACP runtime not initialized"}

    session_id = payload.get("session_id")
    server_id = payload.get("server_id")
    if not isinstance(session_id, int) or not isinstance(server_id, int):
        return {"ok": False, "error": "session_id and server_id are required integers"}

    result = await runtime.invoke_tool(
        tool_name=tool_name,
        session_id=session_id,
        server_id=server_id,
        arguments=payload.get("arguments") or {},
    )
    logger.info(
        "ACP tool invoked: tool_name={}, session_id={}, server_id={}, ok={}",
        tool_name,
        session_id,
        server_id,
        result.get("ok") if isinstance(result, dict) else None,
    )
    return result


@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections.setdefault(session_id, []).append(websocket)
    logger.info("WebSocket connected session_id={}", session_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            del active_connections[session_id]
        logger.info("WebSocket disconnected session_id={}", session_id)
