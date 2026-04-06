from datetime import datetime

from sqlalchemy.orm import Session

from encryption import decrypt_value
from models import Command, Server
from ssh_executor import SSHExecutor
from ws import broadcast_to_session


def get_server_auth(server: Server) -> dict:
    auth = {
        "hostname": server.hostname,
        "port": server.port,
        "username": server.username,
        "auth_method": server.auth_method,
        "password": None,
        "ssh_key": None,
        "passphrase": None,
    }
    if server.encrypted_password:
        auth["password"] = decrypt_value(server.encrypted_password)
    if server.encrypted_ssh_key:
        auth["ssh_key"] = decrypt_value(server.encrypted_ssh_key)
    if server.encrypted_passphrase:
        auth["passphrase"] = decrypt_value(server.encrypted_passphrase)
    return auth


def run_command_sync(command: Command, db: Session) -> Command:
    server = db.query(Server).filter(Server.id == command.server_id).first()
    if not server:
        command.status = "failed"
        command.actual_output = "Server not found"
        command.executed_at = datetime.utcnow()
        return command

    executor = SSHExecutor()
    try:
        executor.connect(**get_server_auth(server))
        result = executor.execute(command.command)
        command.actual_output = result["output"]
        command.status = "success" if result["exit_status"] == 0 else "failed"
    except Exception as exc:
        command.actual_output = str(exc)
        command.status = "failed"
    finally:
        executor.close()

    command.executed_at = datetime.utcnow()
    return command


async def execute_single_command(command: Command, db: Session) -> Command:
    command.status = "executing"
    db.commit()
    db.refresh(command)
    await broadcast_to_session(
        str(command.session_id),
        "command_status_updated",
        {"id": command.id, "status": command.status},
    )

    command = run_command_sync(command, db)
    db.commit()
    db.refresh(command)

    await broadcast_to_session(
        str(command.session_id),
        "command_status_updated",
        {"id": command.id, "status": command.status},
    )
    await broadcast_to_session(
        str(command.session_id),
        "command_output_updated",
        {"id": command.id, "actual_output": command.actual_output},
    )

    if command.status == "failed":
        await broadcast_to_session(
            str(command.session_id),
            "command_failed_ask_user",
            {
                "command_id": command.id,
                "error": command.actual_output or "Unknown error",
            },
        )

    return command


async def execute_group_if_ready(
    group_id: str, session_id: int, db: Session
) -> Command | None:
    group_commands = (
        db.query(Command)
        .filter(Command.session_id == session_id)
        .filter(Command.group_id == group_id)
        .order_by(Command.position_in_group.asc(), Command.id.asc())
        .all()
    )

    if len(group_commands) < 2:
        return None

    if not group_commands:
        return None

    if any(c.status != "approved" for c in group_commands):
        return None

    last_executed = None
    for group_command in group_commands:
        last_executed = await execute_single_command(group_command, db)
    return last_executed
