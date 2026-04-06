from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from database import get_db
from models import Server
from schemas import ServerCreate, ServerUpdate, ServerResponse
from encryption import encrypt_value

router = APIRouter(prefix="/api/servers", tags=["servers"])


@router.get("/", response_model=List[ServerResponse])
def list_servers(db: Session = Depends(get_db)):
    servers = db.query(Server).all()
    result = []
    for s in servers:
        tags = json.loads(s.tags) if s.tags else []
        resp = ServerResponse(
            id=s.id,
            label=s.label,
            hostname=s.hostname,
            port=s.port,
            username=s.username,
            auth_method=s.auth_method,
            password=None,
            ssh_key=None,
            passphrase=None,
            tags=tags,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        result.append(resp)
    return result


@router.post("/", response_model=ServerResponse)
def create_server(server: ServerCreate, db: Session = Depends(get_db)):
    db_server = Server(
        label=server.label,
        hostname=server.hostname,
        port=server.port,
        username=server.username,
        auth_method=server.auth_method,
        encrypted_password=encrypt_value(server.password) if server.password else None,
        encrypted_ssh_key=encrypt_value(server.ssh_key) if server.ssh_key else None,
        encrypted_passphrase=encrypt_value(server.passphrase)
        if server.passphrase
        else None,
        tags=json.dumps(server.tags) if server.tags else None,
    )
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    tags = json.loads(db_server.tags) if db_server.tags else []
    return ServerResponse(
        id=db_server.id,
        label=db_server.label,
        hostname=db_server.hostname,
        port=db_server.port,
        username=db_server.username,
        auth_method=db_server.auth_method,
        password=None,
        ssh_key=None,
        passphrase=None,
        tags=tags,
        created_at=db_server.created_at,
        updated_at=db_server.updated_at,
    )


@router.get("/{server_id}", response_model=ServerResponse)
def get_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    tags = json.loads(server.tags) if server.tags else []
    return ServerResponse(
        id=server.id,
        label=server.label,
        hostname=server.hostname,
        port=server.port,
        username=server.username,
        auth_method=server.auth_method,
        password=None,
        ssh_key=None,
        passphrase=None,
        tags=tags,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int, server_update: ServerUpdate, db: Session = Depends(get_db)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    update_data = server_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("password", "ssh_key", "passphrase"):
            if value is not None:
                setattr(server, f"encrypted_{field}", encrypt_value(value))
        elif field == "tags":
            setattr(server, field, json.dumps(value) if value else None)
        else:
            setattr(server, field, value)

    server.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(server)
    tags = json.loads(server.tags) if server.tags else []
    return ServerResponse(
        id=server.id,
        label=server.label,
        hostname=server.hostname,
        port=server.port,
        username=server.username,
        auth_method=server.auth_method,
        password=None,
        ssh_key=None,
        passphrase=None,
        tags=tags,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.delete("/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    db.delete(server)
    db.commit()
    return {"message": "Server deleted"}


@router.get("/{server_id}/status")
def check_server_status(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    import socket

    try:
        sock = socket.create_connection((server.hostname, server.port), timeout=5)
        sock.close()
        return {"status": "reachable"}
    except Exception:
        return {"status": "unreachable"}
