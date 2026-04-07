from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from loguru import logger

from database import get_db
from models import AgentConfig, ChatMessage, Session as SessionModel
from schemas import ChatMessageCreate, ChatMessageResponse
from ws import broadcast_to_session

router = APIRouter(prefix="/api", tags=["chat"])


def _to_response(message: ChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
    )


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_messages(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [_to_response(m) for m in messages]


def _build_fallback_response(content: str) -> str:
    return (
        "No agent is configured right now. Your message was saved, "
        "but no live agent processed it yet. Add an agent in Settings to enable full ACP chat flow. "
        f"\n\nLast message: {content}"
    )


async def _invoke_agent_runtime(
    request: Request,
    session_id: int,
    server_id: int,
    content: str,
    agent_name: str | None = None,
    model: str | None = None,
) -> str:
    runtime = getattr(request.app.state, "acp_runtime", None)
    if runtime is None:
        return _build_fallback_response(content)

    async def progress(stage: str, details: dict | None):
        payload = details or {}
        if stage == "error":
            logger.error(
                "Agent progress stage={} session_id={} details={}",
                stage,
                session_id,
                payload,
            )
        elif stage in {"tool_call", "completed", "debug"}:
            logger.debug(
                "Agent progress stage={} session_id={} details={}",
                stage,
                session_id,
                payload,
            )
        else:
            logger.info(
                "Agent progress stage={} session_id={} details={}",
                stage,
                session_id,
                payload,
            )
        await broadcast_to_session(
            str(session_id),
            "agent_progress",
            {
                "session_id": session_id,
                "stage": stage,
                "details": details or {},
            },
        )

    return await runtime.generate_agent_response(
        session_id=session_id,
        server_id=server_id,
        content=content,
        agent_name=agent_name,
        model=model,
        progress_cb=progress,
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: int,
    message: ChatMessageCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = ChatMessage(
        session_id=session_id,
        role=message.role,
        content=message.content,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    selected_agent = None
    if message.agent_name:
        selected_agent = (
            db.query(AgentConfig)
            .filter(AgentConfig.agent_name == message.agent_name)
            .order_by(AgentConfig.created_at.desc())
            .first()
        )

    active_agent = (
        selected_agent
        or db.query(AgentConfig)
        .filter(AgentConfig.is_active.is_(True))
        .order_by(AgentConfig.created_at.desc())
        .first()
    )
    if active_agent:
        logger.info(
            "Chat message received session_id={} agent_name={} requested_model={} content_length={}",
            session_id,
            message.agent_name,
            message.model,
            len(message.content or ""),
        )
        runtime_content = await _invoke_agent_runtime(
            request,
            session_id=session_id,
            server_id=session.server_id,
            content=message.content,
            agent_name=message.agent_name,
            model=message.model,
        )
        agent_content = f"[{active_agent.agent_name}] {runtime_content}"
    else:
        agent_content = _build_fallback_response(message.content)

    agent_message = ChatMessage(
        session_id=session_id,
        role="agent",
        content=agent_content,
    )
    db.add(agent_message)
    db.commit()
    db.refresh(agent_message)

    await broadcast_to_session(
        str(session_id),
        "agent_message",
        {
            "id": agent_message.id,
            "session_id": session_id,
            "role": agent_message.role,
            "content": agent_message.content,
            "created_at": agent_message.created_at.isoformat(),
        },
    )

    return _to_response(user_message)
