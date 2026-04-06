from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from command_runtime import execute_group_if_ready, execute_single_command
from database import get_db
from models import Command, Session as SessionModel, SessionAllowedCommand
from routers.permissions import check_command_against_rules
from schemas import CommandCreate, CommandResponse, CommandUpdate
from ws import broadcast_to_session

router = APIRouter(prefix="/api", tags=["commands"])


def _to_response(cmd: Command) -> CommandResponse:
    return CommandResponse(
        id=cmd.id,
        session_id=cmd.session_id,
        server_id=cmd.server_id,
        title=cmd.title,
        description=cmd.description,
        command=cmd.command,
        expected_output=cmd.expected_output,
        rollback_steps=cmd.rollback_steps,
        is_risky=cmd.is_risky,
        group_id=cmd.group_id,
        position_in_group=cmd.position_in_group,
        parent_id=cmd.parent_id,
        node_position_x=cmd.node_position_x,
        node_position_y=cmd.node_position_y,
        status=cmd.status,
        actual_output=cmd.actual_output,
        edited_by_user=cmd.edited_by_user,
        original_command=cmd.original_command,
        created_at=cmd.created_at,
        executed_at=cmd.executed_at,
    )


@router.get("/sessions/{session_id}/commands", response_model=List[CommandResponse])
def list_commands(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    commands = (
        db.query(Command)
        .filter(Command.session_id == session_id)
        .order_by(Command.created_at)
        .all()
    )
    return [_to_response(cmd) for cmd in commands]


@router.post("/commands", response_model=CommandResponse)
async def create_command(cmd: CommandCreate, db: Session = Depends(get_db)):
    status, reason = check_command_against_rules(
        cmd.command,
        cmd.server_id,
        db,
        session_id=cmd.session_id,
    )

    db_cmd = Command(
        session_id=cmd.session_id,
        server_id=cmd.server_id,
        title=cmd.title,
        description=cmd.description,
        command=cmd.command,
        expected_output=cmd.expected_output,
        rollback_steps=cmd.rollback_steps,
        is_risky=cmd.is_risky,
        group_id=cmd.group_id,
        position_in_group=cmd.position_in_group,
        parent_id=cmd.parent_id,
        node_position_x=cmd.node_position_x,
        node_position_y=cmd.node_position_y,
        status=status,
    )
    db.add(db_cmd)
    db.commit()
    db.refresh(db_cmd)
    await broadcast_to_session(
        str(db_cmd.session_id), "command_created", _to_response(db_cmd).model_dump()
    )

    if status == "blocked":
        db_cmd.actual_output = reason
        db.commit()
        db.refresh(db_cmd)
        await broadcast_to_session(
            str(db_cmd.session_id),
            "command_output_updated",
            {"id": db_cmd.id, "actual_output": db_cmd.actual_output},
        )
    elif status == "approved":
        await broadcast_to_session(
            str(db_cmd.session_id),
            "command_status_updated",
            {"id": db_cmd.id, "status": db_cmd.status},
        )
        if db_cmd.group_id:
            await execute_group_if_ready(db_cmd.group_id, db_cmd.session_id, db)
            db.refresh(db_cmd)
        else:
            db_cmd = await execute_single_command(db_cmd, db)

    return _to_response(db_cmd)


@router.post("/commands/{command_id}/approve", response_model=CommandResponse)
async def approve_command(command_id: int, db: Session = Depends(get_db)):
    cmd = db.query(Command).filter(Command.id == command_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    cmd.status = "approved"
    db.commit()
    db.refresh(cmd)
    await broadcast_to_session(
        str(cmd.session_id),
        "command_status_updated",
        {"id": cmd.id, "status": cmd.status},
    )

    if cmd.group_id:
        await execute_group_if_ready(cmd.group_id, cmd.session_id, db)
        db.refresh(cmd)
    else:
        cmd = await execute_single_command(cmd, db)

    return _to_response(cmd)


@router.post("/commands/{command_id}/deny", response_model=CommandResponse)
async def deny_command(command_id: int, db: Session = Depends(get_db)):
    cmd = db.query(Command).filter(Command.id == command_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    cmd.status = "denied"
    db.commit()
    db.refresh(cmd)
    await broadcast_to_session(
        str(cmd.session_id),
        "command_status_updated",
        {"id": cmd.id, "status": cmd.status},
    )
    return _to_response(cmd)


@router.post("/commands/{command_id}/edit", response_model=CommandResponse)
async def edit_command(
    command_id: int, cmd_update: CommandUpdate, db: Session = Depends(get_db)
):
    cmd = db.query(Command).filter(Command.id == command_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")

    update_data = cmd_update.model_dump(exclude_unset=True)
    if "command" in update_data and update_data["command"] != cmd.command:
        cmd.original_command = cmd.command
        cmd.edited_by_user = True

    for field, value in update_data.items():
        setattr(cmd, field, value)

    db.commit()
    db.refresh(cmd)
    await broadcast_to_session(
        str(cmd.session_id),
        "command_status_updated",
        {"id": cmd.id, "status": cmd.status},
    )
    return _to_response(cmd)


@router.post("/commands/{command_id}/reexecute", response_model=CommandResponse)
async def reexecute_command(command_id: int, db: Session = Depends(get_db)):
    cmd = db.query(Command).filter(Command.id == command_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")

    cmd.actual_output = None
    cmd.executed_at = datetime.utcnow()
    cmd.status = "approved"
    db.commit()
    db.refresh(cmd)
    cmd = await execute_single_command(cmd, db)
    return _to_response(cmd)


@router.post("/commands/{command_id}/allow-session")
async def allow_command_session(command_id: int, db: Session = Depends(get_db)):
    cmd = db.query(Command).filter(Command.id == command_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")

    existing = (
        db.query(SessionAllowedCommand)
        .filter(SessionAllowedCommand.session_id == cmd.session_id)
        .filter(SessionAllowedCommand.command_value == cmd.command)
        .first()
    )
    if not existing:
        db.add(
            SessionAllowedCommand(session_id=cmd.session_id, command_value=cmd.command)
        )

    cmd.status = "approved"
    db.commit()
    db.refresh(cmd)
    await broadcast_to_session(
        str(cmd.session_id),
        "command_status_updated",
        {"id": cmd.id, "status": cmd.status},
    )

    if cmd.group_id:
        await execute_group_if_ready(cmd.group_id, cmd.session_id, db)
        db.refresh(cmd)
    else:
        cmd = await execute_single_command(cmd, db)

    return {"message": f"Command pattern '{cmd.command}' allowed for rest of session"}
