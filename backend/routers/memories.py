from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ServerMemory, Server
from schemas import ServerMemoryCreate, ServerMemoryUpdate, ServerMemoryResponse

router = APIRouter(prefix="/api", tags=["memories"])


@router.get("/servers/{server_id}/memories", response_model=List[ServerMemoryResponse])
def list_memories(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    memories = (
        db.query(ServerMemory)
        .filter(ServerMemory.server_id == server_id)
        .order_by(ServerMemory.created_at.desc())
        .all()
    )
    return [
        ServerMemoryResponse(
            id=m.id,
            server_id=m.server_id,
            content=m.content,
            source=m.source,
            approved=m.approved,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in memories
    ]


@router.post("/servers/{server_id}/memories", response_model=ServerMemoryResponse)
def create_memory(
    server_id: int, memory: ServerMemoryCreate, db: Session = Depends(get_db)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    db_memory = ServerMemory(
        server_id=server_id,
        content=memory.content,
        source=memory.source,
        approved=memory.source == "manual",
    )
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    return ServerMemoryResponse(
        id=db_memory.id,
        server_id=db_memory.server_id,
        content=db_memory.content,
        source=db_memory.source,
        approved=db_memory.approved,
        created_at=db_memory.created_at,
        updated_at=db_memory.updated_at,
    )


@router.put("/memories/{memory_id}", response_model=ServerMemoryResponse)
def update_memory(
    memory_id: int, memory_update: ServerMemoryUpdate, db: Session = Depends(get_db)
):
    memory = db.query(ServerMemory).filter(ServerMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    if memory_update.content is not None:
        memory.content = memory_update.content
    memory.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(memory)
    return ServerMemoryResponse(
        id=memory.id,
        server_id=memory.server_id,
        content=memory.content,
        source=memory.source,
        approved=memory.approved,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


@router.delete("/memories/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    memory = db.query(ServerMemory).filter(ServerMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(memory)
    db.commit()
    return {"message": "Memory deleted"}


@router.post("/memories/{memory_id}/approve", response_model=ServerMemoryResponse)
def approve_memory(memory_id: int, db: Session = Depends(get_db)):
    memory = db.query(ServerMemory).filter(ServerMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory.approved = True
    memory.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(memory)
    return ServerMemoryResponse(
        id=memory.id,
        server_id=memory.server_id,
        content=memory.content,
        source=memory.source,
        approved=memory.approved,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


@router.post("/memories/{memory_id}/reject")
def reject_memory(memory_id: int, db: Session = Depends(get_db)):
    memory = db.query(ServerMemory).filter(ServerMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(memory)
    db.commit()
    return {"message": "Memory rejected"}


@router.post("/memories/batch-approve")
def batch_approve_memories(
    memory_ids: List[int] = Body(...), db: Session = Depends(get_db)
):
    count = 0
    for mid in memory_ids:
        memory = db.query(ServerMemory).filter(ServerMemory.id == mid).first()
        if memory:
            memory.approved = True
            memory.updated_at = datetime.utcnow()
            count += 1
    db.commit()
    return {"message": f"{count} memories approved"}
