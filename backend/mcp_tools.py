from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any

from sqlalchemy.orm import Session

from command_runtime import execute_group_if_ready, execute_single_command
from models import Command, Server, ServerMemory, Session as SessionModel
from routers.permissions import check_command_against_rules
from ws import broadcast_to_session


MCP_TOOLS = [
    {
        "name": "execute_command",
        "description": "Execute a shell command on the currently selected SSH server. Always provide meaningful title, description, expected output. Mark as risky and provide rollback steps if the command modifies the system.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short human-readable title for the command",
                },
                "description": {
                    "type": "string",
                    "description": "Explain what this command does and why",
                },
                "command": {
                    "type": "string",
                    "description": "The exact shell command to execute",
                },
                "expected_output": {
                    "type": "string",
                    "description": "What output is expected if successful",
                },
                "rollback_steps": {
                    "type": "string",
                    "description": "Steps to undo if something goes wrong (required if risky)",
                },
                "is_risky": {
                    "type": "boolean",
                    "description": "True if command modifies files, services, or system state",
                },
                "group_id": {
                    "type": "string",
                    "description": "If part of a parallel group, provide shared UUID",
                },
                "position_in_group": {
                    "type": "integer",
                    "description": "Order within the group",
                },
                "parent_command_id": {
                    "type": "integer",
                    "description": "ID of the parent command in the tree",
                },
            },
            "required": ["title", "description", "command"],
        },
    },
    {
        "name": "read_server_memory",
        "description": "Read all stored memories and notes for the current server. Call this at the start of every session to get context about the server.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "write_server_memory",
        "description": "Write a memory or finding about the current server to be remembered in future sessions. Use this to store important discoveries, configurations, or warnings.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory content to store",
                },
                "source": {
                    "type": "string",
                    "enum": ["ai"],
                    "description": "Source of the memory",
                },
            },
            "required": ["content", "source"],
        },
    },
    {
        "name": "get_current_server_info",
        "description": "Get information about the currently selected server (label, hostname, port, tags). Does not return credentials.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


@dataclass
class ToolContext:
    session_id: int
    server_id: int


def get_tool_definitions() -> list[dict[str, Any]]:
    return MCP_TOOLS


def _command_to_dict(command: Command) -> dict[str, Any]:
    return {
        "id": command.id,
        "session_id": command.session_id,
        "server_id": command.server_id,
        "parent_id": command.parent_id,
        "group_id": command.group_id,
        "position_in_group": command.position_in_group,
        "title": command.title,
        "description": command.description,
        "command": command.command,
        "expected_output": command.expected_output,
        "rollback_steps": command.rollback_steps,
        "status": command.status,
        "actual_output": command.actual_output,
        "is_risky": command.is_risky,
        "edited_by_user": command.edited_by_user,
        "original_command": command.original_command,
        "node_position_x": command.node_position_x,
        "node_position_y": command.node_position_y,
        "created_at": command.created_at.isoformat() if command.created_at else None,
        "executed_at": command.executed_at.isoformat() if command.executed_at else None,
    }


async def execute_command_tool(
    db: Session,
    context: ToolContext,
    args: dict[str, Any],
) -> dict[str, Any]:
    session = (
        db.query(SessionModel).filter(SessionModel.id == context.session_id).first()
    )
    if not session:
        return {"ok": False, "error": "Session not found"}
    if session.server_id != context.server_id:
        return {
            "ok": False,
            "error": "Session does not belong to specified server",
        }

    if bool(args.get("is_risky", False)) and not args.get("rollback_steps"):
        return {
            "ok": False,
            "error": "rollback_steps is required when is_risky is true",
        }

    status, reason = check_command_against_rules(
        args["command"],
        context.server_id,
        db,
        session_id=context.session_id,
    )

    command = Command(
        session_id=context.session_id,
        server_id=context.server_id,
        parent_id=args.get("parent_command_id"),
        group_id=args.get("group_id"),
        position_in_group=args.get("position_in_group"),
        title=args["title"],
        description=args["description"],
        command=args["command"],
        expected_output=args.get("expected_output"),
        rollback_steps=args.get("rollback_steps"),
        is_risky=bool(args.get("is_risky", False)),
        status=status,
        created_at=datetime.utcnow(),
    )
    db.add(command)
    db.commit()
    db.refresh(command)

    await broadcast_to_session(
        str(context.session_id),
        "command_created",
        _command_to_dict(command),
    )

    if status == "blocked":
        command.actual_output = reason
        db.commit()
        db.refresh(command)
        await broadcast_to_session(
            str(context.session_id),
            "command_output_updated",
            {"id": command.id, "actual_output": command.actual_output},
        )
        return {
            "ok": False,
            "decision": "blocked",
            "reason": reason,
            "command": _command_to_dict(command),
        }

    if status == "approved":
        await broadcast_to_session(
            str(context.session_id),
            "command_status_updated",
            {"id": command.id, "status": command.status},
        )
        if command.group_id:
            await execute_group_if_ready(command.group_id, context.session_id, db)
            db.refresh(command)
        else:
            command = await execute_single_command(command, db)
        return {
            "ok": True,
            "decision": "approved_auto_executed",
            "reason": reason,
            "command": _command_to_dict(command),
        }

    return {
        "ok": True,
        "decision": "pending",
        "reason": reason,
        "command": _command_to_dict(command),
    }


async def read_server_memory_tool(db: Session, context: ToolContext) -> dict[str, Any]:
    memories = (
        db.query(ServerMemory)
        .filter(ServerMemory.server_id == context.server_id)
        .order_by(ServerMemory.created_at.desc())
        .all()
    )
    data = [
        {
            "id": m.id,
            "content": m.content,
            "source": m.source,
            "approved": m.approved,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        }
        for m in memories
    ]
    return {"ok": True, "memories": data}


async def write_server_memory_tool(
    db: Session,
    context: ToolContext,
    content: str,
    source: str = "ai",
    approved: bool = False,
) -> dict[str, Any]:
    memory = ServerMemory(
        server_id=context.server_id,
        content=content,
        source=source,
        approved=approved,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return {
        "ok": True,
        "memory": {
            "id": memory.id,
            "content": memory.content,
            "source": memory.source,
            "approved": memory.approved,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
        },
    }


async def get_current_server_info_tool(
    db: Session, context: ToolContext
) -> dict[str, Any]:
    server = db.query(Server).filter(Server.id == context.server_id).first()
    if not server:
        return {"ok": False, "error": "Server not found"}

    tags = []
    if server.tags:
        try:
            tags = json.loads(server.tags)
        except json.JSONDecodeError:
            tags = []

    return {
        "ok": True,
        "server": {
            "id": server.id,
            "label": server.label,
            "hostname": server.hostname,
            "port": server.port,
            "username": server.username,
            "auth_method": server.auth_method,
            "tags": tags,
        },
    }
