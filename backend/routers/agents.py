from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import AgentConfig
from schemas import AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse
from encryption import encrypt_value

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/", response_model=List[AgentConfigResponse])
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentConfig).all()
    return [
        AgentConfigResponse(
            id=a.id,
            agent_name=a.agent_name,
            base_url=a.base_url,
            is_active=a.is_active,
            created_at=a.created_at,
        )
        for a in agents
    ]


@router.post("/", response_model=AgentConfigResponse)
def create_agent(agent: AgentConfigCreate, db: Session = Depends(get_db)):
    db_agent = AgentConfig(
        agent_name=agent.agent_name,
        encrypted_api_key=encrypt_value(agent.api_key),
        base_url=agent.base_url,
        is_active=agent.is_active,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return AgentConfigResponse(
        id=db_agent.id,
        agent_name=db_agent.agent_name,
        base_url=db_agent.base_url,
        is_active=db_agent.is_active,
        created_at=db_agent.created_at,
    )


@router.put("/{agent_id}", response_model=AgentConfigResponse)
def update_agent(
    agent_id: int, agent_update: AgentConfigUpdate, db: Session = Depends(get_db)
):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    update_data = agent_update.model_dump(exclude_unset=True)
    if "api_key" in update_data and update_data["api_key"] is not None:
        agent.encrypted_api_key = encrypt_value(update_data.pop("api_key"))
    for field, value in update_data.items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return AgentConfigResponse(
        id=agent.id,
        agent_name=agent.agent_name,
        base_url=agent.base_url,
        is_active=agent.is_active,
        created_at=agent.created_at,
    )


@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted"}


@router.get("/{agent_name}/models")
def get_agent_models(agent_name: str, db: Session = Depends(get_db)):
    agent = db.query(AgentConfig).filter(AgentConfig.agent_name == agent_name).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    model_map = {
        "claude-code": [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-haiku-4-20250514",
        ],
        "opencode": ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514"],
        "codex": ["o3", "o4-mini", "gpt-4.1"],
    }
    models = model_map.get(agent_name, ["default-model"])
    return {"models": models}
