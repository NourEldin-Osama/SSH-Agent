from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from mcp_tools import ToolContext, read_server_memory_tool, write_server_memory_tool
from models import ChatMessage, Command, Session as SessionModel, Server
from schemas import SessionCreate, SessionResponse, SessionUpdate
from ws import broadcast_to_session

router = APIRouter(prefix="/api", tags=["sessions"])


def _to_response(session: SessionModel) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        server_id=session.server_id,
        title=session.title,
        command_count=len(session.commands),
        created_at=session.created_at,
        ended_at=session.ended_at,
    )


@router.get("/servers/{server_id}/sessions", response_model=List[SessionResponse])
def list_sessions(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    sessions = (
        db.query(SessionModel)
        .filter(SessionModel.server_id == server_id)
        .order_by(SessionModel.created_at.desc())
        .all()
    )
    return [_to_response(s) for s in sessions]


@router.post("/servers/{server_id}/sessions", response_model=SessionResponse)
async def create_session(
    server_id: int, session: SessionCreate, db: Session = Depends(get_db)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    db_session = SessionModel(server_id=server_id, title=session.title)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    if not db_session.title:
        generated_title = f"{server.label} session {db_session.id}"
        db_session.title = generated_title
        db.commit()
        db.refresh(db_session)
        await broadcast_to_session(
            str(db_session.id),
            "session_title_generated",
            {"session_id": db_session.id, "title": generated_title},
        )

    memory_result = await read_server_memory_tool(
        db, ToolContext(session_id=db_session.id, server_id=server_id)
    )
    approved_memories = [
        m for m in memory_result.get("memories", []) if m.get("approved")
    ]
    if approved_memories:
        content = "Server memories:\n" + "\n".join(
            f"- {m.get('content', '')}" for m in approved_memories
        )
        system_message = ChatMessage(
            session_id=db_session.id, role="system", content=content
        )
        db.add(system_message)
        db.commit()
        db.refresh(system_message)
        await broadcast_to_session(
            str(db_session.id),
            "agent_message",
            {
                "id": system_message.id,
                "session_id": db_session.id,
                "role": "system",
                "content": system_message.content,
                "created_at": system_message.created_at.isoformat(),
            },
        )

    return _to_response(db_session)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_response(session)


@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int, session_update: SessionUpdate, db: Session = Depends(get_db)
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_update.title is not None:
        session.title = session_update.title
    db.commit()
    db.refresh(session)
    return _to_response(session)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    command_rows = (
        db.query(Command)
        .filter(Command.session_id == session_id)
        .order_by(Command.created_at.asc())
        .all()
    )
    chat_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    summary_parts: list[str] = []
    if command_rows:
        successes = [c for c in command_rows if c.status == "success"]
        failures = [c for c in command_rows if c.status == "failed"]
        summary_parts.append(
            f"Commands: {len(command_rows)} total, {len(successes)} success, {len(failures)} failed"
        )

    if chat_rows:
        last_user = next((m for m in reversed(chat_rows) if m.role == "user"), None)
        summary_parts.append(f"Chat messages: {len(chat_rows)}")
        if last_user:
            summary_parts.append(f"Last user goal: {last_user.content[:200]}")

    session_summary = "\n".join(summary_parts) if summary_parts else "No activity"
    ai_candidates = [
        f"Remember summary for server {session.server_id}: {session_summary}",
        "Remember: Validate risky commands with rollback steps before execution.",
    ]

    created = []
    for content in ai_candidates:
        result = await write_server_memory_tool(
            db,
            ToolContext(session_id=session_id, server_id=session.server_id),
            content=content,
            source="ai",
            approved=False,
        )
        if result.get("ok"):
            created.append(result["memory"])

    if created:
        await broadcast_to_session(
            str(session.id),
            "memory_approval_required",
            {"memories": created},
        )

    return _to_response(session)
