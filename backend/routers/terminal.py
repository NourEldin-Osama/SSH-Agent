from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from command_runtime import get_server_auth
from database import get_db
from models import Server
from schemas import TerminalCommandCreate, TerminalCommandResponse
from ssh_executor import SSHExecutor
from ws import broadcast_to_session

router = APIRouter(prefix="/api/terminal", tags=["terminal"])


@router.post("/execute", response_model=TerminalCommandResponse)
async def execute_terminal_command(
    payload: TerminalCommandCreate,
    db: Session = Depends(get_db),
):
    server = db.query(Server).filter(Server.id == payload.server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    executor = SSHExecutor()
    executed_at = datetime.utcnow()
    try:
        executor.connect(**get_server_auth(server))
        result = executor.execute(payload.command, timeout=payload.timeout)
    except Exception as exc:
        result = {"output": str(exc), "exit_status": 1}
    finally:
        executor.close()

    event_payload = {
        "server_id": payload.server_id,
        "session_id": payload.session_id,
        "command": payload.command,
        "output": result.get("output", ""),
        "exit_status": result.get("exit_status", 1),
        "executed_at": executed_at.isoformat(),
    }

    if payload.session_id is not None:
        await broadcast_to_session(
            str(payload.session_id),
            "terminal_command_result",
            event_payload,
        )

    return TerminalCommandResponse(
        server_id=payload.server_id,
        session_id=payload.session_id,
        command=payload.command,
        output=result.get("output", ""),
        exit_status=result.get("exit_status", 1),
        executed_at=executed_at,
    )
